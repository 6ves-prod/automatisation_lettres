from django import forms
from django.contrib.auth.models import User
from .models import Template, TemplateField, Document, TemplateCategory


class TemplateForm(forms.ModelForm):
    """Formulaire pour créer/modifier un template"""

    class Meta:
        model = Template
        fields = ['title', 'description', 'content', 'category', 'is_public']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Titre du template'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description du template (optionnel)'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control textarea-editor',
                'rows': 15,
                'placeholder': 'Contenu du template avec des champs dynamiques comme {{nom_client}}, {{date}}, etc.'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }


class DocumentForm(forms.ModelForm):
    """Formulaire pour créer/modifier un document"""

    class Meta:
        model = Document
        fields = ['title']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Titre du document',
                'required': True
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].required = True


class TemplateFieldForm(forms.ModelForm):
    """Formulaire pour créer/modifier un champ de template"""

    class Meta:
        model = TemplateField
        # Vérifier quels champs existent réellement dans le modèle
        fields = ['field_name', 'field_label', 'field_type', 'placeholder_text', 'is_required', 'order']
        widgets = {
            'field_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'nom_du_champ (sans espaces)',
                'pattern': '[a-zA-Z_][a-zA-Z0-9_]*'
            }),
            'field_label': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Libellé affiché à l\'utilisateur'
            }),
            'field_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'placeholder_text': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Texte d\'aide (optionnel)'
            }),
            'is_required': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            })
        }

    def clean_field_name(self):
        """Valider que le nom du champ est valide"""
        field_name = self.cleaned_data.get('field_name')
        if field_name:
            import re
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', field_name):
                raise forms.ValidationError(
                    "Le nom du champ ne peut contenir que des lettres, chiffres et underscores, et doit commencer par une lettre ou un underscore.")
        return field_name


class TemplateCategoryForm(forms.ModelForm):
    """Formulaire pour créer/modifier une catégorie de template"""

    class Meta:
        model = TemplateCategory
        fields = ['name', 'description', 'color']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom de la catégorie'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description de la catégorie (optionnel)'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'value': '#007bff'
            })
        }