function AgriNovaAuthUI() {

  return {

    showSecurityMessage(message) {

      console.log("🔐 AgriNova Security:", message);

    },

    logout() {

      /*
       * La véritable suppression de session
       * sera exécutée côté serveur.
       */

      console.log("🚪 Déconnexion demandée");

    }

  };

}

window.agriNovaAuthUI = AgriNovaAuthUI();
