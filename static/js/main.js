// JavaScript principal pour DocBuilder
document.addEventListener('DOMContentLoaded', function() {
    // Initialisation des tooltips Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialisation des popovers Bootstrap
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Animation des cartes au scroll
    initScrollAnimations();

    // Initialisation des fonctionnalités communes
    initCommonFeatures();
});

// Animations au scroll
function initScrollAnimations() {
    const animateElements = document.querySelectorAll('.template-card, .card');

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    });

    animateElements.forEach(el => observer.observe(el));
}

// Fonctionnalités communes
function initCommonFeatures() {
    // Auto-dismiss des alertes après 5 secondes
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Confirmation de suppression
    const deleteButtons = document.querySelectorAll('[data-confirm-delete]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const message = this.getAttribute('data-confirm-delete') || 'Êtes-vous sûr de vouloir supprimer cet élément ?';
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });

    // Loading states pour les boutons
    const submitButtons = document.querySelectorAll('button[type="submit"], .btn-submit');
    submitButtons.forEach(button => {
        button.addEventListener('click', function() {
            if (this.form && this.form.checkValidity()) {
                showButtonLoading(this);
            }
        });
    });
}

// Afficher l'état de chargement d'un bouton
function showButtonLoading(button, text = 'Chargement...') {
    const originalText = button.innerHTML;
    button.innerHTML = `<i class="fas fa-spinner fa-spin me-2"></i>${text}`;
    button.disabled = true;

    // Restaurer après 10 secondes maximum
    setTimeout(() => {
        button.innerHTML = originalText;
        button.disabled = false;
    }, 10000);
}

// Utilitaires pour les notifications
window.showToast = function(message, type = 'info', duration = 4000) {
    const toastContainer = getOrCreateToastContainer();
    const toast = createToast(message, type);
    toastContainer.appendChild(toast);

    // Afficher le toast
    const bsToast = new bootstrap.Toast(toast, { delay: duration });
    bsToast.show();

    // Nettoyer après fermeture
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
};

function getOrCreateToastContainer() {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }
    return container;
}

function createToast(message, type) {
    const colors = {
        success: 'text-bg-success',
        error: 'text-bg-danger',
        warning: 'text-bg-warning',
        info: 'text-bg-info'
    };

    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-triangle',
        warning: 'fa-exclamation-circle',
        info: 'fa-info-circle'
    };

    const toast = document.createElement('div');
    toast.className = `toast ${colors[type] || colors.info}`;
    toast.setAttribute('role', 'alert');

    toast.innerHTML = `
        <div class="toast-body d-flex align-items-center">
            <i class="fas ${icons[type] || icons.info} me-2"></i>
            <span class="flex-grow-1">${message}</span>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
        </div>
    `;

    return toast;
}

// Utilitaire pour copier du texte
window.copyToClipboard = function(text, successMessage = 'Copié dans le presse-papiers') {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showToast(successMessage, 'success');
        }).catch(() => {
            fallbackCopyTextToClipboard(text, successMessage);
        });
    } else {
        fallbackCopyTextToClipboard(text, successMessage);
    }
};

function fallbackCopyTextToClipboard(text, successMessage) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();

    try {
        document.execCommand('copy');
        showToast(successMessage, 'success');
    } catch (err) {
        showToast('Impossible de copier le texte', 'error');
    }

    document.body.removeChild(textArea);
}

// Gestionnaire de recherche avec débounce
window.createSearchHandler = function(searchInput, callback, delay = 300) {
    let timeout;

    searchInput.addEventListener('input', function() {
        const query = this.value;

        clearTimeout(timeout);
        timeout = setTimeout(() => {
            callback(query);
        }, delay);
    });
};

// Utilitaire pour formater les dates
window.formatDate = function(date, locale = 'fr-FR') {
    if (typeof date === 'string') {
        date = new Date(date);
    }

    return date.toLocaleDateString(locale, {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
};

// Utilitaire pour formater les dates relatives
window.formatRelativeDate = function(date) {
    if (typeof date === 'string') {
        date = new Date(date);
    }

    const now = new Date();
    const diff = now - date;
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 7) {
        return formatDate(date);
    } else if (days > 0) {
        return `Il y a ${days} jour${days > 1 ? 's' : ''}`;
    } else if (hours > 0) {
        return `Il y a ${hours} heure${hours > 1 ? 's' : ''}`;
    } else if (minutes > 0) {
        return `Il y a ${minutes} minute${minutes > 1 ? 's' : ''}`;
    } else {
        return 'À l\'instant';
    }
};

// Gestionnaire d'upload de fichiers avec drag & drop
window.createFileUploader = function(dropZone, fileInput, options = {}) {
    const defaultOptions = {
        accept: '*/*',
        maxSize: 10 * 1024 * 1024, // 10MB
        multiple: false,
        onUpload: () => {},
        onError: () => {}
    };

    const config = { ...defaultOptions, ...options };

    // Drag & Drop
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    });

    dropZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');

        const files = Array.from(e.dataTransfer.files);
        handleFiles(files);
    });

    // Click to upload
    dropZone.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', (e) => {
        const files = Array.from(e.target.files);
        handleFiles(files);
    });

    function handleFiles(files) {
        if (!config.multiple) {
            files = files.slice(0, 1);
        }

        files.forEach(file => {
            if (file.size > config.maxSize) {
                config.onError(`Le fichier ${file.name} est trop volumineux.`);
                return;
            }

            config.onUpload(file);
        });
    }
};

// Gestionnaire de thème sombre/clair
window.initThemeToggle = function() {
    const themeToggle = document.getElementById('theme-toggle');
    const currentTheme = localStorage.getItem('theme') || 'light';

    document.documentElement.setAttribute('data-theme', currentTheme);

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const newTheme = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);

            showToast(`Thème ${newTheme === 'dark' ? 'sombre' : 'clair'} activé`, 'info');
        });
    }
};

// Gestionnaire de confirmation modale
window.showConfirmModal = function(title, message, onConfirm, onCancel = null) {
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.tabIndex = -1;

    modal.innerHTML = `
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">${title}</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <p>${message}</p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Annuler</button>
                    <button type="button" class="btn btn-primary" id="confirm-btn">Confirmer</button>
                </div>
            </div>
        </div>
    `;

    document.body.appendChild(modal);

    const bsModal = new bootstrap.Modal(modal);
    const confirmBtn = modal.querySelector('#confirm-btn');

    confirmBtn.addEventListener('click', () => {
        bsModal.hide();
        if (onConfirm) onConfirm();
    });

    modal.addEventListener('hidden.bs.modal', () => {
        modal.remove();
        if (onCancel) onCancel();
    });

    bsModal.show();
};

// Gestion des erreurs globales
window.addEventListener('error', function(e) {
    console.error('Erreur JavaScript:', e.error);
    showToast('Une erreur inattendue s\'est produite', 'error');
});

// Gestion des erreurs de réseau
window.addEventListener('online', () => {
    showToast('Connexion rétablie', 'success');
});

window.addEventListener('offline', () => {
    showToast('Connexion perdue', 'warning');
});