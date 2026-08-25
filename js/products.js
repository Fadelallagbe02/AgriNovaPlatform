const AGRINOVA_PRODUCTS = [];

function addProduct(product) {
  if (!product || !product.id) {
    throw new Error("Produit invalide");
  }

  AGRINOVA_PRODUCTS.push({
    ...product,
    createdAt: product.createdAt || new Date().toISOString()
  });
}

function getProduct(id) {
  return AGRINOVA_PRODUCTS.find(p => p.id === id);
}

function getAvailableProducts() {
  return AGRINOVA_PRODUCTS.filter(
    p => p.status === "available"
  );
}
