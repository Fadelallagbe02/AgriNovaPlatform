/*
 * AGRINOVA PAYMENT MODEL
 * Centralise les appels au Payment Backend.
 */

const PaymentModel = {

    async health() {
        const response = await fetch(
            `${window.AGRINOVA_API.payment}/api/health`
        );

        return response.json();
    },

    async createPayment({
        amount,
        name = "",
        email = "",
        phone = "",
        description = "Paiement AgriNova",
        project = "AGRINOVA"
    }) {

        const response = await fetch(
            `${window.AGRINOVA_API.payment}/api/payment/create`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    amount,
                    customer: {
                        name,
                        email,
                        phone
                    },
                    description,
                    project
                })
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.error || "Erreur création paiement"
            );
        }

        return data;
    },


    async cryptoStatus() {

        const response = await fetch(
            `${window.AGRINOVA_API.payment}/api/crypto/status`
        );

        return response.json();
    },


    async createCryptoPayment({
        amount,
        token = "AGRN"
    }) {

        const response = await fetch(
            `${window.AGRINOVA_API.payment}/api/crypto/payment/create`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    amount,
                    token
                })
            }
        );

        return response.json();
    },


    async verifyCryptoPayment(transactionHash) {

        const response = await fetch(
            `${window.AGRINOVA_API.payment}/api/crypto/payment/verify`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    transaction_hash: transactionHash
                })
            }
        );

        return response.json();
    }
};

window.PaymentModel = PaymentModel;

console.log("✅ AgriNova PaymentModel chargé");
