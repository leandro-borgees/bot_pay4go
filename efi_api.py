import requests
import base64
from config import CLIENTE_ID, CLIENT_SECRET, CERTIFICADO_EFI
import logging


# Função para obter o token de acesso
def get_efi_token():
    url = "https://pix.api.efipay.com.br/oauth/token"
    autorizacao = base64.b64encode(f"{CLIENTE_ID}:{CLIENT_SECRET}".encode()).decode()
    
    headers = {
        "Authorization": f"Basic {autorizacao}",
        "Content-Type": "application/json"
    }
    
    data = {
        "grant_type": "client_credentials"
    }
    
    response = requests.post(url, json=data, headers=headers, cert=CERTIFICADO_EFI)
    if response.status_code == 200:
        return response.json().get('access_token')
    else:
        print("Erro ao obter token de acesso:", response.json())
        return None

def create_efi_pix_payment(amount, description):
    access_token = get_efi_token()
    if not access_token:
        print("Erro: Não foi possível obter o token de acesso.")
        return None
    
    url = "https://api-pix.gerencianet.com.br/v2/cob"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "calendario": {"expiracao": 3600},
        "valor": {"original": f"{amount:.2f}"},
        "chave": "46aadfb3-50d6-4fa4-ae00-e6b8813b0dbe"
    }
    
    response = requests.post(url, json=data, headers=headers, cert=CERTIFICADO_EFI)
    if response.status_code == 201:
        return response.json()
    else:
        print("Erro ao criar pagamento Pix Efí:", response.json())
        return None

def get_efi_payment_status(txid):
    access_token = get_efi_token()
    if not access_token:
        print("Erro: Não foi possível obter o token de acesso.")
        return None
    
    url = f"https://pix.api.efipay.com.br/v2/cob/{txid}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(url, headers=headers, cert=CERTIFICADO_EFI)
# Verifica se a requisição foi bem-sucedida
    if response.status_code == 200:
        resultado = response.json()
        logging.debug("Consulta realizada com sucesso. Dados completos: %s", resultado)
        
        # Captura o status da cobrança
        status = resultado.get('status')
        logging.debug("Status da cobrança capturado: %s", status)
        
        if status == "ATIVA":
            return "pending"
        elif status == "CONCLUIDA":
            return "approved"
        elif status == "REMOVIDA_PELO_USUARIO_RECEBEDOR":
            return "removed"
        elif status == "EXPIRADA":
            return "expired"
        else:
            logging.debug("Status desconhecido: %s", status)
            return "unknown"
    else:
        logging.debug("Erro ao consultar status do pagamento Pix Efí: %s", response.json())
        return None