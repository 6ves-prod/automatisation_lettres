# templates_app/urls.py
from django.urls import path
from . import views

app_name = 'templates_app'

urlpatterns = [
    # Page d'accueil - redirige vers la liste des templates
    path('', views.template_list, name='home'),

    # ===============================
    # URLS POUR LES TEMPLATES
    # ===============================

    # Liste et recherche de templates
    path('templates/', views.template_list, name='template_list'),

    # CRUD des templates
    path('templates/create/', views.template_create, name='template_create'),
    path('templates/<int:template_id>/', views.template_detail, name='template_detail'),
    path('templates/<int:template_id>/edit/', views.template_edit, name='template_edit'),
    path('templates/<int:template_id>/delete/', views.template_delete, name='template_delete'),

    # Gestion des champs de templates
    path('templates/<int:template_id>/fields/', views.template_edit_fields, name='template_edit_fields'),
    path('templates/<int:template_id>/fields/add/', views.template_add_field, name='template_add_field'),
    path('templates/<int:template_id>/fields/<int:field_id>/delete/', views.template_delete_field,
         name='template_delete_field'),

    # Prévisualisation et export
    path('templates/<int:template_id>/preview/', views.template_preview, name='template_preview'),
    path('templates/<int:template_id>/export/', views.template_export, name='template_export'),
    path('templates/<int:template_id>/duplicate/', views.template_duplicate, name='template_duplicate'),

    # ===============================
    # URLS POUR LES DOCUMENTS
    # ===============================

    # Liste et recherche de documents
    path('documents/', views.document_list, name='document_list'),

    # CRUD des documents
    path('documents/create/<int:template_id>/', views.document_create, name='document_create'),
    path('documents/<int:document_id>/', views.document_detail, name='document_detail'),
    path('documents/<int:document_id>/edit/', views.document_edit, name='document_edit'),
    path('documents/<int:document_id>/delete/', views.document_delete, name='document_delete'),
    path('documents/<int:document_id>/duplicate/', views.document_duplicate, name='document_duplicate'),

    # Export de documents
    path('documents/<int:document_id>/export/pdf/', views.document_export_pdf, name='document_export_pdf'),
    path('documents/<int:document_id>/export/html/', views.document_export_html, name='document_export_html'),
    path('documents/<int:document_id>/export/docx/', views.document_export_docx, name='document_export_docx'),

    # Partage de documents
    path('documents/<int:document_id>/share/', views.document_share, name='document_share'),
    path('documents/<int:document_id>/public/', views.document_public_view, name='document_public_view'),

    # ===============================
    # URLS POUR LES CATÉGORIES
    # ===============================

    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:category_id>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:category_id>/delete/', views.category_delete, name='category_delete'),
]