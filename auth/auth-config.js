/*
 * AGRINOVA AUTH CONFIG
 *
 * Architecture prévue :
 * - Authentification backend
 * - Sessions sécurisées
 * - 2FA pour opérations sensibles
 * - Vérification nouvel appareil
 * - Rate limiting
 * - Journal de sécurité
 *
 * IMPORTANT :
 * Aucun mot de passe ou secret privé ne doit être
 * stocké dans le navigateur.
 */

const AUTH_CONFIG = {
  version: "5.0",

  session: {
    secure: true,
    httpOnly: true,
    sameSite: "Strict",
    expirationMinutes: 60
  },

  security: {
    maxLoginAttempts: 5,
    lockoutMinutes: 15,
    requireDeviceVerification: true,
    requireTwoFactorForSensitiveActions: true
  },

  profile: {
    progressiveVerification: true
  }
};

window.AGRINOVA_AUTH_CONFIG = AUTH_CONFIG;
