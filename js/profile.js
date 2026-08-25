const AGRINOVA_PROFILE_ROLES = [
  "buyer",
  "farmer",
  "seller",
  "business",
  "supplier",
  "transporter"
];

function createProfile(data = {}) {
  return {
    id: data.id || crypto.randomUUID(),
    name: data.name || "",
    country: data.country || "",
    role: data.role || "buyer",
    online: Boolean(data.online),
    verified: Boolean(data.verified),
    reputation: Number(data.reputation || 0)
  };
}
