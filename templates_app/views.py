# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
import json
import re

from .models import Template, TemplateField, Document, DocumentFieldValue, TemplateCategory
from .forms import TemplateForm, DocumentForm

User = get_user_model()


# ===============================
# VUES POUR LES TEMPLATES
# ===============================

def template_list(request):
    """Liste des templates avec recherche et filtres"""
    # Récupérer tous les templates accessibles
    if request.user.is_authenticated:
        templates = Template.objects.filter(
            Q(created_by=request.user) | Q(is_public=True)
        ).select_related('created_by', 'category').prefetch_related('fields', 'documents')
    else:
        templates = Template.objects.filter(is_public=True).select_related('created_by', 'category')

    # Filtres
    search = request.GET.get('search', '')
    category_id = request.GET.get('category', '')
    visibility = request.GET.get('visibility', '')

    if search:
        templates = templates.filter(
            Q(title__icontains=search) | Q(description__icontains=search)
        )

    if category_id:
        templates = templates.filter(category_id=category_id)

    if visibility and request.user.is_authenticated:
        if visibility == 'my':
            templates = templates.filter(created_by=request.user)
        elif visibility == 'public':
            templates = templates.filter(is_public=True)

    # Tri par date de création (plus récents en premier)
    templates = templates.order_by('-created_at')

    # Pagination
    paginator = Paginator(templates, 12)
    page = request.GET.get('page')
    templates_page = paginator.get_page(page)

    # Récupérer les catégories pour le filtre
    categories = TemplateCategory.objects.all().order_by('name')

    context = {
        'templates': templates_page,
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
    if not template.is_public and template.created_by != request.user:
        messages.error(request, "Vous n'avez pas accès à ce template.")
        return redirect('templates_app:template_list')

    # Récupérer les champs et documents associés
    fields = template.fields.all().order_by('order', 'id')

    if request.user.is_authenticated:
        recent_documents = template.documents.filter(created_by=request.user).order_by('-updated_at')[:5]
    else:
        recent_documents = []

    context = {
        'template': template,
        'fields': fields,
        'recent_documents': recent_documents,
    }
    return render(request, 'templates_app/template_detail.html', context)


@login_required
def template_create(request):
    """Création d'un nouveau template"""
    if request.method == 'POST':
        form = TemplateForm(request.POST)
        if form.is_valid():
            template = form.save(commit=False)
            template.created_by = request.user
            template.save()

            # Détecter et créer automatiquement les champs
            detect_and_create_fields(template)

            messages.success(request, f'Template "{template.title}" créé avec succès!')
            return redirect('templates_app:template_detail', template_id=template.id)
        else:
            messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
    else:
        form = TemplateForm()

    # Récupérer les catégories
    categories = TemplateCategory.objects.all().order_by('name')

    context = {
        'form': form,
        'categories': categories,
        'title': 'Créer un template'
    }
    return render(request, 'templates_app/template_create.html', context)


@login_required
def template_edit(request, template_id):
    """Édition d'un template"""
    template = get_object_or_404(Template, id=template_id, created_by=request.user)

    if request.method == 'POST':
        form = TemplateForm(request.POST, instance=template)
        if form.is_valid():
            template = form.save()

            # Re-détecter les champs après modification
            detect_and_create_fields(template)

            messages.success(request, f'Template "{template.title}" modifié avec succès!')
            return redirect('templates_app:template_detail', template_id=template.id)
        else:
            messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
    else:
        form = TemplateForm(instance=template)

    categories = TemplateCategory.objects.all().order_by('name')

    context = {
        'form': form,
        'template': template,
        'categories': categories,
        'title': 'Modifier le template'
    }
    return render(request, 'templates_app/template_create.html', context)


@login_required
def template_edit_fields(request, template_id):
    """Édition des champs d'un template"""
    template = get_object_or_404(Template, id=template_id, created_by=request.user)
    fields = template.fields.all().order_by('order', 'id')

    context = {
        'template': template,
        'fields': fields,
    }
    return render(request, 'templates_app/template_edit_fields.html', context)


def template_preview(request, template_id):
    """Prévisualiser un template avec des données d'exemple"""
    template = get_object_or_404(Template, id=template_id)

    # Vérifier les permissions
    if not template.is_public and template.created_by != request.user:
        messages.error(request, "Vous n'avez pas accès à ce template.")
        return redirect('templates_app:template_list')

    # Créer des valeurs d'exemple pour les champs
    example_values = {}
    for field in template.fields.all():
        example_values[field.field_name] = f"[{field.field_label}]"

    # Rendre le contenu avec les valeurs d'exemple
    rendered_content = render_template_content(template.content, example_values)

    context = {
        'template': template,
        'rendered_content': rendered_content,
        'example_values': example_values,
    }
    return render(request, 'templates_app/template_preview.html', context)


# ===============================
# VUES POUR LES DOCUMENTS
# ===============================

@login_required
def document_list(request):
    """Liste des documents de l'utilisateur"""
    documents = Document.objects.filter(created_by=request.user).select_related('template')

    # Filtres
    search = request.GET.get('search', '')
    template_id = request.GET.get('template', '')
    status = request.GET.get('status', '')

    if search:
        documents = documents.filter(title__icontains=search)

    if template_id:
        documents = documents.filter(template_id=template_id)

    if status == 'completed':
        documents = documents.filter(is_completed=True)
    elif status == 'draft':
        documents = documents.filter(is_completed=False)

    # Tri par date de modification
    documents = documents.order_by('-updated_at')

    # Pagination
    paginator = Paginator(documents, 15)
    page = request.GET.get('page')
    documents_page = paginator.get_page(page)

    # Templates pour le filtre
    user_templates = Template.objects.filter(
        Q(created_by=request.user) | Q(is_public=True)
    ).order_by('title')

    context = {
        'documents': documents_page,
        'templates': user_templates,
        'search': search,
        'selected_template': template_id,
        'selected_status': status,
    }
    return render(request, 'templates_app/document_list.html', context)


@login_required
def document_create(request, template_id):
    """Créer un nouveau document basé sur un template"""
    template = get_object_or_404(Template, id=template_id)

    # Vérifier les permissions
    if not template.is_public and template.created_by != request.user:
        messages.error(request, "Vous n'avez pas accès à ce template.")
        return redirect('templates_app:template_list')

    if request.method == 'POST':
        form = DocumentForm(request.POST)
        if form.is_valid():
            # Créer le document
            document = form.save(commit=False)
            document.template = template
            document.created_by = request.user
            if not document.title:
                document.title = f'Document basé sur {template.title}'
            document.save()

            # Sauvegarder les valeurs des champs
            for field in template.fields.all():
                value = request.POST.get(f'field_{field.id}', '')
                if value or field.is_required:
                    DocumentFieldValue.objects.create(
                        document=document,
                        template_field=field,
                        value=value
                    )

            # Marquer comme terminé si demandé
            if request.POST.get('mark_completed'):
                document.is_completed = True
                document.save()

            messages.success(request, f'Document "{document.title}" créé avec succès!')
            return redirect('templates_app:document_detail', document_id=document.id)
        else:
            messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
    else:
        form = DocumentForm(initial={'title': f'Document basé sur {template.title}'})

    # Récupérer les champs du template
    fields = template.fields.all().order_by('order', 'id')

    context = {
        'template': template,
        'form': form,
        'fields': fields,
        'title': 'Créer un document'
    }
    return render(request, 'templates_app/document_form.html', context)


@login_required
def document_detail(request, document_id):
    """Détail d'un document avec rendu final"""
    document = get_object_or_404(Document, id=document_id, created_by=request.user)

    # Récupérer les valeurs des champs
    field_values = {}
    for value in document.field_values.select_related('template_field'):
        field_values[value.template_field.field_name] = value.value

    # Rendu du contenu avec les valeurs
    rendered_content = render_template_content(document.template.content, field_values)

    context = {
        'document': document,
        'rendered_content': rendered_content,
        'field_values': field_values,
    }
    return render(request, 'templates_app/document_detail.html', context)


@login_required
def document_edit(request, document_id):
    """Éditer un document existant"""
    document = get_object_or_404(Document, id=document_id, created_by=request.user)

    if request.method == 'POST':
        form = DocumentForm(request.POST, instance=document)
        if form.is_valid():
            document = form.save()

            # Mettre à jour les valeurs des champs
            for field in document.template.fields.all():
                value = request.POST.get(f'field_{field.id}', '')
                field_value, created = DocumentFieldValue.objects.get_or_create(
                    document=document,
                    template_field=field,
                    defaults={'value': value}
                )
                if not created:
                    field_value.value = value
                    field_value.save()

            # Statut
            document.is_completed = bool(request.POST.get('mark_completed'))
            document.save()

            messages.success(request, f'Document "{document.title}" modifié avec succès!')
            return redirect('templates_app:document_detail', document_id=document.id)
        else:
            messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
    else:
        form = DocumentForm(instance=document)

    # Préparer les valeurs actuelles
    current_values = {}
    for value in document.field_values.select_related('template_field'):
        current_values[f'field_{value.template_field.id}'] = value.value

    fields = document.template.fields.all().order_by('order', 'id')

    context = {
        'document': document,
        'template': document.template,
        'form': form,
        'fields': fields,
        'current_values': current_values,
        'title': 'Modifier le document'
    }
    return render(request, 'templates_app/document_form.html', context)


@login_required
def document_export_pdf(request, document_id):
    """Exporter un document en PDF"""
    document = get_object_or_404(Document, id=document_id, created_by=request.user)

    # Récupérer les valeurs des champs
    field_values = {}
    for value in document.field_values.select_related('template_field'):
        field_values[value.template_field.field_name] = value.value

    # Rendu du contenu
    rendered_content = render_template_content(document.template.content, field_values)

    # Pour l'instant, on retourne du HTML
    # TODO: Implémenter l'export PDF avec reportlab ou weasyprint
    response = HttpResponse(rendered_content, content_type='text/html')
    response['Content-Disposition'] = f'attachment; filename="{document.title}.html"'
    return response


# ===============================
# VUES AJAX
# ===============================

@login_required
@require_http_methods(["POST"])
def template_add_field(request, template_id):
    """Ajouter un champ à un template (AJAX)"""
    template = get_object_or_404(Template, id=template_id, created_by=request.user)

    try:
        data = json.loads(request.body)

        # Validation des données
        field_name = data.get('field_name', '').strip()
        if not field_name or not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', field_name):
            return JsonResponse({
                'success': False,
                'error': 'Nom de champ invalide. Utilisez uniquement lettres, chiffres et underscores.'
            })

        # Vérifier si le champ existe déjà
        if TemplateField.objects.filter(template=template, field_name=field_name).exists():
            return JsonResponse({
                'success': False,
                'error': f'Le champ "{field_name}" existe déjà.'
            })

        field = TemplateField.objects.create(
            template=template,
            field_name=field_name,
            field_label=data.get('field_label', field_name.replace('_', ' ').title()),
            field_type=data.get('field_type', 'text'),
            placeholder_text=data.get('placeholder_text', ''),
            is_required=data.get('is_required', False),
            field_options=json.dumps(data.get('field_options', [])) if data.get('field_options') else '',
            order=data.get('order', 0)
        )

        return JsonResponse({
            'success': True,
            'field': {
                'id': field.id,
                'field_name': field.field_name,
                'field_label': field.field_label,
                'field_type': field.field_type,
                'is_required': field.is_required,
            }
        })
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Données JSON invalides'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def template_delete_field(request, template_id, field_id):
    """Supprimer un champ de template"""
    template = get_object_or_404(Template, id=template_id, created_by=request.user)
    field = get_object_or_404(TemplateField, id=field_id, template=template)

    field_name = field.field_name
    field.delete()

    messages.success(request, f'Champ "{field_name}" supprimé avec succès!')
    return redirect('templates_app:template_edit_fields', template_id=template_id)


@login_required
def template_delete(request, template_id):
    """Supprimer un template"""
    template = get_object_or_404(Template, id=template_id, created_by=request.user)

    if request.method == 'POST':
        template_title = template.title
        template.delete()
        messages.success(request, f'Template "{template_title}" supprimé avec succès!')
        return redirect('templates_app:template_list')

    # Si GET, afficher une page de confirmation
    context = {
        'template': template,
        'documents_count': template.documents.count()
    }
    return render(request, 'templates_app/template_confirm_delete.html', context)


@login_required
def template_duplicate(request, template_id):
    """Dupliquer un template"""
    original_template = get_object_or_404(Template, id=template_id)

    # Vérifier les permissions
    if not original_template.is_public and original_template.created_by != request.user:
        messages.error(request, "Vous n'avez pas accès à ce template.")
        return redirect('templates_app:template_list')

    # Créer une copie du template
    new_template = Template.objects.create(
        title=f"{original_template.title} (Copie)",
        description=original_template.description,
        content=original_template.content,
        category=original_template.category,
        created_by=request.user,
        is_public=False  # La copie est toujours privée
    )

    # Copier les champs
    for field in original_template.fields.all():
        TemplateField.objects.create(
            template=new_template,
            field_name=field.field_name,
            field_label=field.field_label,
            field_type=field.field_type,
            placeholder_text=field.placeholder_text,
            is_required=field.is_required,
            field_options=field.field_options,
            order=field.order
        )

    messages.success(request, f'Template dupliqué avec succès ! Vous pouvez maintenant le modifier.')
    return redirect('templates_app:template_detail', template_id=new_template.id)


@login_required
def template_export(request, template_id):
    """Exporter un template"""
    template = get_object_or_404(Template, id=template_id)

    # Vérifier les permissions
    if not template.is_public and template.created_by != request.user:
        messages.error(request, "Vous n'avez pas accès à ce template.")
        return redirect('templates_app:template_list')

    export_format = request.GET.get('format', 'json')

    if export_format == 'json':
        # Export JSON complet
        template_data = {
            'title': template.title,
            'description': template.description,
            'content': template.content,
            'category': template.category.name if template.category else None,
            'fields': []
        }

        for field in template.fields.all():
            template_data['fields'].append({
                'field_name': field.field_name,
                'field_label': field.field_label,
                'field_type': field.field_type,
                'placeholder_text': field.placeholder_text,
                'is_required': field.is_required,
                'field_options': field.field_options,
                'order': field.order
            })

        response = JsonResponse(template_data, json_dumps_params={'indent': 2})
        response['Content-Disposition'] = f'attachment; filename="{template.title}.json"'
        return response

    elif export_format == 'html':
        # Export HTML simple
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{template.title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .field-highlight {{ background: #fff3cd; padding: 2px 4px; border-radius: 3px; }}
            </style>
        </head>
        <body>
            <h1>{template.title}</h1>
            {template.description and f'<p><em>{template.description}</em></p>' or ''}
            <hr>
            {apply_basic_formatting(template.content)}
        </body>
        </html>
        """

        response = HttpResponse(html_content, content_type='text/html')
        response['Content-Disposition'] = f'attachment; filename="{template.title}.html"'
        return response

    else:
        messages.error(request, 'Format d\'export non supporté.')
        return redirect('templates_app:template_detail', template_id=template_id)


@login_required
def document_delete(request, document_id):
    """Supprimer un document"""
    document = get_object_or_404(Document, id=document_id, created_by=request.user)

    if request.method == 'POST':
        document_title = document.title
        document.delete()
        messages.success(request, f'Document "{document_title}" supprimé avec succès!')
        return redirect('templates_app:document_list')

    # Si GET, afficher une page de confirmation
    context = {
        'document': document
    }
    return render(request, 'templates_app/document_confirm_delete.html', context)


@login_required
def document_duplicate(request, document_id):
    """Dupliquer un document"""
    original_document = get_object_or_404(Document, id=document_id, created_by=request.user)

    # Créer une copie du document
    new_document = Document.objects.create(
        template=original_document.template,
        title=f"{original_document.title} (Copie)",
        created_by=request.user,
        is_completed=False  # La copie est un brouillon
    )

    # Copier les valeurs des champs
    for field_value in original_document.field_values.all():
        DocumentFieldValue.objects.create(
            document=new_document,
            template_field=field_value.template_field,
            value=field_value.value
        )

    messages.success(request, f'Document dupliqué avec succès ! Vous pouvez maintenant le modifier.')
    return redirect('templates_app:document_detail', document_id=new_document.id)


@login_required
def document_export_html(request, document_id):
    """Exporter un document en HTML"""
    document = get_object_or_404(Document, id=document_id, created_by=request.user)

    # Récupérer les valeurs des champs
    field_values = {}
    for value in document.field_values.select_related('template_field'):
        field_values[value.template_field.field_name] = value.value

    # Rendu du contenu
    rendered_content = render_template_content(document.template.content, field_values)

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{document.title}</title>
        <style>
            body {{ 
                font-family: 'Times New Roman', serif; 
                margin: 40px; 
                line-height: 1.6; 
            }}
            @media print {{
                body {{ margin: 20mm; }}
            }}
        </style>
    </head>
    <body>
        {rendered_content}
    </body>
    </html>
    """

    response = HttpResponse(html_content, content_type='text/html')
    response['Content-Disposition'] = f'attachment; filename="{document.title}.html"'
    return response


@login_required
def document_export_docx(request, document_id):
    """Exporter un document en DOCX (placeholder)"""
    document = get_object_or_404(Document, id=document_id, created_by=request.user)

    # TODO: Implémenter l'export DOCX avec python-docx
    messages.warning(request, 'Export DOCX non encore implémenté. Utilisez l\'export HTML.')
    return redirect('templates_app:document_detail', document_id=document_id)


# Placeholder pour les autres vues référencées dans les URLs
def document_share(request, document_id):
    """Partager un document (placeholder)"""
    messages.info(request, 'Fonctionnalité de partage en cours de développement.')
    return redirect('templates_app:document_detail', document_id=document_id)


def document_public_view(request, document_id):
    """Vue publique d'un document (placeholder)"""
    messages.info(request, 'Vue publique en cours de développement.')
    return redirect('templates_app:document_detail', document_id=document_id)


def category_list(request):
    """Liste des catégories (placeholder)"""
    messages.info(request, 'Gestion des catégories en cours de développement.')
    return redirect('templates_app:template_list')


def category_create(request):
    """Créer une catégorie (placeholder)"""
    messages.info(request, 'Gestion des catégories en cours de développement.')
    return redirect('templates_app:template_list')


def category_edit(request, category_id):
    """Modifier une catégorie (placeholder)"""
    messages.info(request, 'Gestion des catégories en cours de développement.')
    return redirect('templates_app:template_list')


def category_delete(request, category_id):
    """Supprimer une catégorie (placeholder)"""
    messages.info(request, 'Gestion des catégories en cours de développement.')
    return redirect('templates_app:template_list')


# ===============================
# FONCTIONS UTILITAIRES
# ===============================

def render_template_content(content, field_values):
    """Rendre le contenu du template avec les valeurs des champs"""
    try:
        # Remplacer les placeholders {{field_name}} par les valeurs
        for field_name, value in field_values.items():
            placeholder = f'{{{{{field_name}}}}}'
            content = content.replace(placeholder, str(value) if value else '')

        # Nettoyer les placeholders non remplis
        content = re.sub(r'\{\{[^}]+\}\}', '[Non renseigné]', content)

        # Appliquer le formatage simple
        content = apply_basic_formatting(content)

        return content
    except Exception as e:
        return f"Erreur lors du rendu: {str(e)}"


def apply_basic_formatting(content):
    """Appliquer un formatage de base au contenu"""
    try:
        # Formatage Markdown simple
        content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
        content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', content)
        content = re.sub(r'_(.*?)_', r'<u>\1</u>', content)

        # Formatage personnalisé
        content = re.sub(r'\[CENTER\](.*?)\[/CENTER\]', r'<div style="text-align: center;">\1</div>', content,
                         flags=re.DOTALL)
        content = re.sub(r'\[JUSTIFY\](.*?)\[/JUSTIFY\]', r'<div style="text-align: justify;">\1</div>', content,
                         flags=re.DOTALL)
        content = re.sub(r'\[RIGHT\](.*?)\[/RIGHT\]', r'<div style="text-align: right;">\1</div>', content,
                         flags=re.DOTALL)

        # Conversion des retours à la ligne
        content = content.replace('\n', '<br>')

        return content
    except Exception as e:
        return content


def detect_and_create_fields(template):
    """Détecter automatiquement les champs dans le contenu et les créer"""
    try:
        # Pattern pour détecter les champs {{field_name}}
        field_pattern = r'\{\{([^}]+)\}\}'
        matches = re.findall(field_pattern, template.content)

        # Nettoyer et dédupliquer les noms de champs
        field_names = set()
        for match in matches:
            field_name = match.strip()
            if field_name and re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', field_name):
                field_names.add(field_name)

        # Créer les champs qui n'existent pas encore
        existing_fields = set(
            template.fields.values_list('field_name', flat=True)
        )

        for field_name in field_names:
            if field_name not in existing_fields:
                # Générer un label automatique
                field_label = field_name.replace('_', ' ').title()

                # Déterminer le type de champ
                field_type = determine_field_type(field_name)

                # Déterminer si le champ est requis
                is_required = is_field_likely_required(field_name)

                TemplateField.objects.create(
                    template=template,
                    field_name=field_name,
                    field_label=field_label,
                    field_type=field_type,
                    is_required=is_required,
                    order=0
                )

        # Supprimer les champs qui ne sont plus dans le contenu
        template.fields.exclude(field_name__in=field_names).delete()

    except Exception as e:
        print(f"Erreur lors de la détection des champs: {e}")


def determine_field_type(field_name):
    """Déterminer automatiquement le type d'un champ basé sur son nom"""
    field_name_lower = field_name.lower()

    # Types basés sur le nom
    if any(word in field_name_lower for word in ['email', 'mail']):
        return 'email'
    elif any(word in field_name_lower for word in ['date', 'debut', 'fin', 'naissance', 'signature']):
        return 'date'
    elif any(word in field_name_lower for word in
             ['montant', 'prix', 'salaire', 'cout', 'total', 'nombre', 'quantite', 'qte']):
        return 'number'
    elif any(word in field_name_lower for word in ['url', 'site', 'lien']):
        return 'url'
    elif any(word in field_name_lower for word in ['adresse', 'description', 'commentaire', 'note', 'contenu']):
        return 'textarea'
    else:
        return 'text'


def is_field_likely_required(field_name):
    """Déterminer si un champ est probablement requis"""
    field_name_lower = field_name.lower()

    # Champs généralement requis
    required_patterns = [
        'nom', 'prenom', 'entreprise', 'societe', 'client', 'poste', 'fonction',
        'montant', 'prix', 'total', 'date_debut', 'date_signature'
    ]

    return any(pattern in field_name_lower for pattern in required_patterns)