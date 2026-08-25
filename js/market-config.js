const AGRINOVA_MARKET = {
  country: localStorage.getItem("agrinova_country") || "BJ",
  currency: localStorage.getItem("agrinova_currency") || "XOF"
};

const MARKET_STATUS = {
  available: "🟢 Disponible",
  verify: "🟡 Stock à confirmer",
  unavailable: "🔴 Indisponible",
  comingSoon: "🔒 Bientôt disponible"
};
