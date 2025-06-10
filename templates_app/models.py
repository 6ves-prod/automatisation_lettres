# models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json


class Template(models.Model):
    """Modèle principal pour les templates"""
    title = models.CharField(max_length=200, verbose_name="Titre du template")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    content = models.TextField(verbose_name="Contenu du template avec placeholders")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Créé par")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")
    is_public = models.BooleanField(default=False, verbose_name="Template public")

    class Meta:
        verbose_name = "Template"
        verbose_name_plural = "Templates"
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class TemplateField(models.Model):
    """Champs modifiables dans un template"""
    FIELD_TYPES = [
        ('text', 'Texte simple'),
        ('textarea', 'Texte long'),
        ('number', 'Nombre'),
        ('date', 'Date'),
        ('email', 'Email'),
        ('url', 'URL'),
        ('select', 'Liste déroulante'),
    ]

    template = models.ForeignKey(Template, on_delete=models.CASCADE, related_name='fields')
    field_name = models.CharField(max_length=100, verbose_name="Nom du champ")
    field_label = models.CharField(max_length=200, verbose_name="Label affiché")
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES, default='text')
    placeholder_text = models.CharField(max_length=200, blank=True, verbose_name="Texte d'aide")
    is_required = models.BooleanField(default=False, verbose_name="Champ obligatoire")
    field_options = models.TextField(blank=True, null=True, verbose_name="Options (pour select)")
    order = models.PositiveIntegerField(default=0, verbose_name="Ordre d'affichage")

    class Meta:
        verbose_name = "Champ de template"
        verbose_name_plural = "Champs de template"
        ordering = ['order', 'id']
        unique_together = ['template', 'field_name']

    def __str__(self):
        return f"{self.template.title} - {self.field_label}"

    def get_options_list(self):
        """Retourne les options sous forme de liste pour les champs select"""
        if self.field_options:
            try:
                return json.loads(self.field_options)
            except json.JSONDecodeError:
                return self.field_options.split('\n')
        return []


class Document(models.Model):
    """Documents créés à partir des templates"""
    template = models.ForeignKey(Template, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=200, verbose_name="Titre du document")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Créé par")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")
    is_completed = models.BooleanField(default=False, verbose_name="Document terminé")

    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.title} (basé sur {self.template.title})"


class DocumentFieldValue(models.Model):
    """Valeurs remplies pour chaque champ d'un document"""
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='field_values')
    template_field = models.ForeignKey(TemplateField, on_delete=models.CASCADE)
    value = models.TextField(verbose_name="Valeur du champ")

    class Meta:
        verbose_name = "Valeur de champ"
        verbose_name_plural = "Valeurs de champs"
        unique_together = ['document', 'template_field']

    def __str__(self):
        return f"{self.document.title} - {self.template_field.field_label}: {self.value[:50]}"


class TemplateCategory(models.Model):
    """Catégories pour organiser les templates"""
    name = models.CharField(max_length=100, unique=True, verbose_name="Nom de la catégorie")
    description = models.TextField(blank=True, verbose_name="Description")
    color = models.CharField(max_length=7, default="#007bff", verbose_name="Couleur (hex)")

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ['name']

    def __str__(self):
        return self.name


# Ajouter le champ catégorie au modèle Template
Template.add_to_class('category', models.ForeignKey(
    TemplateCategory,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    verbose_name="Catégorie"
))