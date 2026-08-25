const AGRINOVA_ORDER_STATUSES = [
  "draft",
  "negotiating",
  "accepted",
  "payment_pending",
  "escrow",
  "shipping",
  "delivered",
  "inspection",
  "completed",
  "dispute",
  "cancelled"
];

function validateTransaction(transaction) {
  const required = [
    "orderId",
    "buyerId",
    "sellerId",
    "productId"
  ];

  for (const field of required) {
    if (!transaction[field]) {
      return {
        valid: false,
        error: `Champ manquant: ${field}`
      };
    }
  }

  return {
    valid: true
  };
}
