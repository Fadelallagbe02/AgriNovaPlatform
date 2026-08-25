#!/usr/bin/env python3

import os
import json
import hashlib
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs
from datetime import datetime, timezone


HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", "8093"))

PAYDUNYA_MODE = os.environ.get("PAYDUNYA_MODE", "test").lower()

PAYDUNYA_MASTER_KEY = os.environ.get("PAYDUNYA_MASTER_KEY", "")
PAYDUNYA_PRIVATE_KEY = os.environ.get("PAYDUNYA_PRIVATE_KEY", "")
PAYDUNYA_TOKEN = os.environ.get("PAYDUNYA_TOKEN", "")

# Commission AgriNova / Fadel Commerce
FEE_PERCENT = float(
    os.environ.get("AGRINOVA_FEE_PERCENT", "2")
)

FEE_MIN = float(
    os.environ.get("AGRINOVA_FEE_MIN", "0")
)

FRONTEND_URL = os.environ.get(
    "FRONTEND_URL",
    "https://fadelallagbe02.github.io/AgriNovaPlatform/"
)

PAYMENT_API_BASE = os.environ.get(
    "PAYMENT_API_BASE",
    "https://agrinova-payment.onrender.com"
)

if PAYDUNYA_MODE == "production":
    PAYDUNYA_CREATE_URL = (
        "https://app.paydunya.com/api/v1/checkout-invoice/create"
    )
else:
    PAYDUNYA_CREATE_URL = (
        "https://app.paydunya.com/sandbox-api/v1/checkout-invoice/create"
    )


def now():
    return datetime.now(timezone.utc).isoformat()


def json_response(handler, status, payload):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header(
        "Access-Control-Allow-Headers",
        "Content-Type, Authorization"
    )
    handler.send_header(
        "Access-Control-Allow-Methods",
        "GET, POST, OPTIONS"
    )
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def read_json(handler):
    length = int(handler.headers.get("Content-Length", "0"))
    raw = handler.rfile.read(length)

    if not raw:
        return {}

    try:
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return None


def paydunya_hash():
    if not PAYDUNYA_MASTER_KEY:
        return ""

    return hashlib.sha512(
        PAYDUNYA_MASTER_KEY.encode("utf-8")
    ).hexdigest()


def verify_ipn_hash(received_hash):
    expected = paydunya_hash()

    if not expected or not received_hash:
        return False

    return hashlib.sha512(
        PAYDUNYA_MASTER_KEY.encode("utf-8")
    ).hexdigest() == received_hash


def calculate_fee(amount):
    """
    Calcule la commission AgriNova.

    Exemple:
    10 000 F avec 2 % = 200 F
    Net = 9 800 F
    """

    amount = float(amount)

    fee = amount * (FEE_PERCENT / 100)

    if fee < FEE_MIN:
        fee = FEE_MIN

    net = amount - fee

    return {
        "gross_amount": round(amount, 2),
        "fee_percent": FEE_PERCENT,
        "fee_amount": round(fee, 2),
        "net_amount": round(net, 2)
    }


def paydunya_create_invoice(payload):
    if not PAYDUNYA_MASTER_KEY:
        return {
            "success": False,
            "error": "PAYDUNYA_MASTER_KEY non configurée"
        }

    if not PAYDUNYA_PRIVATE_KEY:
        return {
            "success": False,
            "error": "PAYDUNYA_PRIVATE_KEY non configurée"
        }

    if not PAYDUNYA_TOKEN:
        return {
            "success": False,
            "error": "PAYDUNYA_TOKEN non configuré"
        }

    headers = {
        "Content-Type": "application/json",
        "PAYDUNYA-MASTER-KEY": PAYDUNYA_MASTER_KEY,
        "PAYDUNYA-PRIVATE-KEY": PAYDUNYA_PRIVATE_KEY,
        "PAYDUNYA-TOKEN": PAYDUNYA_TOKEN,
    }

    request = urllib.request.Request(
        PAYDUNYA_CREATE_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST"
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read().decode("utf-8")

            try:
                return json.loads(raw)
            except Exception:
                return {
                    "success": False,
                    "error": "Réponse PayDunya non JSON",
                    "raw": raw
                }

    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")

        return {
            "success": False,
            "error": "Erreur HTTP PayDunya",
            "status": e.code,
            "raw": raw
        }

    except Exception as e:
        return {
            "success": False,
            "error": "Impossible de contacter PayDunya",
            "detail": str(e)
        }


class PaymentAPI(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        print("[PAYMENT]", fmt % args)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type, Authorization"
        )
        self.send_header(
            "Access-Control-Allow-Methods",
            "GET, POST, OPTIONS"
        )
        self.end_headers()

    def do_GET(self):

        if self.path == "/api/health":
            return json_response(
                self,
                200,
                {
                    "status": "ok",
                    "service": "AgriNova Payment API",
                    "version": "1.0.0",
                    "paydunya_mode": PAYDUNYA_MODE,
                    "smart_contract": "prepared",
                    "time": now()
                }
            )

        if self.path == "/api/crypto/status":
            return json_response(
                self,
                200,
                {
                    "success": True,
                    "blockchain": "BNB Smart Chain",
                    "token": "AGRN",
                    "status": "interface_prepared",
                    "message": (
                        "Le smart contract sera connecté "
                        "après déploiement et configuration "
                        "de son adresse."
                    )
                }
            )

        return json_response(
            self,
            404,
            {"error": "Route inconnue"}
        )

    def do_POST(self):

        # -------------------------------------------------
        # PAYDUNYA IPN
        # -------------------------------------------------

        if self.path == "/api/paydunya/ipn":

            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length)

            try:
                form = parse_qs(
                    raw.decode("utf-8"),
                    keep_blank_values=True
                )

                raw_data = form.get("data", [""])[0]

                if isinstance(raw_data, str):
                    try:
                        data = json.loads(raw_data)
                    except Exception:
                        data = {}
                else:
                    data = raw_data

                if not isinstance(data, dict):
                    return json_response(
                        self,
                        400,
                        {"success": False, "error": "IPN data invalide"}
                    )

                received_hash = str(
                    data.get("hash", "")
                ).strip()

                if not verify_ipn_hash(received_hash):
                    print("⚠️ IPN PayDunya: HASH INVALIDE")

                    return json_response(
                        self,
                        403,
                        {
                            "success": False,
                            "error": "Signature IPN invalide"
                        }
                    )

                status = str(
                    data.get("status", "")
                ).strip().lower()

                invoice = data.get("invoice", {}) or {}

                amount = invoice.get(
                    "total_amount"
                )

                print("========================================")
                print("💳 PAYDUNYA IPN")
                print("========================================")
                print("Status :", status)
                print("Amount :", amount)
                print("Customer:", data.get("customer"))
                print("========================================")

                # Ici viendra l'écriture dans la base de données
                # après création du système de transactions AgriNova.

                if status == "completed":
                    transaction_status = "SUCCESS"
                elif status == "cancelled":
                    transaction_status = "CANCELLED"
                elif status == "failed":
                    transaction_status = "FAILED"
                else:
                    transaction_status = status.upper() or "UNKNOWN"

                return json_response(
                    self,
                    200,
                    {
                        "success": True,
                        "transaction_status": transaction_status
                    }
                )

            except Exception as e:

                print("❌ IPN ERROR:", str(e))

                return json_response(
                    self,
                    500,
                    {
                        "success": False,
                        "error": "Erreur traitement IPN",
                        "detail": str(e)
                    }
                )

        # -------------------------------------------------
        # CREATION PAIEMENT PAYDUNYA
        # -------------------------------------------------

        if self.path == "/api/payment/create":

            data = read_json(self)

            if data is None:
                return json_response(
                    self,
                    400,
                    {"error": "JSON invalide"}
                )

            try:
                amount = int(data.get("amount", 0))
            except Exception:
                amount = 0

            if amount <= 0:
                return json_response(
                    self,
                    400,
                    {"error": "Montant invalide"}
                )

            customer = data.get("customer", {}) or {}

            name = str(
                customer.get("name", "")
            ).strip()

            email = str(
                customer.get("email", "")
            ).strip()

            phone = str(
                customer.get("phone", "")
            ).strip()

            description = str(
                data.get(
                    "description",
                    "Paiement AgriNova"
                )
            ).strip()

            project = str(
                data.get(
                    "project",
                    "AGRINOVA"
                )
            ).strip()

            commission = calculate_fee(amount)

            print("========================================")
            print("💰 AGRINOVA TRANSACTION")
            print("========================================")
            print("Brut        :", commission["gross_amount"], "F")
            print("Commission  :", commission["fee_amount"], "F")
            print("Taux        :", commission["fee_percent"], "%")
            print("Net         :", commission["net_amount"], "F")
            print("========================================")

            payload = {
                "invoice": {
                    "items": {
                        "item_0": {
                            "name": description,
                            "quantity": 1,
                            "unit_price": amount,
                            "total_price": amount,
                            "description": project
                        }
                    },
                    "customer": {
                        "name": name,
                        "email": email,
                        "phone": phone
                    },
                    "total_amount": amount,
                    "description": description
                },
                "store": {
                    "name": "Fadel Commerce",
                    "tagline": "AgriNova",
                    "website_url": FRONTEND_URL
                },
                "actions": {
                    "callback_url":
                        PAYMENT_API_BASE + "/api/paydunya/ipn",
                    "return_url":
                        FRONTEND_URL + "?payment=success",
                    "cancel_url":
                        FRONTEND_URL + "?payment=cancelled"
                },
                "custom_data": {
                    "project": project,
                    "source": "AGRINOVA",
                    "gross_amount": commission["gross_amount"],
                    "fee_percent": commission["fee_percent"],
                    "fee_amount": commission["fee_amount"],
                    "net_amount": commission["net_amount"],
                    "fee_owner": "Fadel Commerce"
                }
            }

            result = paydunya_create_invoice(payload)

            if isinstance(result, dict):
                result["agrinova_commission"] = commission

            return json_response(
                self,
                200,
                result
            )

        # -------------------------------------------------
        # SMART CONTRACT — PREPARATION
        # -------------------------------------------------

        if self.path == "/api/crypto/payment/create":

            data = read_json(self) or {}

            amount = data.get("amount")
            token = data.get("token", "AGRN")

            return json_response(
                self,
                501,
                {
                    "success": False,
                    "status": "not_configured",
                    "payment_type": "crypto",
                    "token": token,
                    "amount": amount,
                    "network": "BNB Smart Chain",
                    "message": (
                        "Interface préparée. "
                        "Le smart contract AGRN doit être "
                        "déployé et son adresse configurée "
                        "avant les paiements blockchain."
                    )
                }
            )

        if self.path == "/api/crypto/payment/verify":

            data = read_json(self) or {}

            return json_response(
                self,
                501,
                {
                    "success": False,
                    "status": "not_configured",
                    "transaction_hash":
                        data.get("transaction_hash"),
                    "message": (
                        "Vérification blockchain non activée "
                        "tant que le contrat AGRN n'est pas "
                        "déployé et configuré."
                    )
                }
            )

        return json_response(
            self,
            404,
            {"error": "Route inconnue"}
        )


if __name__ == "__main__":

    print("========================================")
    print("💳 AGRINOVA PAYMENT BACKEND")
    print("========================================")
    print("Port :", PORT)
    print("PayDunya :", PAYDUNYA_MODE)
    print("IPN :", PAYMENT_API_BASE + "/api/paydunya/ipn")
    print("Frontend :", FRONTEND_URL)
    print("Crypto :", "BNB Smart Chain / AGRN")
    print("========================================")

    server = ThreadingHTTPServer(
        (HOST, PORT),
        PaymentAPI
    )

    server.serve_forever()
