import threading
import time
from datetime import datetime
import json
import logging
from datetime import datetime, timedelta
from config import  PLANS, PLANS_RENEW, TOKEN_BOT_CONVERSA
from telebot import types
import requests
from payment_verification import enqueue_payment_verification
import os



def notify_users_about_expiration(bot_gestao):
    """
    Identifica usuários com planos prestes a expirar e notifica o bot_conversa para enviar mensagens.
    """
    try:
        # Carrega os dados do arquivo JSON
        with open('users.json', 'r') as file:
            users = json.load(file)

        today = datetime.now().date()
        warning_dates = [today + timedelta(days=5), today + timedelta(days=1)]

        for user in users:
            expiry_date = datetime.strptime(user['expiry_date'], "%Y-%m-%d").date()
            if expiry_date in warning_dates:
                # Envia os dados ao bot_conversa
                notify_bot_conversa(user)

    except Exception as e:
        logging.error(f"Erro ao verificar planos prestes a expirar: {e}")
        
        
        
def notify_bot_conversa(user):
    """
    Envia uma solicitação ao bot_conversa para notificar o usuário com botão de renovação.
    """
    url = f"https://api.telegram.org/bot{TOKEN_BOT_CONVERSA}/sendMessage"

    # Configura o botão de renovação
    chat_id = user['chat_id']
    markup = types.InlineKeyboardMarkup()
    renew_button = types.InlineKeyboardButton(
        "Renovar Agora com Desconto",
        callback_data=f"renew_{chat_id}"
    )
    markup.add(renew_button)

    data = {
        "chat_id": chat_id,
        "text": (
            f"⚠️ Sua assinatura está prestes a expirar!\n"
            "🚀 Renove agora para continuar aproveitando os benefícios exclusivos."
        ),
        "parse_mode": "Markdown",
        "reply_markup": markup.to_json()  # Converte o markup para JSON
    }

    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            logging.info(f"Notificação enviada para o usuário {chat_id}.")
        else:
            logging.error(f"Erro ao notificar o usuário {chat_id}: {response.text}")
    except Exception as e:
        logging.error(f"Erro ao enviar solicitação ao bot_conversa: {e}")

def send_renewal_notification(bot_gestao, user):
    chat_id = user['chat_id']
    plan = user['plan']
    discount = PLANS_RENEW.get(plan, 0)
    
    markup = types.InlineKeyboardMarkup()
    renew_button = types.InlineKeyboardButton(
        f"Renovar Agora com Desconto",
        callback_data=f"renew_{chat_id}"
    )
    markup.add(renew_button)
    
    bot_gestao.send_message(
        chat_id,
        f"⚠️ Atenção! Seu plano está quase expirando!\n"
        f"🚀 Renove agora com um super desconto e continue aproveitando todos os benefícios exclusivos!",
        parse_mode="Markdown",
        reply_markup=markup
    )


# Atualizar registro no JSON após a renovação
from datetime import datetime, timedelta
import json

def update_user_plan(chat_id, plan, periodicity):
    """
    Renova o plano e a data de expiração de um usuário no arquivo 'users.json'.
    
    Args:
        chat_id (int): O ID do chat do usuário no Telegram.
        plan (str): O plano escolhido pelo usuário (ex.: "VIP BRONZE", "VIP PRATA").
        periodicity (int): O número de dias que o plano será válido.
    """
    try:
        # Carrega os dados existentes do arquivo JSON
        file_path = 'users.json'
        try:
            with open(file_path, 'r') as file:
                users = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            users = []

        # Flag para indicar se o usuário foi encontrado
        user_found = False

        # Procura o usuário pelo chat_id e atualiza os dados
        for user in users:
            if user['chat_id'] == chat_id:
                # Atualiza o plano e calcula a nova data de expiração
                expiry_date = datetime.now() + timedelta(days=periodicity)
                user['plan'] = plan
                user['expiry_date'] = expiry_date.strftime("%Y-%m-%d")
                user_found = True
                break

        if not user_found:
            # Caso o usuário não exista no arquivo, cria um novo registro
            expiry_date = datetime.now() + timedelta(days=periodicity)
            new_user = {
                "chat_id": chat_id,
                "plan": plan,
                "expiry_date": expiry_date.strftime("%Y-%m-%d")
            }
            users.append(new_user)

        # Salva os dados atualizados no arquivo JSON
        with open(file_path, "w") as file:
            json.dump(users, file, indent=4)

        print(f"Plano do usuário {chat_id} atualizado/renovado para {plan}. Expira em {expiry_date.strftime('%Y-%m-%d')}.")
    except Exception as e:
        print(f"Erro ao renovar o plano do usuário: {e}")






def remove_expired_users(bot_gestao, group_id):
    """
    Remove usuários do grupo VIP cujo plano expirou,
    sem alterar o arquivo JSON.
    """
    try:
        # Carrega os dados do arquivo JSON
        with open('users.json', 'r') as file:
            users = json.load(file)

        # Data atual no formato esperado
        today = datetime.now().strftime("%Y-%m-%d")

        # Filtrar usuários com planos vencidos
        expired_users = [user for user in users if user['expiry_date'].startswith(today)]

        if expired_users:
            for user in expired_users:
                try:
                    # Remove o usuário do grupo
                    bot_gestao.kick_chat_member(group_id, user['chat_id'])
                    print(f"Usuário {user['chat_id']} removido do grupo VIP.")
                except Exception as e:
                    print(f"Erro ao remover o usuário {user['chat_id']}: {e}")
        else:
            print("Nenhum usuário com plano vencido para remover hoje.")

    except Exception as e:
        print(f"Erro ao processar a remoção de usuários: {e}")
def daily_task_scheduler(bot_gestao, group_id):
    while True:
        now = datetime.now()
        if now.hour == 1 and now.minute == 00:
            notify_users_about_expiration(bot_gestao)
            remove_expired_users(bot_gestao, group_id)
            time.sleep(60)
        else:
            time.sleep(10)


def start_daily_task(bot_gestao, group_id):
    """Inicia a tarefa de agendamento em um thread separado."""
    task_thread = threading.Thread(target=daily_task_scheduler, args=(bot_gestao, group_id))
    task_thread.daemon = True  # Torna o thread um thread daemons para encerrar automaticamente
    task_thread.start()
