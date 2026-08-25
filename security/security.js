/*
 * AGRINOVA SECURITY LAYER — V5
 *
 * Cette couche ne remplace PAS le backend.
 * Elle définit les règles que le backend devra appliquer.
 */

const AgriNovaSecurity = {

  validatePassword(password) {

    if (typeof password !== "string") {
      return false;
    }

    return (
      password.length >= 8 &&
      /[A-Z]/.test(password) &&
      /[a-z]/.test(password) &&
      /[0-9]/.test(password)
    );
  },

  sanitizeText(value) {

    if (typeof value !== "string") {
      return "";
    }

    return value
      .replace(/[<>]/g, "")
      .trim();
  },

  sensitiveAction(action) {

    const protectedActions = [
      "change_password",
      "change_email",
      "change_phone",
      "change_wallet",
      "withdraw",
      "payment",
      "release_funds"
    ];

    return protectedActions.includes(action);
  }

};

window.AgriNovaSecurity = AgriNovaSecurity;
