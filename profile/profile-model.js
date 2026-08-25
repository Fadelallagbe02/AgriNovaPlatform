const AGRINOVA_PROFILE_MODEL = {

  id: null,

  identity: {
    displayName: "",
    profilePhoto: "",
    country: "",
    language: ""
  },

  account: {
    roles: [],
    verified: false,
    online: false
  },

  agricultural: {
    productsOffered: [],
    productsWanted: [],
    description: ""
  },

  reputation: {
    score: 0,
    transactions: 0,
    successfulTransactions: 0
  },

  security: {
    twoFactorEnabled: false,
    trustedDevices: [],
    lastLogin: null
  }

};

window.AGRINOVA_PROFILE_MODEL = AGRINOVA_PROFILE_MODEL;
