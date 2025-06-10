from django.contrib import admin
from .models import Template, TemplateField, Document, DocumentFieldValue, TemplateCategory

@admin.register(TemplateCategory)
class TemplateCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'color']
    search_fields = ['name']

class TemplateFieldInline(admin.TabularInline):
    model = TemplateField
    extra = 0

@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'created_by', 'is_public', 'created_at']
    list_filter = ['category', 'is_public', 'created_at']
    search_fields = ['title', 'description']
    inlines = [TemplateFieldInline]

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'template', 'created_by', 'is_completed', 'created_at']
    list_filter = ['template', 'is_completed', 'created_at']
    search_fields = ['title']