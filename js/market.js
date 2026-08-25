const AGRINOVA_DEMO_PRODUCTS = [
  {
    id: "demo-maize-bj-001",
    name: "Maïs",
    category: "Céréales",
    country: "🇧🇯 Bénin",
    city: "Marché local",
    seller: "Producteur vérifié",
    sellerId: "seller-demo-001",
    price: 500,
    currency: "XOF",
    unit: "kg",
    quantity: 3500,
    quality: "Grade A",
    harvest: "2026",
    status: "available",
    verifiedStock: true,
    negotiable: true,
    description:
      "Maïs destiné à la consommation et à la transformation. Stock déclaré par le vendeur et soumis aux règles de vérification AgriNova."
  },
  {
    id: "demo-cocoa-ci-001",
    name: "Cacao",
    category: "Cultures",
    country: "🇨🇮 Côte d’Ivoire",
    city: "Marché local",
    seller: "Producteur partenaire",
    sellerId: "seller-demo-002",
    price: 0,
    currency: "XOF",
    unit: "kg",
    quantity: 0,
    quality: "À confirmer",
    harvest: "2026",
    status: "unavailable",
    verifiedStock: false,
    negotiable: true,
    description:
      "Produit prévu dans le catalogue. Les transactions seront activées lorsque le stock sera disponible."
  }
];

function agrinovaGetProducts() {
  const saved = JSON.parse(
    localStorage.getItem("agrinova_products") || "[]"
  );

  return [...AGRINOVA_DEMO_PRODUCTS, ...saved];
}

function agrinovaSaveProduct(product) {
  const products = JSON.parse(
    localStorage.getItem("agrinova_products") || "[]"
  );

  products.push({
    ...product,
    id: crypto.randomUUID(),
    createdAt: new Date().toISOString()
  });

  localStorage.setItem(
    "agrinova_products",
    JSON.stringify(products)
  );
}

function agrinovaFormatPrice(price, currency) {
  if (!price || price <= 0) return "Prix à définir";
  return new Intl.NumberFormat("fr-FR").format(price) + " " + currency;
}

function agrinovaStatusLabel(status) {
  return MARKET_STATUS[status] || MARKET_STATUS.unavailable;
}
