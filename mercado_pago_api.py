import mercadopago
import datetime
from config import TOKEN_MERCADOPAGO

sdk = mercadopago.SDK(TOKEN_MERCADOPAGO)

def create_payment_preference(amount, description):
    try:
        preference_data = {
            "items": [{
                "title": description,
                "quantity": 1,
                "unit_price": amount
            }],
            "payer": {
                "email": 'email@example.com'
            },
            "expires": True,
            "expiration_date_to": (datetime.datetime.now() + datetime.timedelta(minutes=10)).strftime("%Y-%m-%dT%H:%M:%S.000-03:00")
        }
        preference = sdk.preference().create(preference_data)
        return preference['response'] if 'response' in preference else None
    except Exception as e:
        print(f"Erro ao criar preferência de pagamento: {e}")
        return None

def create_pix_payment(amount, description):
    try:
        payment_data = {
            "transaction_amount": amount,
            "description": description,
            "payment_method_id": "pix",
            "payer": {
                "email": 'email@example.com'
            },
            "date_of_expiration": (datetime.datetime.now() + datetime.timedelta(minutes=10)).strftime("%Y-%m-%dT%H:%M:%S.000-03:00")
        }
        payment = sdk.payment().create(payment_data)
        return payment['response'] if 'response' in payment else None
    except Exception as e:
        print(f"Erro ao criar pagamento Pix: {e}")
        return None

def get_payment_status(payment_id):
    try:
        result = sdk.payment().get(payment_id)
        return result['response'] if 'response' in result else None
    except Exception as e:
        print(f"Erro ao verificar pagamento: {e}")
        return None