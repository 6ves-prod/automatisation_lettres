from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect


# Vue pour rediriger la racine vers les templates
def home_redirect(request):
    return redirect('templates_app:template_list')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_redirect, name='home_redirect'),

    # URLs d'authentification Django intégrées
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),

    # URLs de l'application principale (incluant signup)
    path('', include('templates_app.urls')),
]

# Servir les fichiers statiques et media en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[
        0] if settings.STATICFILES_DIRS else settings.STATIC_ROOT)