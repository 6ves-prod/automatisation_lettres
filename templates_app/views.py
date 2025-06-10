from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse, Http404
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from .models import Template, Document, TemplateField, DocumentFieldValue, TemplateCategory
from .forms import TemplateForm, DocumentForm, TemplateFieldForm, TemplateCategoryForm
import re


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

    if search:
        templates = templates.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search)
        )

    if category_id:
        templates = templates.filter(category_id=category_id)

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
        if field.field_type == 'text':
            preview_data[field.field_name] = f"[Exemple de {field.field_label.lower()}]"
        elif field.field_type == 'email':
            preview_data[field.field_name] = "exemple@email.com"
        elif field.field_type == 'date':
            preview_data[field.field_name] = "01/01/2024"
        elif field.field_type == 'number':
            preview_data[field.field_name] = "100"
        elif field.field_type == 'url':
            preview_data[field.field_name] = "https://exemple.com"
        elif field.field_type == 'textarea':
            preview_data[field.field_name] = f"[Texte d'exemple pour {field.field_label.lower()}]"
        elif field.field_type == 'select':
            preview_data[field.field_name] = "[Option sélectionnée]"
        else:
            preview_data[field.field_name] = f"[{field.field_label}]"

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
                            field=field,
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
        'document': None,  # Pas de document existant pour création
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
        current_values[f'field_{field_value.field.id}'] = field_value.value

    if request.method == 'POST':
        form = DocumentForm(request.POST, instance=document)

        if form.is_valid():
            try:
                # Mettre à jour le document
                document = form.save(commit=False)
                document.is_completed = request.POST.get('mark_completed') == 'on'
                document.save()

                # Mettre à jour les valeurs des champs
                # Supprimer les anciennes valeurs
                document.field_values.all().delete()

                # Créer les nouvelles valeurs
                for field in fields:
                    field_name = f'field_{field.id}'
                    field_value = request.POST.get(field_name, '')

                    if field_value or field.is_required:
                        DocumentFieldValue.objects.create(
                            document=document,
                            field=field,
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


def document_detail(request, document_id):
    """Détail d'un document avec le contenu rendu"""
    document = get_object_or_404(Document, id=document_id, created_by=request.user)
    template = document.template

    # Récupérer les valeurs des champs
    field_values = {}
    rendered_values = {}

    for field_value in document.field_values.all():
        field_name = field_value.field.field_name
        field_values[field_name] = field_value.value
        rendered_values[field_value.field.field_label] = field_value.value

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
    """Liste des documents de l'utilisateur avec filtres"""
    documents = Document.objects.filter(created_by=request.user).order_by('-updated_at')

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

    # Pagination
    paginator = Paginator(documents, 10)
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
    }
    return render(request, 'templates_app/document_list.html', context)


# ===============================
# VUES DE PLACEHOLDERS (pour éviter les erreurs)
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
def document_delete(request, document_id):
    """Placeholder pour supprimer un document"""
    messages.info(request, "Fonction de suppression en cours de développement.")
    return redirect('templates_app:document_detail', document_id=document_id)


@login_required
def document_export_html(request, document_id):
    """Export HTML basique"""
    document = get_object_or_404(Document, id=document_id, created_by=request.user)
    messages.info(request, "Export HTML en cours de développement.")
    return redirect('templates_app:document_detail', document_id=document_id)


@login_required
def document_export_pdf(request, document_id):
    """Placeholder pour export PDF"""
    messages.info(request, "Export PDF en cours de développement.")
    return redirect('templates_app:document_detail', document_id=document_id)


@login_required
def document_export_docx(request, document_id):
    """Placeholder pour export DOCX"""
    messages.info(request, "Export DOCX en cours de développement.")
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

def create_fields_from_content(template):
    """Créer automatiquement les champs à partir du contenu du template"""
    if not template.content:
        return

    # Expression régulière pour trouver les placeholders {{field_name}}
    pattern = r'\{\{([a-zA-Z_][a-zA-Z0-9_]*)\}\}'
    matches = re.findall(pattern, template.content)

    if not matches:
        return

    # Supprimer les doublons et trier
    unique_fields = list(set(matches))
    unique_fields.sort()

    # Créer les champs qui n'existent pas encore
    existing_fields = set(template.fields.values_list('field_name', flat=True))

    for i, field_name in enumerate(unique_fields):
        if field_name not in existing_fields:
            # Créer un libellé lisible à partir du nom du champ
            field_label = field_name.replace('_', ' ').title()

            TemplateField.objects.create(
                template=template,
                field_name=field_name,
                field_label=field_label,
                field_type='text',  # Par défaut
                is_required=False,
                order=i * 10
            )