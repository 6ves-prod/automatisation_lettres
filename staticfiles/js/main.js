// static/js/main.js
// Fichier JavaScript principal pour DocBuilder

// Attendre que le DOM soit chargé
document.addEventListener('DOMContentLoaded', function() {
    console.log('Main.js loaded');

    // Initialisation des composants
    initializeComponents();

    // Gestionnaires d'événements
    setupEventHandlers();

    // Animations personnalisées
    setupAnimations();
});

/**
 * Initialiser les composants Bootstrap et autres
 */
function initializeComponents() {
    // Initialiser tous les tooltips
    const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltips.forEach(tooltip => {
        new bootstrap.Tooltip(tooltip);
    });

    // Initialiser tous les popovers
    const popovers = document.querySelectorAll('[data-bs-toggle="popover"]');
    popovers.forEach(popover => {
        new bootstrap.Popover(popover);
    });

    // Initialiser les modals
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        new bootstrap.Modal(modal);
    });

    console.log('Bootstrap components initialized');
}

/**
 * Configurer les gestionnaires d'événements
 */
function setupEventHandlers() {
    // Gestionnaire pour les formulaires avec validation
    const forms = document.querySelectorAll('form[data-validate="true"]');
    forms.forEach(form => {
        form.addEventListener('submit', handleFormSubmit);
    });

    // Gestionnaire pour les boutons de suppression avec confirmation
    const deleteButtons = document.querySelectorAll('[data-action="delete"]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', handleDeleteConfirmation);
    });

    // Gestionnaire pour les messages d'alerte auto-dismiss
    setupAlertAutoDismiss();

    console.log('Event handlers set up');
}

/**
 * Configurer les animations personnalisées
 */
function setupAnimations() {
    // Animation fade-in pour les nouveaux éléments
    const fadeElements = document.querySelectorAll('.fade-in');
    fadeElements.forEach((element, index) => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(20px)';

        setTimeout(() => {
            element.style.transition = 'all 0.5s ease';
            element.style.opacity = '1';
            element.style.transform = 'translateY(0)';
        }, index * 100);
    });

    // Animation pour les cartes au survol
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
            this.style.transition = 'transform 0.3s ease';
            this.style.boxShadow = '0 4px 15px rgba(0,0,0,0.2)';
        });

        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '';
        });
    });

    console.log('Animations set up');
}

/**
 * Gérer la soumission des formulaires avec validation
 */
function handleFormSubmit(event) {
    const form = event.target;
    const submitButton = form.querySelector('button[type="submit"]');

    if (submitButton) {
        // Désactiver le bouton et afficher un spinner
        submitButton.disabled = true;
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Traitement...';

        // Réactiver le bouton après 3 secondes si nécessaire
        setTimeout(() => {
            if (submitButton.disabled) {
                submitButton.disabled = false;
                submitButton.innerHTML = submitButton.getAttribute('data-original-text') || 'Envoyer';
            }
        }, 3000);
    }
}

/**
 * Gérer les confirmations de suppression
 */
function handleDeleteConfirmation(event) {
    event.preventDefault();

    const button = event.target.closest('[data-action="delete"]');
    const itemName = button.getAttribute('data-item-name') || 'cet élément';

    if (confirm(`Êtes-vous sûr de vouloir supprimer ${itemName} ? Cette action est irréversible.`)) {
        // Si confirmation, rediriger vers l'URL de suppression
        const deleteUrl = button.getAttribute('data-delete-url') || button.href;
        if (deleteUrl) {
            window.location.href = deleteUrl;
        }
    }
}

/**
 * Configuration de l'auto-dismiss des alertes
 */
function setupAlertAutoDismiss() {
    const alerts = document.querySelectorAll('.alert[data-auto-dismiss]');

    alerts.forEach(alert => {
        const delay = parseInt(alert.getAttribute('data-auto-dismiss')) || 5000;

        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert && alert.parentNode) {
                bsAlert.close();
            }
        }, delay);
    });
}

/**
 * Fonction utilitaire pour afficher des notifications toast
 */
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container') || createToastContainer();

    const toastId = 'toast-' + Date.now();
    const toastHTML = `
        <div class="toast" id="${toastId}" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <i class="fas fa-${getToastIcon(type)} me-2 text-${type}"></i>
                <strong class="me-auto">Notification</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;

    toastContainer.insertAdjacentHTML('beforeend', toastHTML);

    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement);
    toast.show();

    // Supprimer l'élément après qu'il soit caché
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
}

/**
 * Créer le conteneur de toast s'il n'existe pas
 */
function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
    return container;
}

/**
 * Obtenir l'icône appropriée pour le type de toast
 */
function getToastIcon(type) {
    const icons = {
        'success': 'check-circle',
        'error': 'exclamation-triangle',
        'warning': 'exclamation-circle',
        'info': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

/**
 * Fonction utilitaire pour faire des requêtes AJAX
 */
function makeAjaxRequest(url, options = {}) {
    const defaultOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        }
    };

    const finalOptions = { ...defaultOptions, ...options };

    return fetch(url, finalOptions)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .catch(error => {
            console.error('AJAX request failed:', error);
            showToast('Erreur de connexion au serveur', 'error');
            throw error;
        });
}

/**
 * Fonction utilitaire pour obtenir le token CSRF
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Rendre certaines fonctions disponibles globalement
window.showToast = showToast;
window.makeAjaxRequest = makeAjaxRequest;