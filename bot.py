import logging
import threading
import time
import json
from telebot import TeleBot, apihelper
from config import TOKEN_BOT_CONVERSA, TOKEN_BOT_GESTAO, GROUP_ID, user_plans, user_payment_methods, processed_payments
from handlers import send_welcome, callback_query_handler
from remove_users import start_daily_task

# Configuração de logs
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("bot.log", mode='a'), logging.StreamHandler()]
)

# Inicializa os bots
bot_conversa = TeleBot(TOKEN_BOT_CONVERSA)
bot_gestao = TeleBot(TOKEN_BOT_GESTAO)

# Lock para leitura/escrita segura em arquivos
file_lock = threading.Lock()

# Função para salvar dados em JSON com segurança
def save_data_safely(filename, data):
    with file_lock:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
        logging.info(f"Dados salvos com sucesso em {filename}")

# Função para carregar dados com segurança
def load_data_safely(filename):
    with file_lock:
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

# Persistência periódica dos dados em memória
def periodic_save():
    while True:
        save_data_safely("user_plans.json", user_plans)
        save_data_safely("user_payment_methods.json", user_payment_methods)
        save_data_safely("processed_payments.json", list(processed_payments))
        time.sleep(300)  # Salva a cada 5 minutos

# Thread para salvar dados periodicamente
save_thread = threading.Thread(target=periodic_save, daemon=True)
save_thread.start()

# Handlers do bot
@bot_conversa.message_handler(commands=['start', 'reiniciar'])
def welcome_message(message):
    send_welcome(bot_conversa, message)

@bot_conversa.callback_query_handler(func=lambda call: True)
def callback_query(call):
    callback_query_handler(bot_conversa, call)

@bot_conversa.message_handler(func=lambda message: True)
def handle_unknown_message(message):
    chat_id = message.chat.id
    bot_conversa.send_message(
        chat_id,
        "⚠️ Não entendi sua mensagem.\n"
        "Use o comando /start para iniciar a conversa e ver as opções disponíveis.",
        parse_mode="Markdown"
    )

# Função para polling com controle de taxa
def start_bot_polling():
    while True:
        try:
            logging.info("Iniciando o polling do bot...")
            bot_conversa.polling(none_stop=True, interval=0)
        except apihelper.ApiException as e:
            if e.error_code == 429:
                retry_after = int(e.result_json.get('retry_after', 60))
                logging.warning(f"Limite de taxa atingido. Aguardando {retry_after} segundos...")
                time.sleep(retry_after)
            else:
                logging.error(f"Erro na API do Telegram: {e}")
                time.sleep(3)
        except Exception as e:
            logging.error(f"Erro inesperado: {e}. Reiniciando em 3 segundos...")
            time.sleep(3)

# Thread para tarefas diárias
def safe_start_daily_task():
    try:
        start_daily_task(bot_gestao, GROUP_ID)
    except Exception as e:
        logging.error(f"Erro na tarefa diária: {e}")
        time.sleep(10)

# Inicia thread para tarefas diárias
daily_task_thread = threading.Thread(target=safe_start_daily_task, daemon=True)
daily_task_thread.start()

logging.info("Bot iniciado com sucesso.")

if __name__ == "__main__":
    start_bot_polling()
