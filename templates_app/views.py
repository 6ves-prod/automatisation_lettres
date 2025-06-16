# templates_app/views.py - Fichier complet avec exports fonctionnels
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.http import HttpResponse, JsonResponse, Http404, FileResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.urls import reverse, NoReverseMatch
from django.template.loader import render_to_string
from .models import Template, Document, TemplateField, DocumentFieldValue, TemplateCategory
from .forms import TemplateForm, DocumentForm, TemplateFieldForm, TemplateCategoryForm
import re
import logging
import io
import os
from datetime import timedelta
from .forms import CustomUserCreationForm, CustomAuthenticationForm

# Imports pour les exports
# Imports pour PDF
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib import colors
    from reportlab.pdfgen import canvas

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# Imports pour DOCX
try:
    from docx import Document as DocxDocument
    from docx.shared import Inches, Pt
    from docx.enum.text import WD_PARAGRAPH_ALIGNMENT

    PYTHON_DOCX_AVAILABLE = True
except ImportError:
    PYTHON_DOCX_AVAILABLE = False

# Alternative avec WeasyPrint
try:
    import weasyprint

    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

# Configuration du logging pour debug
logger = logging.getLogger(__name__)


# ===============================
# VUE D'ACCUEIL
# ===============================

def home_view(request):
    """Page d'accueil avec statistiques et gestion du tutoriel"""
    context = {
        'total_templates': Template.objects.filter(is_public=True).count(),
        'total_users': Template.objects.values('created_by').distinct().count(),
        'total_documents': Document.objects.count(),
    }

    if request.user.is_authenticated:
        # Vérifier si c'est un nouvel utilisateur (inscrit dans les 5 dernières minutes)
        five_minutes_ago = timezone.now() - timedelta(minutes=5)
        is_new_user = request.user.date_joined > five_minutes_ago

        context.update({
            'user_templates': Template.objects.filter(created_by=request.user).count(),
            'user_documents': Document.objects.filter(created_by=request.user).count(),
            'recent_templates': Template.objects.filter(created_by=request.user).order_by('-updated_at')[:3],
            'recent_documents': Document.objects.filter(created_by=request.user).order_by('-updated_at')[:3],
            'is_new_user': is_new_user,
        })

    return render(request, 'home.html', context)


# ===============================
# VUES D'AUTHENTIFICATION
# ===============================

def signup_view(request):
    """Vue d'inscription avec formulaire personnalisé"""
    logger.info(f"Signup view called with method: {request.method}")

    # Rediriger si déjà connecté
    if request.user.is_authenticated:
        messages.info(request, 'Vous êtes déjà connecté.')
        return redirect('home')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        logger.info(f"Form data received - username: {request.POST.get('username', 'N/A')}")

        if form.is_valid():
            try:
                # Créer l'utilisateur avec email
                user = form.save()
                logger.info(f"User created successfully: {user.username} - {user.email}")

                # Connecter automatiquement l'utilisateur
                login(request, user)
                logger.info(f"User logged in successfully: {user.username}")

                messages.success(
                    request,
                    f'Bienvenue {user.username} ! Votre compte a été créé avec succès.'
                )

                # Redirection sécurisée avec tutoriel pour nouveaux utilisateurs
                try:
                    return redirect('home')  # Rediriger vers l'accueil avec tutoriel auto
                except NoReverseMatch:
                    logger.warning("home URL not found, redirecting to templates")
                    return redirect('templates_app:template_list')

            except Exception as e:
                logger.error(f"Error creating user: {str(e)}")
                messages.error(request, f'Erreur lors de la création du compte : {str(e)}')

        else:
            logger.warning(f"Form validation failed: {form.errors}")
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')

    else:
        form = CustomUserCreationForm()

    context = {
        'form': form,
        'title': 'Créer un compte - DocBuilder'
    }

    return render(request, 'registration/signup.html', context)


def login_view(request):
    """Vue de connexion avec formulaire personnalisé"""
    logger.info(f"Login view called with method: {request.method}")

    # Rediriger si déjà connecté
    if request.user.is_authenticated:
        messages.info(request, 'Vous êtes déjà connecté.')
        return redirect('templates_app:template_list')

    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        logger.info(f"Login attempt for username: {request.POST.get('username', 'N/A')}")

        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            # Authentifier l'utilisateur
            user = authenticate(username=username, password=password)

            if user is not None:
                login(request, user)
                logger.info(f"User logged in successfully: {user.username}")

                messages.success(request, f'Bienvenue {user.username} !')

                # Redirection vers la page demandée ou accueil avec tutoriel
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)

                # Pour les connexions, rediriger vers les templates directement
                try:
                    return redirect('templates_app:template_list')
                except NoReverseMatch:
                    return redirect('home')
            else:
                logger.warning(f"Authentication failed for username: {username}")
                messages.error(request, 'Nom d\'utilisateur ou mot de passe incorrect.')
        else:
            logger.warning(f"Login form validation failed: {form.errors}")
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')

    else:
        form = CustomAuthenticationForm()

    context = {
        'form': form,
        'title': 'Connexion - DocBuilder'
    }

    return render(request, 'registration/login.html', context)


# ===============================
# VUES DES TEMPLATES
# ===============================

@login_required
def template_list(request):
    """Liste des templates avec recherche et filtres"""
    templates = Template.objects.filter(
        Q(created_by=request.user) | Q(is_public=True)
    ).select_related('created_by', 'category').annotate(
        document_count=Count('documents')
    ).order_by('-created_at')

    # Filtres
    search = request.GET.get('search', '')
    category_id = request.GET.get('category', '')
    visibility = request.GET.get('visibility', '')

    if search:
        templates = templates.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search)
        )

    if category_id:
        templates = templates.filter(category_id=category_id)

    if visibility == 'my':
        templates = templates.filter(created_by=request.user)
    elif visibility == 'public':
        templates = templates.filter(is_public=True)

    # Pagination
    paginator = Paginator(templates, 12)
    page_number = request.GET.get('page')
    templates = paginator.get_page(page_number)

    # Catégories pour le filtre
    categories = TemplateCategory.objects.all().order_by('name')

    context = {
        'templates': templates,
        'categories': categories,
        'search': search,
        'selected_category': category_id,
        'selected_visibility': visibility,
    }
    return render(request, 'templates_app/template_list.html', context)


def template_detail(request, template_id):
    """Détail d'un template"""
    template = get_object_or_404(Template, id=template_id)

    # Vérifier les permissions
    if not template.is_public and (not request.user.is_authenticated or template.created_by != request.user):
        messages.error(request, "Vous n'avez pas accès à ce template.")
        return redirect('templates_app:template_list')

    # Récupérer les champs et documents associés
    fields = template.fields.all().order_by('order', 'id')

    if request.user.is_authenticated:
        recent_documents = template.documents.filter(created_by=request.user).order_by('-updated_at')[:5]
    else:
        recent_documents = []

    # Calculer les statistiques
    all_documents = template.documents.all()
    completed_documents = all_documents.filter(is_completed=True)
    draft_documents = all_documents.filter(is_completed=False)

    context = {
        'template': template,
        'fields': fields,
        'recent_documents': recent_documents,
        'total_documents': all_documents.count(),
        'completed_documents_count': completed_documents.count(),
        'draft_documents_count': draft_documents.count(),
        'template_content_length': len(template.content) if template.content else 0,
    }
    return render(request, 'templates_app/template_detail.html', context)


@login_required
def template_create(request):
    """Créer un nouveau template"""
    if request.method == 'POST':
        form = TemplateForm(request.POST)
        if form.is_valid():
            template = form.save(commit=False)
            template.created_by = request.user
            template.save()

            # Extraire et créer automatiquement les champs du contenu
            create_fields_from_content(template)

            messages.success(request, f'Template "{template.title}" créé avec succès !')
            return redirect('templates_app:template_detail', template_id=template.id)
        else:
            messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
    else:
        form = TemplateForm()

    context = {
        'form': form,
        'template': None,
    }
    return render(request, 'templates_app/template_create.html', context)


@login_required
def template_edit(request, template_id):
    """Modifier un template existant"""
    template = get_object_or_404(Template, id=template_id, created_by=request.user)

    if request.method == 'POST':
        form = TemplateForm(request.POST, instance=template)
        if form.is_valid():
            template = form.save()

            # Mettre à jour les champs si le contenu a changé
            create_fields_from_content(template)

            messages.success(request, f'Template "{template.title}" modifié avec succès !')
            return redirect('templates_app:template_detail', template_id=template.id)
        else:
            messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
    else:
        form = TemplateForm(instance=template)

    context = {
        'form': form,
        'template': template,
    }
    return render(request, 'templates_app/template_create.html', context)


def template_preview(request, template_id):
    """Aperçu du template avec des données d'exemple"""
    template = get_object_or_404(Template, id=template_id)

    # Vérifier les permissions
    if not template.is_public and (not request.user.is_authenticated or template.created_by != request.user):
        messages.error(request, "Vous n'avez pas accès à ce template.")
        return redirect('templates_app:template_list')

    # Récupérer les champs du template
    fields = template.fields.all()

    # Créer des données d'exemple pour l'aperçu
    preview_data = {}
    for field in fields:
        preview_data[field.field_name] = generate_sample_data(field.field_name)

    # Remplacer les placeholders dans le contenu
    rendered_content = template.content
    for field_name, field_value in preview_data.items():
        placeholder = f'{{{{{field_name}}}}}'
        rendered_content = rendered_content.replace(placeholder, str(field_value))

    context = {
        'template': template,
        'fields': fields,
        'rendered_content': rendered_content,
        'preview_data': preview_data,
        'is_preview': True,
    }
    return render(request, 'templates_app/template_preview.html', context)


# ===============================
# VUES DES DOCUMENTS
# ===============================

@login_required
def document_create(request, template_id):
    """Créer un nouveau document à partir d'un template"""
    template = get_object_or_404(Template, id=template_id)

    # Vérifier les permissions
    if not template.is_public and template.created_by != request.user:
        messages.error(request, "Vous n'avez pas accès à ce template.")
        return redirect('templates_app:template_list')

    # Récupérer les champs du template
    fields = template.fields.all().order_by('order', 'id')

    if request.method == 'POST':
        form = DocumentForm(request.POST)

        if form.is_valid():
            try:
                # Créer le document
                document = Document.objects.create(
                    template=template,
                    title=form.cleaned_data['title'],
                    created_by=request.user,
                    is_completed=request.POST.get('mark_completed') == 'on'
                )

                # Sauvegarder les valeurs des champs
                for field in fields:
                    field_name = f'field_{field.id}'
                    field_value = request.POST.get(field_name, '')

                    if field_value or field.is_required:
                        DocumentFieldValue.objects.create(
                            document=document,
                            template_field=field,
                            value=field_value
                        )

                messages.success(request, f'Document "{document.title}" créé avec succès !')
                return redirect('templates_app:document_detail', document_id=document.id)

            except Exception as e:
                messages.error(request, f'Erreur lors de la création du document : {str(e)}')
        else:
            messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
    else:
        # Formulaire vide pour création
        initial_data = {
            'title': f'Document basé sur {template.title} - {timezone.now().strftime("%d/%m/%Y %H:%M")}'
        }
        form = DocumentForm(initial=initial_data)

    context = {
        'form': form,
        'template': template,
        'fields': fields,
        'document': None,
    }
    return render(request, 'templates_app/document_form.html', context)


@login_required
def document_edit(request, document_id):
    """Modifier un document existant"""
    document = get_object_or_404(Document, id=document_id, created_by=request.user)
    template = document.template
    fields = template.fields.all().order_by('order', 'id')

    # Récupérer les valeurs actuelles
    current_values = {}
    for field_value in document.field_values.all():
        current_values[f'field_{field_value.template_field.id}'] = field_value.value

    if request.method == 'POST':
        form = DocumentForm(request.POST, instance=document)

        if form.is_valid():
            try:
                # Mettre à jour le document
                document = form.save(commit=False)
                document.is_completed = request.POST.get('mark_completed') == 'on'
                document.save()

                # Mettre à jour les valeurs des champs
                document.field_values.all().delete()

                # Créer les nouvelles valeurs
                for field in fields:
                    field_name = f'field_{field.id}'
                    field_value = request.POST.get(field_name, '')

                    if field_value or field.is_required:
                        DocumentFieldValue.objects.create(
                            document=document,
                            template_field=field,
                            value=field_value
                        )

                messages.success(request, f'Document "{document.title}" modifié avec succès !')
                return redirect('templates_app:document_detail', document_id=document.id)

            except Exception as e:
                messages.error(request, f'Erreur lors de la modification : {str(e)}')
        else:
            messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
    else:
        form = DocumentForm(instance=document)

    context = {
        'form': form,
        'template': template,
        'fields': fields,
        'document': document,
        'current_values': current_values,
    }
    return render(request, 'templates_app/document_form.html', context)


@login_required
def document_detail(request, document_id):
    """Détail d'un document avec le contenu rendu"""
    document = get_object_or_404(Document, id=document_id, created_by=request.user)
    template = document.template

    # Récupérer les valeurs des champs
    field_values = {}
    rendered_values = {}

    for field_value in document.field_values.all():
        field_name = field_value.template_field.field_name
        field_values[field_name] = field_value.value
        rendered_values[field_value.template_field.field_label] = field_value.value

    # Remplacer les placeholders dans le contenu du template
    rendered_content = template.content
    for field_name, field_value in field_values.items():
        placeholder = f'{{{{{field_name}}}}}'
        rendered_content = rendered_content.replace(placeholder, str(field_value))

    context = {
        'document': document,
        'template': template,
        'rendered_content': rendered_content,
        'field_values': rendered_values,
    }
    return render(request, 'templates_app/document_detail.html', context)


@login_required
def document_list(request):
    """Liste des documents de l'utilisateur avec filtres et statistiques"""
    documents = Document.objects.filter(created_by=request.user).select_related('template').order_by('-updated_at')

    # Filtres
    search = request.GET.get('search', '')
    selected_template = request.GET.get('template', '')
    selected_status = request.GET.get('status', '')

    if search:
        documents = documents.filter(
            Q(title__icontains=search) |
            Q(template__title__icontains=search)
        )

    if selected_template:
        documents = documents.filter(template_id=selected_template)

    if selected_status == 'completed':
        documents = documents.filter(is_completed=True)
    elif selected_status == 'draft':
        documents = documents.filter(is_completed=False)

    # Calculs des statistiques
    all_documents = Document.objects.filter(created_by=request.user)
    completed_count = all_documents.filter(is_completed=True).count()
    draft_count = all_documents.filter(is_completed=False).count()

    # Documents créés cette semaine
    week_ago = timezone.now() - timedelta(days=7)
    recent_count = all_documents.filter(created_at__gte=week_ago).count()

    # Pagination
    paginator = Paginator(documents, 12)
    page_number = request.GET.get('page')
    documents = paginator.get_page(page_number)

    # Templates pour le filtre
    templates = Template.objects.filter(
        Q(created_by=request.user) | Q(is_public=True)
    ).order_by('title')

    context = {
        'documents': documents,
        'templates': templates,
        'search': search,
        'selected_template': selected_template,
        'selected_status': selected_status,
        'completed_count': completed_count,
        'draft_count': draft_count,
        'recent_count': recent_count,
    }
    return render(request, 'templates_app/document_list.html', context)


@login_required
def document_delete(request, document_id):
    """Supprimer un document avec confirmation"""
    document = get_object_or_404(Document, id=document_id, created_by=request.user)

    if request.method == 'POST':
        document_title = document.title
        document.delete()
        messages.success(request, f'Le document "{document_title}" a été supprimé avec succès.')
        return redirect('templates_app:document_list')

    context = {
        'document': document,
    }
    return render(request, 'templates_app/document_confirm_delete.html', context)


# ===============================
# VUES D'EXPORT - FONCTIONNELLES
# ===============================

@login_required
def document_export_pdf(request, document_id):
    """Export PDF avec ReportLab ou WeasyPrint"""
    document = get_object_or_404(Document, id=document_id, created_by=request.user)

    if not REPORTLAB_AVAILABLE and not WEASYPRINT_AVAILABLE:
        messages.error(request,
                       "Les bibliothèques PDF ne sont pas installées. Installez reportlab ou weasyprint avec: pip install reportlab")
        return redirect('templates_app:document_detail', document_id=document_id)

    try:
        # Récupérer les données du document
        template = document.template
        field_values = {}

        for field_value in document.field_values.all():
            field_name = field_value.template_field.field_name
            field_values[field_name] = field_value.value

        # Remplacer les placeholders
        rendered_content = template.content
        for field_name, field_value in field_values.items():
            placeholder = f'{{{{{field_name}}}}}'
            rendered_content = rendered_content.replace(placeholder, str(field_value))

        if WEASYPRINT_AVAILABLE:
            return export_pdf_weasyprint(document, rendered_content)
        else:
            return export_pdf_reportlab(document, rendered_content)

    except Exception as e:
        messages.error(request, f'Erreur lors de l\'export PDF : {str(e)}')
        return redirect('templates_app:document_detail', document_id=document_id)


@login_required
def document_export_docx(request, document_id):
    """Export DOCX avec python-docx"""
    document = get_object_or_404(Document, id=document_id, created_by=request.user)

    if not PYTHON_DOCX_AVAILABLE:
        messages.error(request,
                       "La bibliothèque python-docx n'est pas installée. Installez avec: pip install python-docx")
        return redirect('templates_app:document_detail', document_id=document_id)

    try:
        # Récupérer les données du document
        template = document.template
        field_values = {}

        for field_value in document.field_values.all():
            field_name = field_value.template_field.field_name
            field_values[field_name] = field_value.value

        # Remplacer les placeholders
        rendered_content = template.content
        for field_name, field_value in field_values.items():
            placeholder = f'{{{{{field_name}}}}}'
            rendered_content = rendered_content.replace(placeholder, str(field_value))

        # Créer le document Word
        doc = DocxDocument()

        # Configurer les styles
        styles = doc.styles

        # Style normal
        normal_style = styles['Normal']
        normal_style.font.size = Pt(12)
        normal_style.font.name = 'Times New Roman'
        normal_style.paragraph_format.line_spacing = 1.5

        # Ajouter le titre
        title_para = doc.add_heading(document.title, 0)
        title_para.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

        # Ajouter la date
        date_para = doc.add_paragraph(f"Généré le {timezone.now().strftime('%d/%m/%Y à %H:%M')}")
        date_para.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

        # Ajouter une ligne vide
        doc.add_paragraph("")

        # Ajouter le contenu principal
        lines = rendered_content.split('\n')
        for line in lines:
            if line.strip():
                doc.add_paragraph(line.strip())
            else:
                doc.add_paragraph("")

        # Ajouter le footer
        doc.add_paragraph("")
        footer_para = doc.add_paragraph(f"Document généré par DocBuilder - {document.template.title}")
        footer_para.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

        # Sauvegarder dans un buffer
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)

        # Créer la réponse
        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        filename = f"{document.title.replace(' ', '_')}.docx"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response

    except Exception as e:
        messages.error(request, f'Erreur lors de l\'export DOCX : {str(e)}')
        return redirect('templates_app:document_detail', document_id=document_id)


@login_required
def document_export_html(request, document_id):
    """Export HTML amélioré"""
    document = get_object_or_404(Document, id=document_id, created_by=request.user)

    try:
        # Récupérer les données du document
        template = document.template
        field_values = {}

        for field_value in document.field_values.all():
            field_name = field_value.template_field.field_name
            field_values[field_name] = field_value.value

        # Remplacer les placeholders
        rendered_content = template.content
        for field_name, field_value in field_values.items():
            placeholder = f'{{{{{field_name}}}}}'
            rendered_content = rendered_content.replace(placeholder, str(field_value))

        # Créer le HTML complet
        html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{document.title}</title>
    <style>
        body {{
            font-family: 'Times New Roman', serif;
            margin: 2cm;
            line-height: 1.6;
            color: #333;
            background: white;
        }}
        .document-header {{
            text-align: center;
            margin-bottom: 2em;
            padding-bottom: 1em;
            border-bottom: 2px solid #3498db;
        }}
        .document-header h1 {{
            color: #2c3e50;
            margin-bottom: 0.5em;
            font-size: 2em;
        }}
        .document-content {{
            margin: 2em 0;
            text-align: justify;
        }}
        .document-footer {{
            margin-top: 3em;
            padding-top: 1em;
            border-top: 1px solid #bdc3c7;
            font-size: 0.9em;
            color: #7f8c8d;
            text-align: center;
        }}
        h1, h2, h3 {{ color: #2c3e50; }}
        p {{ margin-bottom: 1em; }}

        @media print {{
            body {{ margin: 1cm; }}
            .no-print {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="document-header">
        <h1>{document.title}</h1>
        <p><em>Généré le {timezone.now().strftime('%d/%m/%Y à %H:%M')}</em></p>
    </div>

    <div class="document-content">
        {rendered_content.replace(chr(10), '<br>')}
    </div>

    <div class="document-footer">
        <p><strong>Document généré par DocBuilder</strong></p>
        <p>Template source : {document.template.title}</p>
        <p class="no-print">
            <button onclick="window.print()" style="padding: 10px 20px; background: #3498db; color: white; border: none; border-radius: 5px; cursor: pointer;">
                Imprimer ce document
            </button>
        </p>
    </div>
</body>
</html>"""

        # Créer la réponse
        response = HttpResponse(html_content, content_type='text/html')
        filename = f"{document.title.replace(' ', '_')}.html"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response

    except Exception as e:
        messages.error(request, f'Erreur lors de l\'export HTML : {str(e)}')
        return redirect('templates_app:document_detail', document_id=document_id)


# ===============================
# FONCTIONS UTILITAIRES POUR EXPORTS
# ===============================

def export_pdf_weasyprint(document, content):
    """Export PDF avec WeasyPrint (recommandé pour le CSS)"""
    # Créer le HTML avec styles
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{
                margin: 2cm;
                size: A4;
            }}
            body {{
                font-family: 'Times New Roman', serif;
                font-size: 12pt;
                line-height: 1.6;
                color: #333;
            }}
            h1, h2, h3 {{
                color: #2c3e50;
                margin-top: 1em;
                margin-bottom: 0.5em;
            }}
            h1 {{ font-size: 18pt; }}
            h2 {{ font-size: 16pt; }}
            h3 {{ font-size: 14pt; }}
            p {{ margin-bottom: 1em; }}
            .header {{
                text-align: center;
                margin-bottom: 2em;
                padding-bottom: 1em;
                border-bottom: 2px solid #3498db;
            }}
            .footer {{
                margin-top: 3em;
                padding-top: 1em;
                border-top: 1px solid #bdc3c7;
                font-size: 10pt;
                color: #7f8c8d;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>{document.title}</h1>
            <p>Généré le {timezone.now().strftime('%d/%m/%Y à %H:%M')}</p>
        </div>

        <div class="content">
            {content.replace(chr(10), '<br>')}
        </div>

        <div class="footer">
            <p>Document généré par DocBuilder - {document.template.title}</p>
        </div>
    </body>
    </html>
    """

    # Générer le PDF
    pdf_file = weasyprint.HTML(string=html_content).write_pdf()

    # Créer la réponse HTTP
    response = HttpResponse(pdf_file, content_type='application/pdf')
    filename = f"{document.title.replace(' ', '_')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response


def export_pdf_reportlab(document, content):
    """Export PDF avec ReportLab (plus basique)"""
    buffer = io.BytesIO()

    # Créer le document PDF
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1 * inch)

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=18,
        spaceAfter=30,
        alignment=1  # Centré
    )

    normal_style = styles['Normal']
    normal_style.fontSize = 12
    normal_style.leading = 18

    # Contenu
    story = []

    # Titre
    title = Paragraph(document.title, title_style)
    story.append(title)

    # Date
    date_para = Paragraph(f"Généré le {timezone.now().strftime('%d/%m/%Y à %H:%M')}", styles['Normal'])
    story.append(date_para)
    story.append(Spacer(1, 20))

    # Contenu principal (diviser par lignes)
    lines = content.split('\n')
    for line in lines:
        if line.strip():
            para = Paragraph(line.strip(), normal_style)
            story.append(para)
        else:
            story.append(Spacer(1, 12))

    # Footer
    story.append(Spacer(1, 30))
    footer = Paragraph(f"Document généré par DocBuilder - {document.template.title}", styles['Normal'])
    story.append(footer)

    # Construire le PDF
    doc.build(story)

    # Réponse
    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(pdf, content_type='application/pdf')
    filename = f"{document.title.replace(' ', '_')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response


# ===============================
# VUES PLACEHOLDER (fonctionnalités futures)
# ===============================

@login_required
def template_duplicate(request, template_id):
    """Placeholder pour dupliquer un template"""
    messages.info(request, "Fonction de duplication en cours de développement.")
    return redirect('templates_app:template_detail', template_id=template_id)


@login_required
def template_delete(request, template_id):
    """Placeholder pour supprimer un template"""
    messages.info(request, "Fonction de suppression en cours de développement.")
    return redirect('templates_app:template_detail', template_id=template_id)


@login_required
def template_edit_fields(request, template_id):
    """Placeholder pour éditer les champs"""
    messages.info(request, "Fonction d'édition des champs en cours de développement.")
    return redirect('templates_app:template_detail', template_id=template_id)


@login_required
def template_add_field(request, template_id):
    """Placeholder pour ajouter un champ"""
    messages.info(request, "Fonction d'ajout de champ en cours de développement.")
    return redirect('templates_app:template_detail', template_id=template_id)


@login_required
def template_delete_field(request, template_id, field_id):
    """Placeholder pour supprimer un champ"""
    messages.info(request, "Fonction de suppression de champ en cours de développement.")
    return redirect('templates_app:template_detail', template_id=template_id)


@login_required
def document_duplicate(request, document_id):
    """Placeholder pour dupliquer un document"""
    messages.info(request, "Fonction de duplication en cours de développement.")
    return redirect('templates_app:document_detail', document_id=document_id)


@login_required
def template_export(request, template_id):
    """Placeholder pour export template"""
    messages.info(request, "Export de template en cours de développement.")
    return redirect('templates_app:template_detail', template_id=template_id)


@login_required
def category_list(request):
    """Placeholder pour liste des catégories"""
    messages.info(request, "Gestion des catégories en cours de développement.")
    return redirect('templates_app:template_list')


@login_required
def category_create(request):
    """Placeholder pour créer une catégorie"""
    messages.info(request, "Création de catégorie en cours de développement.")
    return redirect('templates_app:template_list')


@login_required
def category_edit(request, category_id):
    """Placeholder pour modifier une catégorie"""
    messages.info(request, "Modification de catégorie en cours de développement.")
    return redirect('templates_app:template_list')


@login_required
def category_delete(request, category_id):
    """Placeholder pour supprimer une catégorie"""
    messages.info(request, "Suppression de catégorie en cours de développement.")
    return redirect('templates_app:template_list')


# ===============================
# FONCTIONS UTILITAIRES
# ===============================

def extract_fields_from_content(content):
    """Extraire les champs dynamiques du contenu du template"""
    if not content:
        return []

    # Expression régulière pour trouver les placeholders {{field_name}}
    pattern = r'\{\{([a-zA-Z_][a-zA-Z0-9_]*)\}\}'
    matches = re.findall(pattern, content)

    # Supprimer les doublons et trier
    unique_fields = list(set(matches))
    unique_fields.sort()

    return unique_fields


def generate_sample_data(field_name):
    """Générer des données d'exemple pour un champ"""
    samples = {
        'nom_client': 'Jean Dupont',
        'nom_entreprise': 'ACME Corporation',
        'adresse_entreprise': '123 Rue de la Paix, 75001 Paris',
        'email': 'contact@example.com',
        'telephone': '01 23 45 67 89',
        'date_aujourd_hui': timezone.now().strftime('%d/%m/%Y'),
        'date_debut': '01/01/2024',
        'salaire': '3 500 €',
        'poste': 'Développeur Full-Stack',
        'montant_total': '1 250,00 €',
        'numero_reference': 'REF-2024-001',
        'ville': 'Paris',
        'date': timezone.now().strftime('%d/%m/%Y'),
    }

    # Essayer de deviner le type de données basé sur le nom du champ
    field_lower = field_name.lower()

    if 'email' in field_lower:
        return 'contact@example.com'
    elif 'date' in field_lower:
        return timezone.now().strftime('%d/%m/%Y')
    elif 'nom' in field_lower and 'client' in field_lower:
        return 'Jean Dupont'
    elif 'nom' in field_lower and 'entreprise' in field_lower:
        return 'ACME Corporation'
    elif 'adresse' in field_lower:
        return '123 Rue de la Paix, 75001 Paris'
    elif 'telephone' in field_lower or 'tel' in field_lower:
        return '01 23 45 67 89'
    elif 'montant' in field_lower or 'prix' in field_lower:
        return '1 250,00 €'
    elif 'numero' in field_lower or 'ref' in field_lower:
        return 'REF-2024-001'
    elif 'ville' in field_lower:
        return 'Paris'
    else:
        return samples.get(field_name, f'[Exemple pour {field_name.replace("_", " ")}]')


def create_fields_from_content(template):
    """Créer automatiquement les champs à partir du contenu du template"""
    if not template.content:
        return

    # Extraire les champs du contenu
    field_names = extract_fields_from_content(template.content)

    if not field_names:
        return

    # Créer les champs qui n'existent pas encore
    existing_fields = set(template.fields.values_list('field_name', flat=True))

    for i, field_name in enumerate(field_names):
        if field_name not in existing_fields:
            # Créer un libellé lisible à partir du nom du champ
            field_label = field_name.replace('_', ' ').title()

            # Déterminer le type de champ basé sur le nom
            field_type = 'text'  # Par défaut
            if 'email' in field_name.lower():
                field_type = 'email'
            elif 'date' in field_name.lower():
                field_type = 'date'
            elif 'description' in field_name.lower() or 'commentaire' in field_name.lower():
                field_type = 'textarea'
            elif 'montant' in field_name.lower() or 'prix' in field_name.lower() or 'salaire' in field_name.lower():
                field_type = 'number'

            # Déterminer si le champ est requis
            is_required = field_name.lower() in [
                'nom_client', 'nom_entreprise', 'email', 'date_debut', 'montant_total'
            ]

            TemplateField.objects.create(
                template=template,
                field_name=field_name,
                field_label=field_label,
                field_type=field_type,
                is_required=is_required,
                order=i * 10,
                placeholder_text=f'Entrez {field_label.lower()}'
            )