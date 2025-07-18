from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect
from django.http import HttpResponse


def home_redirect(request):
    """Rediriger la racine vers la page appropriée"""
    if request.user.is_authenticated:
        return redirect('templates_app:template_list')
    else:
        return redirect('templates_app:login')  # Changé pour pointer vers notre login


def test_view(request):
    """Vue de test pour vérifier que Django fonctionne"""
    return HttpResponse("""
    <h1>Django fonctionne !</h1>
    <p>Liens de test :</p>
    <ul>
        <li><a href="/signup/">Inscription</a></li>
        <li><a href="/login/">Connexion</a></li>
        <li><a href="/admin/">Administration</a></li>
        <li><a href="/templates/">Templates</a></li>
    </ul>
    """)


urlpatterns = [
    # Administration Django
    path('admin/', admin.site.urls),

    # Vue de test
    path('test/', test_view, name='test'),

    # Page d'accueil
    path('', home_redirect, name='home'),

    # Logout (garde la vue Django intégrée)
    path('accounts/logout/', auth_views.LogoutView.as_view(
        next_page='templates_app:login'  # Redirige vers notre login après logout
    ), name='logout'),

    # URLs de l'application (incluant login et signup personnalisés)
    path('', include('templates_app.urls')),
]

# Servir les fichiers statiques en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    if settings.STATICFILES_DIRS:
        urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    else:
        urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
