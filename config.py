# Configurações do bot e API
import json
import os

data_file  = 'bot_config.json'

def load_bot_token():
    try:
        # Verifica se o arquivo existe
        if os.path.exists(data_file):
            with open(data_file, "r") as f:
                config = json.load(f)
                return config.get("token", "")
        else:
            # Retorna vazio se o arquivo não existir
            return ""
    except (FileNotFoundError, json.JSONDecodeError):
        # Retorna vazio em caso de erro
        return ""

# Carrega o token do arquivo JSON
#TOKEN_BOT_CONVERSA = load_bot_token()

TOKEN_BOT_CONVERSA = '7311553740:AAGnexxnHdPSAunECbOa3aBC67u_k434kXI'
TOKEN_BOT_GESTAO = '7719880182:AAFYu9k4Dw0CZMWb-BX6Lv8azMHfD9ugLA8' 
TOKEN_MERCADOPAGO = 'APP_USR-2179435799020724-091320-904084a56a6f1be88dc5073f27d65a08-270581412'
CLIENTE_ID = 'Client_Id_fb6ae71e1705caf64079ae8e085ff132ba10f4b3'
CLIENT_SECRET = 'Client_Secret_53e430bcbc2a5d329543d40778d9205bf5df9296'
CERTIFICADO_EFI = 'producao-611378-deu certo_cert.pem'
GROUP_LINK = 'https://t.me/+4n44cVujSHthNDlh'
ID_DONO = 'SyncAdmin_bot'
GROUP_ID = -1002215259001
#GROUP_ID = -1002492656387
PUSHINPAY_TOKEN = '12135|CiUHyafyGhi0uG8gLi6MQkm3Gm660SHV5jCWlzsWed4f5b87'
PUSHINPAY_BASE_URL = 'https://api.pushinpay.com.br/api'
NOTIFICATION_IDS = [1199857681] 


welcome_image = 'welcome_image.jpg'

PLANS = {
    "VIP BRONZE": (14.90, "🔥 VIP BRONZE - 7 dias ", 7),
    "VIP PRATA": (24.90, "✨ VIP PRATA - 30 dias",   30),
    "VIP OURO": (57.90, "🏆 VIP OURO - 1 ano", 365)
}



PLANS_DOWNSELL = {
    "VIP BRONZE": (11.90, "🔥 VIP BRONZE - 7 dias ", 7),
    "VIP PRATA": (17.70, "✨ VIP PRATA - 30 dias",   30),
    "VIP OURO": (50.70, "🏆 VIP OURO - 1 ano", 365)
}


DISCOUNTS = {
    "VIP BRONZE": 0,  # 0% de desconto
    "VIP PRATA": 10,  # 10% de desconto
    "VIP OURO": 15,  # 15% de desconto
    "VIP PRO": 25,  # 25% de desconto
}



# Atualizando o dicionário de planos para renovação considerando o desconto
PLANS_RENEW = {
    f"{plan}": (
        round(price * (1 - discount / 100), 2),  # Calcula o preço com desconto
        f"{description.strip()}",    # Adiciona 'Renovação' ao texto
        duration,
    )
    for plan, (price, description, duration) in PLANS.items()
    for discount in [DISCOUNTS.get(plan, 0)]  # Obtém o desconto correspondente
}


# Escolha do Gateway de pagamento
gateway_pagamento = "pushin_pay"  # Opções: "efi", "mercado_pago" e "pushin_pay"

# Armazenamento temporário de planos e métodos de pagamento escolhidos
user_plans = {}
user_payment_methods = {}



# Dicionário para rastrear pagamentos já processados
processed_payments = set()  # Armazena os IDs dos usuários processados