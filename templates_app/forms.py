from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Template, TemplateField, Document, TemplateCategory


class CustomUserCreationForm(UserCreationForm):
    """Formulaire d'inscription personnalisé"""

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre adresse email'
        })
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Choisissez un nom d\'utilisateur',
                'maxlength': '150'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personnaliser les widgets pour les champs de mot de passe
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Choisissez un mot de passe sécurisé'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Répétez votre mot de passe'
        })

        # Personnaliser les labels
        self.fields['username'].label = 'Nom d\'utilisateur'
        self.fields['email'].label = 'Adresse email'
        self.fields['password1'].label = 'Mot de passe'
        self.fields['password2'].label = 'Confirmer le mot de passe'

        # Tous les champs sont requis
        for field_name, field in self.fields.items():
            field.required = True

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class CustomAuthenticationForm(AuthenticationForm):
    """Formulaire de connexion personnalisé"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Personnaliser les widgets
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Votre nom d\'utilisateur'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Votre mot de passe'
        })

        # Personnaliser les labels
        self.fields['username'].label = 'Nom d\'utilisateur'
        self.fields['password'].label = 'Mot de passe'
# Alternative : Formulaires entièrement personnalisés sans héritage Django

class SimpleSignupForm(forms.Form):
    """Formulaire d'inscription simple sans héritage Django"""

    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Choisissez un nom d\'utilisateur'
        }),
        label='Nom d\'utilisateur'
    )

    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Choisissez un mot de passe sécurisé'
        }),
        label='Mot de passe'
    )

    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Répétez votre mot de passe'
        }),
        label='Confirmer le mot de passe'
    )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Ce nom d'utilisateur existe déjà.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")

        return cleaned_data


class SimpleLoginForm(forms.Form):
    """Formulaire de connexion simple"""

    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre nom d\'utilisateur'
        }),
        label='Nom d\'utilisateur'
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre mot de passe'
        }),
        label='Mot de passe'
    )

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