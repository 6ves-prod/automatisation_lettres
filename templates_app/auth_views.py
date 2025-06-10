from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.urls import reverse
import logging

# Configuration du logging pour debug
logger = logging.getLogger(__name__)


@csrf_protect
@never_cache
def signup_view(request):
    """Vue d'inscription avec gestion complète des erreurs"""

    # Debug: log de la requête
    logger.info(f"Signup view called with method: {request.method}")

    # Rediriger si déjà connecté
    if request.user.is_authenticated:
        messages.info(request, 'Vous êtes déjà connecté.')
        return redirect('templates_app:template_list')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)

        # Debug: afficher les données reçues
        logger.info(f"Form data received: {request.POST}")

        if form.is_valid():
            try:
                # Créer l'utilisateur
                user = form.save()
                logger.info(f"User created successfully: {user.username}")

                # Connecter automatiquement l'utilisateur SANS authenticate()
                login(request, user)
                logger.info(f"User logged in successfully: {user.username}")

                messages.success(
                    request,
                    f'Bienvenue {user.username} ! Votre compte a été créé avec succès.'
                )

                # Redirection sécurisée
                try:
                    return redirect('templates_app:template_list')
                except:
                    # Fallback si l'URL n'existe pas
                    return redirect('/')

            except Exception as e:
                logger.error(f"Error creating user: {str(e)}")
                messages.error(request, f'Erreur lors de la création du compte : {str(e)}')

        else:
            # Log des erreurs de formulaire
            logger.warning(f"Form validation failed: {form.errors}")

            # Ajouter les erreurs aux messages
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        messages.error(request, error)
                    else:
                        messages.error(request, f'{field}: {error}')
    else:
        form = UserCreationForm()

    # Context pour le template
    context = {
        'form': form,
        'title': 'Créer un compte - DocBuilder'
    }

    return render(request, 'registration/signup.html', context)