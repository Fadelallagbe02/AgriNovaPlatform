/*
 * Structure du journal de sécurité.
 *
 * En production, ces événements seront enregistrés
 * côté serveur et non uniquement dans le navigateur.
 */

const SECURITY_EVENT_TYPES = {

  LOGIN_SUCCESS: "login_success",
  LOGIN_FAILED: "login_failed",

  NEW_DEVICE: "new_device",

  PASSWORD_CHANGED: "password_changed",

  EMAIL_CHANGED: "email_changed",

  TWO_FACTOR_ENABLED: "two_factor_enabled",

  WALLET_CHANGED: "wallet_changed",

  SENSITIVE_ACTION: "sensitive_action"

};

window.AGRINOVA_SECURITY_EVENTS = SECURITY_EVENT_TYPES;
