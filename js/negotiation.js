function createOffer({
  orderId,
  buyerId,
  sellerId,
  amount,
  currency
}) {
  if (!orderId || !buyerId || !sellerId) {
    throw new Error("Transaction incomplète");
  }

  if (!Number.isFinite(amount) || amount <= 0) {
    throw new Error("Montant invalide");
  }

  return {
    id: crypto.randomUUID(),
    orderId,
    buyerId,
    sellerId,
    amount,
    currency,
    status: "pending",
    createdAt: new Date().toISOString()
  };
}
