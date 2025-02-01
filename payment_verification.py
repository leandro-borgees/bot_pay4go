import time
import logging
import threading
import queue
from config import user_plans, user_payment_methods, gateway_pagamento, processed_payments
from mercado_pago_api import get_payment_status as get_mp_payment_status
from efi_api import get_efi_payment_status
from pushinpay_api import check_pushinpay_payment_status
from group_utils import send_group_link

# Configura o logging para depuração
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# Fila para manter os pagamentos que precisam ser verificados
payment_queue = queue.Queue()

# Função que coloca o pagamento na fila para ser verificado
def enqueue_payment_verification(bot_conversa, chat_id, payment_id, payment_method):
    payment_queue.put((bot_conversa, chat_id, payment_id, payment_method))
    logging.debug(f"Pagamento enfileirado para verificação: {payment_id}")

# Função para processar a fila de pagamentos em uma thread separada
def process_payment_queue():
    while True:
        bot_conversa, chat_id, payment_id, payment_method = payment_queue.get()
        try:
            handle_payment_verification(bot_conversa, chat_id, payment_id, payment_method)
        except Exception as e:
            logging.error(f"Erro ao verificar pagamento: {e}")
        finally:
            payment_queue.task_done()  # Marca a tarefa como concluída

# Função que verifica o status do pagamento periodicamente
def handle_payment_verification(bot_conversa, chat_id, payment_id, payment_method):
    """
    Verifica o status do pagamento por 30 minutos e notifica o usuário se não for aprovado.
    """
    start_time = time.time()
    informed_pending = False  # Para rastrear se já avisamos sobre o pagamento pendente

    while time.time() - start_time < 10 * 60:  # Verifica por até 10 minutos
        if payment_id in processed_payments:
            logging.debug(f"Pagamento {payment_id} já processado. Ignorando.")
            return

        # Verifica o status do pagamento com base no gateway escolhido
        if payment_method == 'credit_card' or gateway_pagamento == "mercado_pago":
            status = get_mp_payment_status(payment_id)
            status_check = status and status.get('status') == 'approved'
        elif gateway_pagamento == "efi":
            status = get_efi_payment_status(payment_id)
            status_check = status == 'approved'
        elif gateway_pagamento == "pushin_pay":
            status_info = check_pushinpay_payment_status(payment_id)
            status_check = status_info.get('status') == 'paid'
        else:
            status_check = False

        if status_check:
            send_group_link(bot_conversa, chat_id)
            processed_payments.add(payment_id)
            return

        # Exibe a mensagem de pagamento pendente somente após o usuário clicar no bot_conversaão
        if not informed_pending:
            bot_conversa.answer_callback_query(
                f"⚠️ Pagamento ainda não identificado. Por favor, aguarde e tente novamente.",
                show_alert=False
            )
            informed_pending = True

        time.sleep(1)  # Aguarda 1 minuto antes de verificar novamente

    # Após 30 minutos sem confirmação
    bot_conversa.send_message(
        chat_id,
        "⚠️ O pagamento não foi identificado no tempo limite.\n"
        "Por favor, gere uma nova cobrança para continuar.",
        parse_mode="Markdown"
    )




# Inicia uma thread para processar a fila de pagamentos
payment_thread = threading.Thread(target=process_payment_queue, daemon=True)
payment_thread.start()