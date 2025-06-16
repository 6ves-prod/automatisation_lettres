// Variables globales
let detectedFieldsList = new Set();
let currentStep = 2;

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    const contentTextarea = document.getElementById('id_content');
    if (contentTextarea) {
        // Détecter les champs au chargement
        detectFields();

        // Écouter les changements
        contentTextarea.addEventListener('input', detectFields);

        // Exemple de contenu par défaut
        if (!contentTextarea.value.trim()) {
            contentTextarea.value = `CONTRAT DE TRAVAIL À DURÉE INDÉTERMINÉE

Entre l'entreprise {{nom_entreprise}}, située à {{adresse_entreprise}}, 
représentée par {{nom_representant}}, en qualité de {{fonction_representant}},

Et {{prenom_employe}} {{nom_employe}}, né(e) le {{date_naissance}} à {{lieu_naissance}}, 
demeurant {{adresse_employe}}, ci-après dénommé(e) « le salarié ».

ARTICLE 1 - ENGAGEMENT
L'entreprise engage le salarié en qualité de {{poste}} à compter du {{date_debut}}.

ARTICLE 2 - RÉMUNÉRATION  
Le salaire mensuel brut s'élève à {{salaire}} euros, soit {{salaire_net}} euros nets.

ARTICLE 3 - PÉRIODE D'ESSAI
Une période d'essai de {{duree_essai}} est prévue.

Fait à {{lieu_signature}}, le {{date_signature}}

Signature de l'employeur          Signature du salarié
_____________________            _____________________`;
            detectFields();
        }

        updateStepIndicator();
    }

    // Auto-sauvegarde toutes les 30 secondes
    setInterval(autoSave, 30000);
});

// Fonction de détection des champs
function detectFields() {
    const contentTextarea = document.getElementById('id_content');
    if (!contentTextarea) return;

    const content = contentTextarea.value;
    const fieldRegex = /\{\{([^}]+)\}\}/g;
    const fields = new Set();
    let match;

    while ((match = fieldRegex.exec(content)) !== null) {
        const fieldName = match[1].trim();
        if (fieldName && !fieldName.includes(' ')) {
            fields.add(fieldName);
        }
    }

    detectedFieldsList = fields;
    updateFieldsDisplay();
    updateCounters();
    updatePreview();
}

// Mise à jour de l'affichage des champs
function updateFieldsDisplay() {
    const container = document.getElementById('detectedFields');
    if (!container) return;

    const fieldArray = Array.from(detectedFieldsList);

    if (fieldArray.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted py-4">
                <i class="fas fa-search fa-2x mb-3"></i>
                <p>Aucun champ détecté</p>
                <small>Tapez {{nom_champ}} dans le texte</small>
            </div>
        `;
        return;
    }

    let html = '';
    const displayLimit = 6;

    fieldArray.slice(0, displayLimit).forEach(field => {
        const isRequired = isFieldRequired(field);
        const fieldLabel = generateFieldLabel(field);

        html += `
            <div class="detected-field">
                <div>
                    <strong>${field}</strong>
                    <br><small class="text-muted">${fieldLabel}</small>
                </div>
                <span class="badge ${isRequired ? 'bg-danger' : 'bg-warning'}">
                    ${isRequired ? 'Requis' : 'Optionnel'}
                </span>
            </div>
        `;
    });

    if (fieldArray.length > displayLimit) {
        html += `
            <small class="text-muted d-block mt-2">
                <i class="fas fa-info-circle"></i> +${fieldArray.length - displayLimit} autres champs... 
                <a href="#" onclick="showAllFields()">Voir tous</a>
            </small>
        `;
    }

    container.innerHTML = html;
}

// Générer un label lisible pour un champ
function generateFieldLabel(fieldName) {
    const labels = {
        'nom_entreprise': 'Nom de l\'entreprise',
        'adresse_entreprise': 'Adresse complète',
        'nom_representant': 'Nom du représentant',
        'prenom_employe': 'Prénom de l\'employé',
        'nom_employe': 'Nom de l\'employé',
        'poste': 'Poste occupé',
        'salaire': 'Salaire brut (€)',
        'salaire_net': 'Salaire net (€)',
        'date_debut': 'Date de début',
        'date_naissance': 'Date de naissance',
        'lieu_naissance': 'Lieu de naissance',
        'adresse_employe': 'Adresse de l\'employé',
        'duree_essai': 'Durée période d\'essai',
        'lieu_signature': 'Lieu de signature',
        'date_signature': 'Date de signature',
        'fonction_representant': 'Fonction du représentant',
        'nom_client': 'Nom du client',
        'date_aujourd_hui': 'Date d\'aujourd\'hui',
        'montant_total': 'Montant total',
        'adresse_complete': 'Adresse complète',
        'numero_reference': 'Numéro de référence',
        'email': 'Adresse email'
    };

    return labels[fieldName] || fieldName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

// Déterminer si un champ est requis
function isFieldRequired(fieldName) {
    const requiredFields = [
        'nom_entreprise', 'nom_representant', 'prenom_employe',
        'nom_employe', 'poste', 'salaire', 'date_debut',
        'nom_client', 'montant_total'
    ];
    return requiredFields.includes(fieldName);
}

// Mise à jour des compteurs
function updateCounters() {
    const contentTextarea = document.getElementById('id_content');
    if (!contentTextarea) return;

    const content = contentTextarea.value;
    const charCount = content.length;
    const fieldCount = detectedFieldsList.size;

    const charCountEl = document.getElementById('charCount');
    const fieldCountEl = document.getElementById('fieldCount');
    const fieldCountBadge = document.getElementById('fieldCountBadge');

    if (charCountEl) charCountEl.textContent = charCount;
    if (fieldCountEl) fieldCountEl.textContent = fieldCount;
    if (fieldCountBadge) fieldCountBadge.textContent = fieldCount;
}

// Insertion d'un champ à la position du curseur
function insertField(fieldText) {
    const textarea = document.getElementById('id_content');
    if (!textarea) return;

    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;

    const textBefore = textarea.value.substring(0, start);
    const textAfter = textarea.value.substring(end);

    textarea.value = textBefore + fieldText + textAfter;
    textarea.focus();
    textarea.setSelectionRange(start + fieldText.length, start + fieldText.length);

    detectFields();
}

// Insertion de templates prédéfinis
function insertTemplate(type) {
    const templates = {
        'header': `

{{ville}}, le {{date}}

{{nom_entreprise}}
{{adresse_entreprise}}
{{telephone}} - {{email}}

`,
        'article': `

ARTICLE {{numero_article}} - {{titre_article}}
{{contenu_article}}

`,
        'signature': `

Fait à {{lieu_signature}}, le {{date_signature}}

Signature de l'employeur          Signature du salarié
_____________________            _____________________

`,
        'date': `{{ville}}, le {{date}}

`,
        'table': `

| Désignation | Quantité | Prix unitaire | Total |
|-------------|----------|---------------|-------|
| {{produit_1}} | {{qte_1}} | {{prix_1}} € | {{total_1}} € |
| {{produit_2}} | {{qte_2}} | {{prix_2}} € | {{total_2}} € |

**TOTAL:** {{montant_total}} €

`,
        'conditions': `

CONDITIONS GÉNÉRALES:
- {{condition_1}}
- {{condition_2}}
- {{condition_3}}

`
    };

    if (templates[type]) {
        insertField(templates[type]);
    }
}

// Formatage du texte sélectionné
function formatText(action) {
    const textarea = document.getElementById('id_content');
    if (!textarea) return;

    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selectedText = textarea.value.substring(start, end);

    if (!selectedText) {
        showNotification('Veuillez sélectionner du texte à formater', 'warning');
        return;
    }

    let formattedText = '';

    switch(action) {
        case 'bold':
            formattedText = `**${selectedText}**`;
            break;
        case 'italic':
            formattedText = `*${selectedText}*`;
            break;
        case 'underline':
            formattedText = `_${selectedText}_`;
            break;
        case 'center':
            formattedText = `[CENTER]${selectedText}[/CENTER]`;
            break;
        case 'justify':
            formattedText = `[JUSTIFY]${selectedText}[/JUSTIFY]`;
            break;
    }

    const textBefore = textarea.value.substring(0, start);
    const textAfter = textarea.value.substring(end);
    textarea.value = textBefore + formattedText + textAfter;

    textarea.focus();
    textarea.setSelectionRange(start, start + formattedText.length);

    showNotification('Formatage appliqué', 'success');
    detectFields();
}

// Insertion rapide d'un champ personnalisé
function insertQuickField() {
    const fieldName = prompt('Nom du champ (sans espaces, ex: nom_client):');
    if (fieldName) {
        if (fieldName.match(/^[a-zA-Z_][a-zA-Z0-9_]*$/)) {
            insertField(`{{${fieldName}}}`);
        } else {
            showNotification('Le nom du champ doit contenir uniquement des lettres, chiffres et underscores', 'error');
        }
    }
}

// Affichage de l'aperçu
function showPreview() {
    updatePreview();
    const modal = new bootstrap.Modal(document.getElementById('previewModal'));
    modal.show();
}

// Mise à jour de l'aperçu en temps réel
function updatePreview() {
    const contentTextarea = document.getElementById('id_content');
    const preview = document.getElementById('livePreview');

    if (!contentTextarea || !preview) return;

    const content = contentTextarea.value;
    let previewContent = content;

    if (!content.trim()) {
        preview.innerHTML = `
            <div class="text-center text-muted py-5">
                <i class="fas fa-file-alt fa-3x mb-3"></i>
                <p>L'aperçu apparaîtra ici...</p>
                <small>Commencez à taper du contenu dans l'éditeur</small>
            </div>
        `;
        return;
    }

    // Remplacer les champs par des highlights
    detectedFieldsList.forEach(field => {
        const regex = new RegExp(`\\{\\{${field}\\}\\}`, 'g');
        previewContent = previewContent.replace(regex, `<span class="field-highlight">{{${field}}}</span>`);
    });

    // Appliquer le formatage
    previewContent = previewContent
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/_(.*?)_/g, '<u>$1</u>')
        .replace(/\[CENTER\](.*?)\[\/CENTER\]/g, '<div style="text-align: center;">$1</div>')
        .replace(/\[JUSTIFY\](.*?)\[\/JUSTIFY\]/g, '<div style="text-align: justify;">$1</div>')
        .replace(/\n/g, '<br>');

    preview.innerHTML = previewContent;
}

// Auto-formatage du contenu
function autoFormat() {
    const textarea = document.getElementById('id_content');
    if (!textarea) return;

    let content = textarea.value;

    // Correction des espaces multiples
    content = content.replace(/\s+/g, ' ');
    // Correction des retours à la ligne multiples
    content = content.replace(/\n{3,}/g, '\n\n');
    // Capitalisation après les points
    content = content.replace(/\.\s+([a-z])/g, function(match, p1) {
        return '. ' + p1.toUpperCase();
    });

    textarea.value = content;
    detectFields();
    showNotification('Auto-formatage appliqué', 'success');
}

// Vider le contenu
function clearContent() {
    if (confirm('Êtes-vous sûr de vouloir vider tout le contenu ?')) {
        const textarea = document.getElementById('id_content');
        if (textarea) {
            textarea.value = '';
            detectFields();
            showNotification('Contenu vidé', 'info');
        }
    }
}

// Afficher tous les champs
function showAllFields() {
    const fieldArray = Array.from(detectedFieldsList);
    let html = '';

    fieldArray.forEach(field => {
        const isRequired = isFieldRequired(field);
        const fieldLabel = generateFieldLabel(field);

        html += `
            <div class="detected-field">
                <div>
                    <strong>${field}</strong>
                    <br><small class="text-muted">${fieldLabel}</small>
                </div>
                <span class="badge ${isRequired ? 'bg-danger' : 'bg-warning'}">
                    ${isRequired ? 'Requis' : 'Optionnel'}
                </span>
            </div>
        `;
    });

    const container = document.getElementById('detectedFields');
    if (container) {
        container.innerHTML = html;
    }
}

// Sauvegarde du template
function saveTemplate() {
    const form = document.getElementById('templateForm');
    const titleInput = document.getElementById('id_title');
    const contentTextarea = document.getElementById('id_content');

    // Validation côté client
    if (!titleInput || !titleInput.value.trim()) {
        showNotification('Veuillez entrer un titre pour le template', 'error');
        if (titleInput) titleInput.focus();
        return;
    }

    if (!contentTextarea || !contentTextarea.value.trim()) {
        showNotification('Veuillez entrer le contenu du template', 'error');
        if (contentTextarea) contentTextarea.focus();
        return;
    }

    if (detectedFieldsList.size === 0) {
        if (!confirm('Aucun champ dynamique détecté. Continuer quand même ?')) {
            return;
        }
    }

    // Afficher l'état de chargement
    showLoadingButton();

    // Soumettre le formulaire
    if (form) {
        form.submit();
    }
}

// Continuer vers la configuration
function continueToConfiguration() {
    // Fermer le modal s'il est ouvert
    const modal = bootstrap.Modal.getInstance(document.getElementById('previewModal'));
    if (modal) modal.hide();

    // Sauvegarder d'abord
    saveTemplate();
}

// Auto-sauvegarde
function autoSave() {
    const titleInput = document.getElementById('id_title');
    const contentTextarea = document.getElementById('id_content');

    if (titleInput && contentTextarea && contentTextarea.value.trim()) {
        const draftData = {
            title: titleInput.value,
            description: document.getElementById('id_description')?.value || '',
            content: contentTextarea.value,
            category: document.getElementById('id_category')?.value || '',
            isPublic: document.getElementById('id_is_public')?.checked || false,
            timestamp: Date.now()
        };

        try {
            localStorage.setItem('template_draft', JSON.stringify(draftData));
            showNotification('Brouillon sauvegardé automatiquement', 'info', 2000);
        } catch (e) {
            console.warn('Impossible de sauvegarder le brouillon:', e);
        }
    }
}

// Charger un brouillon sauvegardé
function loadDraft() {
    try {
        const draft = localStorage.getItem('template_draft');
        if (draft) {
            const draftData = JSON.parse(draft);
            const now = Date.now();
            const draftAge = now - draftData.timestamp;

            // Si le brouillon a moins de 24h
            if (draftAge < 24 * 60 * 60 * 1000) {
                if (confirm('Un brouillon récent a été trouvé. Voulez-vous le charger ?')) {
                    document.getElementById('id_title').value = draftData.title || '';
                    document.getElementById('id_description').value = draftData.description || '';
                    document.getElementById('id_content').value = draftData.content || '';
                    if (draftData.category) document.getElementById('id_category').value = draftData.category;
                    document.getElementById('id_is_public').checked = draftData.isPublic || false;

                    detectFields();
                    showNotification('Brouillon chargé', 'success');
                }
            }
        }
    } catch (e) {
        console.warn('Impossible de charger le brouillon:', e);
    }
}

// Mise à jour de l'indicateur d'étapes
function updateStepIndicator() {
    const steps = document.querySelectorAll('.step');
    steps.forEach((step, index) => {
        step.classList.remove('active', 'completed');
        if (index + 1 < currentStep) {
            step.classList.add('completed');
        } else if (index + 1 === currentStep) {
            step.classList.add('active');
        }
    });
}

// Affichage des notifications
function showNotification(message, type = 'info', duration = 4000) {
    const colors = {
        success: '#28a745',
        error: '#dc3545',
        warning: '#ffc107',
        info: '#17a2b8'
    };

    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-triangle',
        warning: 'fa-exclamation-circle',
        info: 'fa-info-circle'
    };

    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${colors[type]};
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        z-index: 9999;
        animation: slideInRight 0.3s ease;
        max-width: 400px;
        font-weight: 500;
    `;

    notification.innerHTML = `
        <div style="display: flex; align-items: center;">
            <i class="fas ${icons[type]} me-2"></i>
            ${message}
        </div>
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => {
            if (notification.parentNode) {
                document.body.removeChild(notification);
            }
        }, 300);
    }, duration);
}


function hideLoadingButton() {
    const saveBtn = document.querySelector('button[onclick="saveTemplate()"]');
    if (saveBtn) {
        saveBtn.innerHTML = '<i class="fas fa-arrow-right"></i> Étape suivante';
        saveBtn.disabled = false;
    }
}

// Raccourcis clavier
document.addEventListener('keydown', function(e) {
    if (e.ctrlKey || e.metaKey) {
        switch(e.key) {
            case 's':
                e.preventDefault();
                saveTemplate();
                break;
            case 'b':
                e.preventDefault();
                formatText('bold');
                break;
            case 'i':
                e.preventDefault();
                formatText('italic');
                break;
            case 'p':
                e.preventDefault();
                showPreview();
                break;
        }
    }
});

// Charger le brouillon au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    // Petit délai pour s'assurer que tous les éléments sont chargés
    setTimeout(loadDraft, 500);
});

// Ajout des styles pour les animations si ils n'existent pas
if (!document.querySelector('#notification-styles')) {
    const style = document.createElement('style');
    style.id = 'notification-styles';
    style.textContent = `
        @keyframes slideInRight {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        @keyframes slideOutRight {
            from { transform: translateX(0); opacity: 1; }
            to { transform: translateX(100%); opacity: 0; }
        }
    `;
    document.head.appendChild(style);
}