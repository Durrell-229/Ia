/**
 * Système Anti-Triche pour Académie Numérique
 */
const AntiCheat = {
    violations: 0,
    maxViolations: 3,

    init() {
        this.lockFullscreen();
        this.detectTabChange();
        this.disableShortcuts();
        console.log("Système Anti-Triche initialisé.");
    },

    lockFullscreen() {
        document.addEventListener('fullscreenchange', () => {
            if (!document.fullscreenElement) {
                this.reportViolation("Sortie du mode plein écran détectée.");
            }
        });
    },

    detectTabChange() {
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.reportViolation("Changement d'onglet ou fenêtre détecté.");
            }
        });
    },

    disableShortcuts() {
        window.addEventListener('keydown', (e) => {
            // Désactiver Ctrl+C, Ctrl+V, Alt+Tab, etc.
            if (e.ctrlKey && (e.key === 'c' || e.key === 'v')) {
                e.preventDefault();
                this.reportViolation("Tentative de copier/coller détectée.");
            }
        });
        window.addEventListener('contextmenu', e => e.preventDefault());
    },

    reportViolation(message) {
        this.violations++;
        alert(`ALERTE ANTI-TRICHE (${this.violations}/${this.maxViolations}) : ${message}`);
        
        if (this.violations >= this.maxViolations) {
            alert("Exclusion automatique pour triche répétée.");
            window.location.href = "/exams/blocked/";
        }
        
        // Log to server via fetch
        fetch('/api/v1/compositions/report-cheat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ message: message, count: this.violations })
        });
    }
};
