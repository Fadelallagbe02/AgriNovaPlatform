function AgriNovaAuthUI() {

  const API = window.AGRINOVA_API.auth;

  async function request(path, options = {}) {

    const response = await fetch(API + path, {
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {})
      },
      ...options
    });

    let data = {};

    try {
      data = await response.json();
    } catch (_) {}

    if (!response.ok) {
      throw new Error(data.error || "Erreur serveur");
    }

    return data;
  }

  return {

    async register(data) {
      return request("/api/auth/register", {
        method: "POST",
        body: JSON.stringify(data)
      });
    },

    async login(email, password) {
      return request("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({
          email,
          password
        })
      });
    },

    async me() {
      return request("/api/auth/me", {
        method: "GET"
      });
    },

    async logout() {
      return request("/api/auth/logout", {
        method: "POST",
        body: JSON.stringify({})
      });
    },

    showSecurityMessage(message) {
      console.log("🔐 AgriNova Security:", message);
    }

  };
}

window.agriNovaAuthUI = AgriNovaAuthUI();
