# forms.py
from django import forms
from django.core.exceptions import ValidationError
from .models import Template, TemplateField, Document, TemplateCategory
import re


class TemplateForm(forms.ModelForm):
    """Formulaire pour créer/modifier un template"""

    class Meta:
        model = Template
        fields = ['title', 'description', 'content', 'category', 'is_public']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Contrat de Travail CDI',
                'maxlength': 200
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Décrivez brièvement l\'usage de ce template...'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control textarea-editor',
                'rows': 20,
                'placeholder': '''Rédigez votre template ici...

Exemple :
CONTRAT DE TRAVAIL

Entre l'entreprise {{nom_entreprise}} et {{nom_employe}}

Poste: {{poste}}
Salaire: {{salaire}} €
Date de début: {{date_debut}}

Signature employeur: _______________
Signature employé: _______________'''
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'title': 'Titre du template',
            'description': 'Description',
            'content': 'Contenu du template',
            'category': 'Catégorie',
            'is_public': 'Template public'
        }
        help_texts = {
            'title': 'Donnez un nom explicite à votre template',
            'description': 'Décrivez à quoi sert ce template',
            'content': 'Rédigez le contenu avec des champs dynamiques {{nom_champ}}',
            'is_public': 'Si coché, ce template sera visible par tous les utilisateurs'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Rendre le titre obligatoire avec une meilleure validation
        self.fields['title'].required = True

        # Rendre le contenu obligatoire
        self.fields['content'].required = True

        # Ajouter une option vide pour la catégorie
        self.fields['category'].empty_label = "Sélectionner une catégorie"
        self.fields['category'].required = False

    def clean_title(self):
        """Validation personnalisée du titre"""
        title = self.cleaned_data.get('title', '').strip()

        if not title:
            raise ValidationError("Le titre est obligatoire.")

        if len(title) < 3:
            raise ValidationError("Le titre doit contenir au moins 3 caractères.")

        # Vérifier l'unicité pour l'utilisateur (si c'est une création)
        if not self.instance.pk:  # Nouveau template
            # Note: Nous devrons passer l'utilisateur dans la vue
            pass

        return title

    def clean_content(self):
        """Validation personnalisée du contenu"""
        content = self.cleaned_data.get('content', '').strip()

        if not content:
            raise ValidationError("Le contenu est obligatoire.")

        if len(content) < 10:
            raise ValidationError("Le contenu doit contenir au moins 10 caractères.")

        # Vérifier la syntaxe des champs dynamiques
        field_pattern = r'\{\{([^}]+)\}\}'
        matches = re.findall(field_pattern, content)

        invalid_fields = []
        for match in matches:
            field_name = match.strip()
            # Vérifier que le nom du champ est valide
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', field_name):
                invalid_fields.append(field_name)

        if invalid_fields:
            raise ValidationError(
                f"Noms de champs invalides: {', '.join(invalid_fields)}. "
                "Utilisez uniquement lettres, chiffres et underscores (pas d'espaces)."
            )

        return content


class TemplateFieldForm(forms.ModelForm):
    """Formulaire pour configurer un champ de template"""

    class Meta:
        model = TemplateField
        fields = [
            'field_name', 'field_label', 'field_type',
            'placeholder_text', 'is_required', 'field_options', 'order'
        ]
        widgets = {
            'field_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'nom_du_champ',
                'pattern': '[a-zA-Z_][a-zA-Z0-9_]*'
            }),
            'field_label': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Label affiché à l\'utilisateur'
            }),
            'field_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'placeholder_text': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Texte d\'aide pour l\'utilisateur'
            }),
            'is_required': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'field_options': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Option 1\nOption 2\nOption 3'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            })
        }
        labels = {
            'field_name': 'Nom du champ',
            'field_label': 'Label affiché',
            'field_type': 'Type de champ',
            'placeholder_text': 'Texte d\'aide',
            'is_required': 'Champ obligatoire',
            'field_options': 'Options (pour liste déroulante)',
            'order': 'Ordre d\'affichage'
        }

    def clean_field_name(self):
        """Validation du nom de champ"""
        field_name = self.cleaned_data.get('field_name', '').strip()

        if not field_name:
            raise ValidationError("Le nom du champ est obligatoire.")

        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', field_name):
            raise ValidationError(
                "Le nom du champ doit commencer par une lettre ou un underscore, "
                "et ne contenir que des lettres, chiffres et underscores."
            )

        return field_name

    def clean(self):
        """Validation globale du formulaire"""
        cleaned_data = super().clean()
        field_type = cleaned_data.get('field_type')
        field_options = cleaned_data.get('field_options')

        # Si c'est un champ select, les options sont obligatoires
        if field_type == 'select' and not field_options:
            raise ValidationError({
                'field_options': 'Les options sont obligatoires pour un champ de type "Liste déroulante".'
            })

        return cleaned_data


class DocumentForm(forms.ModelForm):
    """Formulaire pour créer/modifier un document"""

    class Meta:
        model = Document
        fields = ['title']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Titre du document'
            })
        }
        labels = {
            'title': 'Titre du document'
        }

    def clean_title(self):
        """Validation du titre du document"""
        title = self.cleaned_data.get('title', '').strip()

        if not title:
            raise ValidationError("Le titre du document est obligatoire.")

        if len(title) < 3:
            raise ValidationError("Le titre doit contenir au moins 3 caractères.")

        return title


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
                'placeholder': 'Description de la catégorie'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'value': '#007bff'
            })
        }
        labels = {
            'name': 'Nom de la catégorie',
            'description': 'Description',
            'color': 'Couleur'
        }


class DocumentFieldValueForm(forms.Form):
    """Formulaire dynamique pour saisir les valeurs des champs d'un document"""

    def __init__(self, template_fields, current_values=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Créer un champ pour chaque champ du template
        for field in template_fields:
            field_name = f'field_{field.id}'

            # Déterminer le widget selon le type
            if field.field_type == 'textarea':
                widget = forms.Textarea(attrs={
                    'class': 'form-control',
                    'rows': 4,
                    'placeholder': field.placeholder_text
                })
            elif field.field_type == 'number':
                widget = forms.NumberInput(attrs={
                    'class': 'form-control',
                    'placeholder': field.placeholder_text
                })
            elif field.field_type == 'date':
                widget = forms.DateInput(attrs={
                    'class': 'form-control',
                    'type': 'date'
                })
            elif field.field_type == 'email':
                widget = forms.EmailInput(attrs={
                    'class': 'form-control',
                    'placeholder': field.placeholder_text
                })
            elif field.field_type == 'url':
                widget = forms.URLInput(attrs={
                    'class': 'form-control',
                    'placeholder': field.placeholder_text
                })
            elif field.field_type == 'select':
                # Récupérer les options
                options = field.get_options_list()
                choices = [('', 'Sélectionner...')] + [(opt, opt) for opt in options]
                widget = forms.Select(choices=choices, attrs={'class': 'form-select'})
            else:  # text par défaut
                widget = forms.TextInput(attrs={
                    'class': 'form-control',
                    'placeholder': field.placeholder_text
                })

            # Créer le champ
            self.fields[field_name] = forms.CharField(
                label=field.field_label,
                required=field.is_required,
                widget=widget,
                help_text=field.placeholder_text if field.placeholder_text else None
            )

            # Définir la valeur actuelle si fournie
            if current_values and field_name in current_values:
                self.fields[field_name].initial = current_values[field_name]


class TemplateSearchForm(forms.Form):
    """Formulaire de recherche et filtrage des templates"""

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher un template...',
            'autocomplete': 'off'
        })
    )

    category = forms.ModelChoiceField(
        queryset=TemplateCategory.objects.all(),
        required=False,
        empty_label="Toutes les catégories",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    visibility = forms.ChoiceField(
        choices=[
            ('', 'Tous les templates'),
            ('my', 'Mes templates'),
            ('public', 'Templates publics')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    sort_by = forms.ChoiceField(
        choices=[
            ('-created_at', 'Plus récents'),
            ('created_at', 'Plus anciens'),
            ('title', 'Nom A-Z'),
            ('-title', 'Nom Z-A'),
            ('-documents_count', 'Plus utilisés')
        ],
        required=False,
        initial='-created_at',
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class DocumentSearchForm(forms.Form):
    """Formulaire de recherche et filtrage des documents"""

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher un document...',
            'autocomplete': 'off'
        })
    )

    template = forms.ModelChoiceField(
        queryset=Template.objects.none(),  # Sera défini dans la vue
        required=False,
        empty_label="Tous les templates",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    status = forms.ChoiceField(
        choices=[
            ('', 'Tous les statuts'),
            ('draft', 'Brouillons'),
            ('completed', 'Terminés')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    sort_by = forms.ChoiceField(
        choices=[
            ('-updated_at', 'Modifiés récemment'),
            ('-created_at', 'Créés récemment'),
            ('title', 'Nom A-Z'),
            ('-title', 'Nom Z-A')
        ],
        required=False,
        initial='-updated_at',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Définir les templates disponibles pour l'utilisateur
        if user and user.is_authenticated:
            from django.db.models import Q
            self.fields['template'].queryset = Template.objects.filter(
                Q(created_by=user) | Q(is_public=True)
            ).order_by('title')


class BulkActionForm(forms.Form):
    """Formulaire pour les actions en lot"""

    ACTION_CHOICES = [
        ('', 'Sélectionner une action'),
        ('delete', 'Supprimer'),
        ('duplicate', 'Dupliquer'),
        ('export', 'Exporter'),
        ('change_category', 'Changer de catégorie'),
        ('toggle_public', 'Basculer public/privé')
    ]

    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'onchange': 'toggleActionOptions(this.value)'
        })
    )

    selected_items = forms.CharField(
        widget=forms.HiddenInput()
    )

    # Champs conditionnels
    new_category = forms.ModelChoiceField(
        queryset=TemplateCategory.objects.all(),
        required=False,
        empty_label="Sélectionner une catégorie",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'style': 'display: none;'
        })
    )

    def clean_selected_items(self):
        """Validation des éléments sélectionnés"""
        selected_items = self.cleaned_data.get('selected_items', '')

        if not selected_items:
            raise ValidationError("Aucun élément sélectionné.")

        try:
            # Convertir en liste d'entiers
            item_ids = [int(x) for x in selected_items.split(',') if x.strip()]
            if not item_ids:
                raise ValidationError("Aucun élément valide sélectionné.")
            return item_ids
        except (ValueError, TypeError):
            raise ValidationError("IDs d'éléments invalides.")

    def clean(self):
        """Validation globale"""
        cleaned_data = super().clean()
        action = cleaned_data.get('action')

        # Validation spécifique selon l'action
        if action == 'change_category':
            new_category = cleaned_data.get('new_category')
            if not new_category:
                raise ValidationError({
                    'new_category': 'Veuillez sélectionner une catégorie.'
                })

        return cleaned_data


class AdvancedSearchForm(forms.Form):
    """Formulaire de recherche avancée"""

    # Critères de recherche
    title_contains = forms.CharField(
        required=False,
        label="Titre contient",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mots dans le titre...'
        })
    )

    content_contains = forms.CharField(
        required=False,
        label="Contenu contient",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mots dans le contenu...'
        })
    )

    has_field = forms.CharField(
        required=False,
        label="Contient le champ",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'nom_du_champ'
        })
    )

    # Filtres de date
    created_after = forms.DateField(
        required=False,
        label="Créé après",
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    created_before = forms.DateField(
        required=False,
        label="Créé avant",
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    # Filtres numériques
    min_fields = forms.IntegerField(
        required=False,
        label="Nombre minimum de champs",
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 0
        })
    )

    max_fields = forms.IntegerField(
        required=False,
        label="Nombre maximum de champs",
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 0
        })
    )

    # Filtres d'utilisation
    min_documents = forms.IntegerField(
        required=False,
        label="Minimum de documents créés",
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 0
        })
    )

    def clean(self):
        """Validation des dates et nombres"""
        cleaned_data = super().clean()

        # Validation des dates
        created_after = cleaned_data.get('created_after')
        created_before = cleaned_data.get('created_before')

        if created_after and created_before and created_after > created_before:
            raise ValidationError("La date 'Créé après' doit être antérieure à 'Créé avant'.")

        # Validation des champs min/max
        min_fields = cleaned_data.get('min_fields')
        max_fields = cleaned_data.get('max_fields')

        if min_fields is not None and max_fields is not None and min_fields > max_fields:
            raise ValidationError("Le nombre minimum de champs doit être inférieur ou égal au maximum.")

        return cleaned_data


class ImportTemplateForm(forms.Form):
    """Formulaire pour importer un template depuis un fichier"""

    IMPORT_FORMATS = [
        ('json', 'JSON'),
        ('csv', 'CSV'),
        ('txt', 'Texte brut')
    ]

    file = forms.FileField(
        label="Fichier à importer",
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.json,.csv,.txt'
        }),
        help_text="Formats supportés: JSON, CSV, TXT (max 5MB)"
    )

    format = forms.ChoiceField(
        choices=IMPORT_FORMATS,
        label="Format du fichier",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    category = forms.ModelChoiceField(
        queryset=TemplateCategory.objects.all(),
        required=False,
        empty_label="Aucune catégorie",
        label="Catégorie pour les templates importés",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    make_public = forms.BooleanField(
        required=False,
        label="Rendre les templates publics",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def clean_file(self):
        """Validation du fichier uploadé"""
        file = self.cleaned_data.get('file')

        if not file:
            raise ValidationError("Aucun fichier sélectionné.")

        # Vérifier la taille (5MB max)
        if file.size > 5 * 1024 * 1024:
            raise ValidationError("Le fichier ne doit pas dépasser 5MB.")

        # Vérifier l'extension
        allowed_extensions = ['.json', '.csv', '.txt']
        file_extension = '.' + file.name.split('.')[-1].lower()

        if file_extension not in allowed_extensions:
            raise ValidationError(f"Extension non supportée. Utilisez: {', '.join(allowed_extensions)}")

        return file


class ExportTemplateForm(forms.Form):
    """Formulaire pour exporter des templates"""

    EXPORT_FORMATS = [
        ('json', 'JSON (complet)'),
        ('csv', 'CSV (données tabulaires)'),
        ('pdf', 'PDF (aperçu)'),
        ('html', 'HTML (web)'),
        ('docx', 'Word (document)')
    ]

    templates = forms.ModelMultipleChoiceField(
        queryset=Template.objects.none(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label="Templates à exporter"
    )

    format = forms.ChoiceField(
        choices=EXPORT_FORMATS,
        label="Format d'export",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    include_fields = forms.BooleanField(
        required=False,
        initial=True,
        label="Inclure la configuration des champs",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    include_documents = forms.BooleanField(
        required=False,
        label="Inclure les documents créés",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Limiter aux templates de l'utilisateur
        if user and user.is_authenticated:
            from django.db.models import Q
            self.fields['templates'].queryset = Template.objects.filter(
                Q(created_by=user) | Q(is_public=True)
            ).order_by('title')


# Formset pour gérer plusieurs champs de template
from django.forms import inlineformset_factory

TemplateFieldFormSet = inlineformset_factory(
    Template,
    TemplateField,
    form=TemplateFieldForm,
    extra=0,
    can_delete=True,
    can_order=True
)