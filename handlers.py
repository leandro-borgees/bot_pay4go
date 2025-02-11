from config import PLANS, user_plans, user_payment_methods, gateway_pagamento,welcome_image,PLANS_RENEW,PLANS_DOWNSELL,GROUP_ID,GROUP_LINK,TOKEN_BOT_GESTAO, NOTIFICATION_IDS
from mercado_pago_api import create_payment_preference, create_pix_payment, get_payment_status as get_mp_payment_status
from efi_api import create_efi_pix_payment, get_efi_payment_status
from pushinpay_api import create_pushinpay_pix_payment, check_pushinpay_payment_status
from payment_verification import enqueue_payment_verification
from group_utils import send_group_link,send_group_link_downsell,generate_group_link,generate_group_link_donwsell
import threading
from telebot import types
import logging
import time
from remove_users import update_user_plan
import threading
import json
from datetime import datetime, timedelta
from telebot import TeleBot
from time import sleep

bot_gestao = TeleBot(TOKEN_BOT_GESTAO)

# Arquivo JSON que armazena informações de usuários
FILE_PATH = "users.json"

# Dicionários para rastreamento de interações e mensagens enviadas
interaction_tracker = {}
downsells_sent = {}

def remove_buttons(bot_conversa, chat_id, message_id):
    """
    Remove os botões de uma mensagem específica.
    """
    try:
        bot_conversa.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=None)
        logging.info(f"Botões removidos para a mensagem {message_id} do usuário {chat_id}.")
    except Exception as e:
        logging.error(f"Erro ao remover botões para a mensagem {message_id} do usuário {chat_id}: {e}")




def is_user_in_json(chat_id):
    """
    Verifica se o usuário já está registrado no arquivo JSON.
    """
    try:
        with open(FILE_PATH, 'r') as file:
            users = json.load(file)
            return any(user['chat_id'] == chat_id for user in users)
    except (FileNotFoundError, json.JSONDecodeError):
        return False


def schedule_follow_up_message(bot_conversa, chat_id):
    """
    Agenda o envio de uma mensagem 25 minutos após a interação inicial,
    verificando se o usuário já está registrado no JSON.
    """
    interaction_time = datetime.now()
    interaction_tracker[chat_id] = interaction_time

    def send_follow_up():
        time.sleep(25 * 60)  # Aguarda 25 minutos

        # Verifica se o tempo de interação ainda corresponde ao registrado
        if interaction_tracker.get(chat_id) == interaction_time:
            # Verifica se o usuário já está no JSON
            if is_user_in_json(chat_id):
                logging.info(f"Usuário {chat_id} já está registrado no JSON. Mensagem de follow-up não enviada.")
                interaction_tracker.pop(chat_id, None)  # Remove da lista de interação
                return

            # Verifica se o downsell já foi enviado nas últimas 24 horas
            last_downsell_time = downsells_sent.get(chat_id)
            if last_downsell_time and (datetime.now() - last_downsell_time).total_seconds() < 24 * 3600:
                logging.info(f"Mensagem de downsell não enviada para {chat_id}. Já enviada nas últimas 24 horas.")
                interaction_tracker.pop(chat_id, None)  # Remove da lista de interação
                return

            # Cria o botão para reiniciar a conversa
            markup = types.InlineKeyboardMarkup()
            restart_button = types.InlineKeyboardButton(
                "🔥 Aproveitar a oferta exclusiva!",
                callback_data="restart_conversation"
            )
            markup.add(restart_button)

            # Envia a mensagem de follow-up
            try:
                bot_conversa.send_message(
                    chat_id,
                    (
                        "😉 **Olá! Percebemos que você demonstrou bastante interesse, mas ainda não concluiu sua compra.**\n\n"
                        "🎉 **Para facilitar, estamos oferecendo um DESCONTO EXCLUSIVO!**\n\n"
                        "👇 **Clique no botão abaixo e aproveite essa oportunidade agora mesmo. É rápido e super fácil!**"
                    ),
                    parse_mode="Markdown",
                    reply_markup=markup
                )
                logging.info(f"Mensagem de follow-up enviada para o usuário {chat_id}.")
            except Exception as e:
                logging.error(f"Erro ao enviar mensagem de follow-up para {chat_id}: {e}")

            # Atualiza o registro do último envio do downsell
            downsells_sent[chat_id] = datetime.now()
            interaction_tracker.pop(chat_id, None)  # Remove da lista de interação

    # Inicia uma thread para enviar a mensagem no tempo certo
    threading.Thread(target=send_follow_up, daemon=True).start()



def send_welcome(bot_conversa, message):
    chat_id = message.chat.id
    
    # Agenda o envio da mensagem de follow-up
    schedule_follow_up_message(bot_conversa, chat_id)


    
    # Envia uma imagem como mensagem de boas-vindas
    with open("welcome_image.jpg", "rb") as photo:
        bot_conversa.send_photo(
            chat_id,
            photo,
            caption=(
    "🔥 Bem-vindo ao MAIOR Grupo VIP do Telegram! 🔥\n\n"
    "🔞 EXCLUSIVO PARA OS MELHORES! 🔞\n"
    "📣 Aqui você encontra conteúdos que ninguém mais tem acesso!\n\n"
    "O QUE VOCÊ VAI ENCONTRAR AQUI:\n"
    "🔹 Onlyfans\n"
    "🔹 CloseFriends\n"
    "🔹 Privacy\n"
    "🔹 Incesto Real\n"
    "🔹 Grupos de Live\n"
    "🔹 XVideosRed\n"
    "🔹 DarkWEB\n"
    "🔹 Vazadas Exclusivas\n"
    "🔹 Tufos\n"
    "🔹 E muito mais...\n\n"
    "✨ Por que escolher nossos planos?\n"
    "✔️ Acesso TOTAL ao conteúdo VIP\n"
    "✔️ Planos com benefícios exclusivos\n"
    "✔️ Atualizações frequentes e conteúdos novos\n\n"
    "⚡ NÃO PERCA TEMPO! Garanta já o seu acesso e aproveite vantagens exclusivas!\n\n"
    "📞 Suporte VIP 24h: @Suporte_OnlyFuns\n"
)


        )
    
     # Aguardar 2 segundos antes de continuar
    time.sleep(1.9)

    # Exibe as opções de plano
    show_plan_options(bot_conversa, chat_id)



def show_plan_options(bot_conversa, chat_id):
    markup = types.InlineKeyboardMarkup()
    for key, (price, description, periodicity) in PLANS.items():
        button_text = f"{description} - R${price:.2f}"
        markup.add(types.InlineKeyboardButton(button_text, callback_data=f"plan_{key}"))

    message_text = (
    "🔥 ESCOLHA SEU PLANO VIP AGORA! 🔥\n\n"
    "🔸 🥉 VIP BRONZE\n"
    "➡️ Acesso TOTAL por 7 dias\n\n"
    "🔸 🥈 VIP PRATA\n"
    "➡️ Acesso TOTAL por 30 dias\n"
    "➡️ + Categorias Especiais\n\n"
    "🔸 🥇 VIP OURO\n"
    "✔️ O campeão de vendas!\n"
    "➡️ Todas as categorias especiais\n"
    "➡️ + Novos conteúdos exclusivos\n\n"
    "🎉 Garanta já o seu acesso e desfrute do melhor conteúdo VIP! 🎉"
)



    bot_conversa.send_message(chat_id, message_text, reply_markup=markup, parse_mode="Markdown")


def show_plan_option_discounts(bot_conversa, chat_id):
    markup = types.InlineKeyboardMarkup()
    for key, (price, description, periodicity) in PLANS_RENEW.items():
        button_text = f"{description} - R${price:.2f}"
        markup.add(types.InlineKeyboardButton(button_text, callback_data=f"discounts_{key}"))

    message_text = (
        "🔥 Nossos Planos!!! 🔥\n\n"
        "🔸 🥉 VIP BRONZE\n"
        "➡️ Acesso TOTAL por 7 dias\n\n"
        "🔸 🥈 VIP PRATA\n"
        "➡️ Acesso TOTAL por 30 dias + Categorias Especiais\n\n"
        "🔸 🥇 VIP OURO\n"
        "➡️ O campeão de vendas\n"
        "➡️ Acesso 1 ano + todas as categorias especiais + novos conteúdos\n\n"
        "🔸 💎 VIP PRO\n"
        "➡️ O mais desejado\n"
        "➡️ Tudo do VIP OURO + 10 GRUPOS EXCLUSIVOS\n\n"
        "🔒 Pagamento único, acesso permanente.\n\n"
        "📞 Suporte: @Suporte\_OnlyFuns\n"
        "🛡️ Pagamento 100% garantido via Mercado Pago (PIX/CARTÃO)"
    )

    bot_conversa.send_message(chat_id, message_text, reply_markup=markup, parse_mode="Markdown")

    


def show_plan_option_downsell(bot_conversa, chat_id):
    markup = types.InlineKeyboardMarkup()
    for key, (price, description, periodicity) in PLANS_DOWNSELL.items():
        button_text = f"{description} - R${price:.2f}"
        markup.add(types.InlineKeyboardButton(button_text, callback_data=f"downsell_{key}"))

    message_text = (
        "🔥 Nossos Planos!!! 🔥\n\n"
        "🔸 🥉 VIP BRONZE\n"
        "➡️ Acesso TOTAL por 7 dias\n\n"
        "🔸 🥈 VIP PRATA\n"
        "➡️ Acesso TOTAL por 30 dias + Categorias Especiais\n\n"
        "🔸 🥇 VIP OURO\n\n"
        "🔒 Pagamento único, acesso permanente.\n\n"
        "📞 Suporte: @Suporte\_OnlyFuns\n"
        "🛡️ Pagamento 100% garantido via Mercado Pago (PIX/CARTÃO)"
    )

    bot_conversa.send_message(chat_id, message_text, reply_markup=markup)







def show_payment_method_options(bot_conversa, chat_id):
    markup = types.InlineKeyboardMarkup()
    #markup.add(types.InlineKeyboardButton("💳 Cartão de Crédito", callback_data="payment_credit_card"))
    markup.add(types.InlineKeyboardButton("💠 Pix", callback_data="payment_pix_code"))
    #markup.add(types.InlineKeyboardButton("📷 Pix - QR Code", callback_data="payment_pix_qr"))
    bot_conversa.send_message(chat_id, "Escolha o método de pagamento:", reply_markup=markup)

def show_payment_method_options_discounts(bot_conversa, chat_id):
    markup = types.InlineKeyboardMarkup()
    #markup.add(types.InlineKeyboardButton("💳 Cartão de Crédito", callback_data="payment_credit_card_discounts"))
    markup.add(types.InlineKeyboardButton("💠 Pix", callback_data="payment_pix_code_discounts"))
    #markup.add(types.InlineKeyboardButton("📷 Pix - QR Code", callback_data="payment_pix_qr"))
    bot_conversa.send_message(chat_id, "Escolha o método de pagamento:", reply_markup=markup)
    
def show_payment_method_options_downsell(bot_conversa, chat_id):
    markup = types.InlineKeyboardMarkup()
    #markup.add(types.InlineKeyboardButton("💳 Cartão de Crédito", callback_data="payment_credit_card_downsell"))
    markup.add(types.InlineKeyboardButton("💠 Pix", callback_data="payment_pix_code_downsell"))
    #markup.add(types.InlineKeyboardButton("📷 Pix - QR Code", callback_data="payment_pix_qr"))
    bot_conversa.send_message(chat_id, "Escolha o método de pagamento:", reply_markup=markup)

def callback_query_handler(bot_conversa, call):
    
    chat_id = call.message.chat.id
    message_id = call.message.message_id  # Obtém o ID da mensagem com os bot_conversaões

       
    if call.data.startswith("renew_"):
        # Exibe as opções de planos para renovação
        show_plan_option_discounts(bot_conversa, chat_id)
        
        
    elif call.data == "restart_conversation":
        #bot_conversa.send_message(call.message.chat.id, "👋 Que bom ter você de volta! Vamos continuar sua compra?")
        show_plan_option_downsell(bot_conversa, chat_id)  # Reinicia a interação
    
    elif call.data.startswith("discounts_"):
        plan = call.data.split("_")[1]
        user_plans[chat_id] = plan
        #bot_conversa.send_message(chat_id, f"🔄 Você escolheu renovar o plano {PLANS_RENEW[plan][1]} com o valor de R${PLANS_RENEW[plan][0]:.2f}.")
        #show_payment_method_options_discounts(bot_conversa, chat_id)
        send_pix_code_discounts(bot_conversa, chat_id, plan, send_qr=False)
        #send_pix_code_discounts
        
    elif call.data.startswith("downsell_"):
        plan = call.data.split("_")[1]
        user_plans[chat_id] = plan
        #bot_conversa.send_message(chat_id, f"🔄 Você escolheu renovar o plano {PLANS_RENEW[plan][1]} com o valor de R${PLANS_RENEW[plan][0]:.2f}.")
        #show_payment_method_options_downsell(bot_conversa, chat_id)
        send_pix_code_downsell(bot_conversa, chat_id, plan, send_qr=False)

        
        
    #if call.data.startswith("restart_conversation"):
     #   plan = call.data.split("_")[1]
      #  user_plans[chat_id] = plan
       # amount, description, duration = PLANS_DOWNSELL[plan]  # Obtém os detalhes do plano
        #bot_conversa.send_message(
            #chat_id,
            #(
                #f"🎉 Parabéns pela escolha! 🎉\n\n"
                #f"💎 Plano Selecionado:\n"
                #f"🔥 {description.strip()} 🔥\n\n"
                #f"⏳ Duração: {duration} dias de acesso total\n"
                #f"💰 Valor: R${amount:.2f}\n\n"
                #f"🚀 Você está a um passo de liberar o acesso VIP mais exclusivo do Telegram!\n\n"
                #f"🎯 Escolha agora a sua forma de pagamento para continuar!"
            #),
            #parse_mode="Markdown"
       #)
        #show_payment_method_options_downsell(bot_conversa, chat_id)

    
    if call.data.startswith("plan_"):
        plan = call.data.split("_")[1]
        user_plans[chat_id] = plan
        amount, description, duration = PLANS[plan]  # Obtém os detalhes do plano
        #bot_conversa.send_message(
            #chat_id,x'
            #(
                #f"🎉 Parabéns pela escolha! 🎉\n\n"
                #f"💎 Plano Selecionado:\n"
                #f"🔥 {description.strip()} 🔥\n\n"
                #f"⏳ Duração: {duration} dias de acesso total\n"
                #f"💰 Valor: R${amount:.2f}\n\n"
                #f"🚀 Você está a um passo de liberar o acesso VIP mais exclusivo do Telegram!\n\n"
                #f"🎯 Escolha agora a sua forma de pagamento para continuar!"
            #),
            #parse_mode="Markdown"
       #)
        #show_payment_method_options(bot_conversa, chat_id)
        send_pix_code(bot_conversa, chat_id, plan, send_qr=False)

        



    elif call.data == "payment_credit_card":
        plan = user_plans.get(chat_id)
        if plan:
            user_payment_methods[chat_id] = 'credit_card'
            send_payment_link(bot_conversa, chat_id, plan)


    elif call.data == "payment_pix_code":
        plan = user_plans.get(chat_id)
        if plan:
            user_payment_methods[chat_id] = 'pix'
            send_pix_code(bot_conversa, chat_id, plan, send_qr=False)

    elif call.data == "payment_credit_card_discounts":
        plan = user_plans.get(chat_id)
        if plan:
            user_payment_methods[chat_id] = 'credit_card'
            send_payment_link_discounts(bot_conversa, chat_id, plan)


    elif call.data == "payment_pix_code_discounts":
        plan = user_plans.get(chat_id)
        if plan:
            user_payment_methods[chat_id] = 'pix'
            send_pix_code_discounts(bot_conversa, chat_id, plan, send_qr=False)

    elif call.data == "payment_credit_card_downsell":
        plan = user_plans.get(chat_id)
        if plan:
            user_payment_methods[chat_id] = 'credit_card'
            send_payment_link_downsell(bot_conversa, chat_id, plan)


    elif call.data == "payment_pix_code_downsell":
        plan = user_plans.get(chat_id)
        if plan:
            user_payment_methods[chat_id] = 'pix'
            send_pix_code_downsell(bot_conversa, chat_id, plan, send_qr=False)


    elif call.data == "payment_pix_qr":
        plan = user_plans.get(chat_id)
        if plan:
            user_payment_methods[chat_id] = 'pix'
            send_pix_code(bot_conversa, chat_id, plan, send_qr=True)


    elif call.data.startswith("verify_payment:"):
        payment_id = call.data.split(":")[1]
        if gateway_pagamento == "mercado_pago":
            status = get_mp_payment_status(payment_id)
            status_check = status.get('status') == 'approved'
        elif gateway_pagamento == "efi":
            status = get_efi_payment_status(payment_id)
            status_check = status == 'approved'
        elif gateway_pagamento == "pushin_pay":
            status_info = check_pushinpay_payment_status(payment_id)
            status_check = status_info.get('status') == 'paid'

        else:
            status_check = False

        if status_check:
            # Remove os botões da mensagem
            try:
                bot_conversa.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=None)
            except Exception as e:
                logging.error(f"Erro ao remover botões: {e}")

            # Gera o link do grupo
            link = generate_group_link(bot_gestao, chat_id)
            if link:
                bot_conversa.send_message(
                    chat_id,
                    f"✅ Pagamento aprovado! Clique no link abaixo para entrar no grupo VIP:\n{link}"
                )

            else:
                bot_conversa.send_message(
                    chat_id,
                    "⚠️ Ocorreu um erro ao gerar o link de acesso. Por favor, tente novamente mais tarde."
                )
        else:
            bot_conversa.send_message(
                chat_id,
                "⚠️ O pagamento ainda não foi identificado. Tente novamente mais tarde.",
                parse_mode="Markdown"
            )

        


    if call.data.startswith("verify_payment_discounts:"):
        payment_id = call.data.split(":")[1]
        if gateway_pagamento == "mercado_pago":
            status = get_mp_payment_status(payment_id)
            status_check = status.get('status') == 'approved'
        elif gateway_pagamento == "efi":
            status = get_efi_payment_status(payment_id)
            status_check = status == 'approved'
        elif gateway_pagamento == "pushin_pay":
            status_info = check_pushinpay_payment_status(payment_id)
            status_check = status_info.get('status') == 'paid'

        if status_check:
        # Remove os bot_conversaões após a confirmação do pagamento
            bot_conversa.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=None)

        # Atualiza o registro do usuário
        plan = user_plans.get(chat_id)
        if plan:
            amount, description, periodicity = PLANS_RENEW[plan]
            update_user_plan(chat_id, plan, periodicity)

        # Envia a confirmação de renovação para o usuário
        bot_conversa.send_message(chat_id, "✅ Seu plano foi renovado com sucesso! Aproveite mais dias de acesso VIP.", parse_mode="Markdown")

        # Envia a notificação para o administrador
        plan_info = PLANS.get(plan)
        if plan_info:
            plan_value = plan_info[0]  # O valor do plano
            plan_duration = plan_info[2]  # A duração do plano em dias
            expiry_date = datetime.now() + timedelta(days=plan_duration)

            # Coleta a data de aquisição (data atual)
            acquisition_date = datetime.now().strftime("%Y-%m-%d")

            notification_message = (
                f"🎉 *Renovação de Assinatura Realizada!* 🎉\n\n"
                f"📊 **Detalhes da Renovação:**\n"
                f"👤 **ID do Usuário:** {chat_id}\n"
                f"💳 **Plano Selecionado:** {plan}\n"
                f"💵 **Valor do Plano:** R${plan_value:.2f}\n"
                f"📅 **Data de Aquisição:** {acquisition_date}\n"
                f"⏳ **Data de Expiração:** {expiry_date.strftime('%Y-%m-%d')}"
            )

            # Envia a notificação para o administrador
            for admin_id in NOTIFICATION_IDS:
                try:
                    bot_gestao.send_message(
                        admin_id,
                        notification_message,
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logging.error(f"Erro ao notificar o administrador {admin_id}: {e}")
        
        
    if call.data.startswith("verify_payment_downsell:"):
        payment_id = call.data.split(":")[1]
        if gateway_pagamento == "mercado_pago":
            status = get_mp_payment_status(payment_id)
            status_check = status.get('status') == 'approved'
        elif gateway_pagamento == "efi":
            status = get_efi_payment_status(payment_id)
            status_check = status == 'approved'
        elif gateway_pagamento == "pushin_pay":
            status_info = check_pushinpay_payment_status(payment_id)
            status_check = status_info.get('status') == 'paid'

        else:
            status_check = False

        if status_check:
            # Remove os botões da mensagem após a confirmação do pagamento
            remove_buttons(bot_conversa, chat_id, message_id)

            # Gera o link do grupo
            link = generate_group_link_donwsell(bot_gestao, chat_id)
            if link:
                bot_conversa.send_message(
                    chat_id,
                    f"✅ Pagamento aprovado! Clique no link abaixo para entrar no grupo VIP:\n{link}"
                )
            else:
                bot_conversa.send_message(
                    chat_id,
                    "⚠️ Ocorreu um erro ao gerar o link de acesso. Por favor, tente novamente mais tarde."
                )
        else:
            bot_conversa.send_message(
                chat_id,
                "⚠️ O pagamento ainda não foi identificado.",
                parse_mode="Markdown"
            )
      




def send_payment_link(bot_conversa, chat_id, plan):
    amount, description,periodicity = PLANS[plan]
    preference = create_payment_preference(amount, description)
    if not preference:
        bot_conversa.send_message(chat_id, "⚠️ Ocorreu um erro ao gerar o pagamento. Tente novamente mais tarde.")
        return

    payment_url = preference['init_point']
    payment_id = preference['id']

    bot_conversa.send_message(chat_id, "💳 Clique no link abaixo para realizar o pagamento com cartão de crédito:")
    bot_conversa.send_message(chat_id, payment_url)

    markup = types.InlineKeyboardMarkup()
    pay_btn = types.InlineKeyboardButton("Verificar Pagamento", callback_data=f"verify_payment:{payment_id}")
    markup.add(pay_btn)

    bot_conversa.send_message(chat_id, "✅ Após efetuar o pagamento, clique no botão abaixo:", reply_markup=markup)
    enqueue_payment_verification(bot_conversa, chat_id, payment_id, 'credit_card')

def send_payment_link_discounts(bot_conversa, chat_id, plan):
    amount, description,periodicity = PLANS_RENEW[plan]
    preference = create_payment_preference(amount, description)
    if not preference:
        bot_conversa.send_message(chat_id, "⚠️ Ocorreu um erro ao gerar o pagamento. Tente novamente mais tarde.")
        return

    payment_url = preference['init_point']
    payment_id = preference['id']

    bot_conversa.send_message(chat_id, "💳 Clique no link abaixo para realizar o pagamento com cartão de crédito:")
    bot_conversa.send_message(chat_id, payment_url)

    markup = types.InlineKeyboardMarkup()
    pay_btn = types.InlineKeyboardButton("Verificar Pagamento", callback_data=f"verify_payment_discounts:{payment_id}")
    markup.add(pay_btn)

    bot_conversa.send_message(chat_id, "✅ Após efetuar o pagamento, clique no botão abaixo:", reply_markup=markup)
    
    
def send_payment_link_downsell(bot_conversa, chat_id, plan):
    amount, description,periodicity = PLANS_DOWNSELL[plan]
    preference = create_payment_preference(amount, description)
    if not preference:
        bot_conversa.send_message(chat_id, "⚠️ Ocorreu um erro ao gerar o pagamento. Tente novamente mais tarde.")
        return

    payment_url = preference['init_point']
    payment_id = preference['id']

    bot_conversa.send_message(chat_id, "💳 Clique no link abaixo para realizar o pagamento com cartão de crédito:")
    bot_conversa.send_message(chat_id, payment_url)

    markup = types.InlineKeyboardMarkup()
    pay_btn = types.InlineKeyboardButton("Verificar Pagamento", callback_data=f"verify_payment_downsell:{payment_id}")
    markup.add(pay_btn)

    bot_conversa.send_message(chat_id, "✅ Após efetuar o pagamento, clique no botão abaixo:", reply_markup=markup)

def escape_markdown(text):
    escape_chars = r'_\[\]()~>#+-=|{}.!'
    return ''.join(f'\\{char}' if char in escape_chars else char for char in text)

def send_pix_code(bot_conversa, chat_id, plan, send_qr=True):
    amount, description,periodicity = PLANS[plan]

    if gateway_pagamento == "mercado_pago":
        payment = create_pix_payment(amount, description)
        if not payment:
            bot_conversa.send_message(chat_id, "⚠️ Ocorreu um erro ao gerar o pagamento. Tente novamente mais tarde.")
            return
        pix_code = payment['point_of_interaction']['transaction_data']['qr_code']
        qr_code_url = payment['point_of_interaction']['transaction_data']['qr_code_base64']
        payment_id = payment['id']

    elif gateway_pagamento == "efi":
        payment = create_efi_pix_payment(amount, description,periodicity)
        if not payment:
            bot_conversa.send_message(chat_id, "⚠️ Ocorreu um erro ao gerar o pagamento. Tente novamente mais tarde.")
            return
        pix_code = payment['pixCopiaECola']
        qr_code_url = f"https://quickchart.io/qr?text={pix_code}"
        payment_id = payment['txid']

    elif gateway_pagamento == "pushin_pay":
        payment = create_pushinpay_pix_payment(amount)
        if not payment or "error" in payment:
            bot_conversa.send_message(chat_id, f"⚠️ Ocorreu um erro ao gerar o pagamento: {payment.get('error', 'Erro desconhecido')}")
            return
        pix_code = payment['qr_code_text']
        qr_code_url = payment['qr_code']
        payment_id = payment['id']
    
    else:
        bot_conversa.send_message(chat_id, "⚠️ Gateway de pagamento inválido.")
        return
    


    # Depois envia o código Pix com o botão para verificar pagamento
    pix_code_box = f"<pre>{pix_code}</pre>"
    bot_conversa.send_message(
        chat_id,
        (
            "🚀 Finalize seu pagamento agora!\n\n"
            f"💎 Plano Selecionado: {description.strip()}\n"
            f"💵 Valor: R${amount:.2f}\n\n"
            "💠 Aqui está seu código Pix. Copie e pague no seu banco:\n"
            f"{pix_code_box}"
        ),
        parse_mode="HTML")

    qr_code_url = f"https://quickchart.io/qr?text={pix_code}"  # URL do QR Code
    # Primeiro envia o QR Code
    bot_conversa.send_message(chat_id, "🔗 Aqui está seu QR Code. Escaneie e pague no seu banco:")
    bot_conversa.send_photo(chat_id, qr_code_url)

    markup = types.InlineKeyboardMarkup()
    pay_btn = types.InlineKeyboardButton("Verificar Pagamento", callback_data=f"verify_payment:{payment_id}")
    markup.add(pay_btn)
    bot_conversa.send_message(chat_id, "✅ Após realizar o pagamento, seu link será automaticamente disponibilizado aqui. Se pagou e o link ainda não apareceu, clique no botão Verificar Pagamento:", reply_markup=markup)    
 

    # Adiciona o botão de verificar pagamento ao final

    


        
    

        #bot_conversa.send_message(chat_id, "🔗 Aqui está seu código Pix. Copie e pague no seu banco:", parse_mode="HTML")
        #bot_conversa.send_message(chat_id, pix_code_box, parse_mode="HTML", reply_markup=markup)


    
def send_pix_code_discounts(bot_conversa, chat_id, plan, send_qr=True):
    amount, description,periodicity = PLANS_RENEW[plan]

    if gateway_pagamento == "mercado_pago":
        payment = create_pix_payment(amount, description)
        if not payment:
            bot_conversa.send_message(chat_id, "⚠️ Ocorreu um erro ao gerar o pagamento. Tente novamente mais tarde.")
            return
        pix_code = payment['point_of_interaction']['transaction_data']['qr_code']
        qr_code_url = payment['point_of_interaction']['transaction_data']['qr_code_base64']
        payment_id = payment['id']

    elif gateway_pagamento == "efi":
        payment = create_efi_pix_payment(amount, description,periodicity)
        if not payment:
            bot_conversa.send_message(chat_id, "⚠️ Ocorreu um erro ao gerar o pagamento. Tente novamente mais tarde.")
            return
        pix_code = payment['pixCopiaECola']
        qr_code_url = f"https://quickchart.io/qr?text={pix_code}"
        payment_id = payment['txid']

    elif gateway_pagamento == "pushin_pay":
        payment = create_pushinpay_pix_payment(amount)
        if not payment or "error" in payment:
            bot_conversa.send_message(chat_id, f"⚠️ Ocorreu um erro ao gerar o pagamento: {payment.get('error', 'Erro desconhecido')}")
            return
        pix_code = payment['qr_code_text']
        qr_code_url = payment['qr_code']
        payment_id = payment['id']
    
    else:
        bot_conversa.send_message(chat_id, "⚠️ Gateway de pagamento inválido.")
        return
    


    # Depois envia o código Pix com o botão para verificar pagamento
    pix_code_box = f"<pre>{pix_code}</pre>"
    bot_conversa.send_message(
        chat_id,
        (
            "🚀 Finalize seu pagamento agora!\n\n"
            f"💎 Plano Selecionado: {description.strip()}\n"
            f"💵 Valor: R${amount:.2f}\n\n"
            "💠 Aqui está seu código Pix. Copie e pague no seu banco:\n"
            f"{pix_code_box}"
        ),
        parse_mode="HTML"
    )
    
    qr_code_url = f"https://quickchart.io/qr?text={pix_code}"  # URL do QR Code

     # Primeiro envia o QR Code
    bot_conversa.send_message(chat_id, "🔗 Aqui está seu QR Code. Escaneie e pague no seu banco:")
    bot_conversa.send_photo(chat_id, qr_code_url)

    # Adiciona o botão de verificar pagamento ao final
    markup = types.InlineKeyboardMarkup()
    pay_btn = types.InlineKeyboardButton("Verificar Pagamento", callback_data=f"verify_payment_discounts:{payment_id}")
    markup.add(pay_btn)
    bot_conversa.send_message(chat_id, "✅ Após realizar o pagamento, seu link será automaticamente disponibilizado aqui. Se pagou e o link ainda não apareceu, clique no botão Verificar Pagamento:", reply_markup=markup)
 

def send_pix_code_downsell(bot_conversa, chat_id, plan, send_qr=True):
    amount, description,periodicity = PLANS_DOWNSELL[plan]

    if gateway_pagamento == "mercado_pago":
        payment = create_pix_payment(amount, description)
        if not payment:
            bot_conversa.send_message(chat_id, "⚠️ Ocorreu um erro ao gerar o pagamento. Tente novamente mais tarde.")
            return
        pix_code = payment['point_of_interaction']['transaction_data']['qr_code']
        qr_code_url = payment['point_of_interaction']['transaction_data']['qr_code_base64']
        payment_id = payment['id']

    elif gateway_pagamento == "efi":
        payment = create_efi_pix_payment(amount, description,periodicity)
        if not payment:
            bot_conversa.send_message(chat_id, "⚠️ Ocorreu um erro ao gerar o pagamento. Tente novamente mais tarde.")
            return
        pix_code = payment['pixCopiaECola']
        qr_code_url = f"https://quickchart.io/qr?text={pix_code}"
        payment_id = payment['txid']

    elif gateway_pagamento == "pushin_pay":
        payment = create_pushinpay_pix_payment(amount)
        if not payment or "error" in payment:
            bot_conversa.send_message(chat_id, f"⚠️ Ocorreu um erro ao gerar o pagamento: {payment.get('error', 'Erro desconhecido')}")
            return
        pix_code = payment['qr_code_text']
        qr_code_url = payment['qr_code']
        payment_id = payment['id']
    
    else:
        bot_conversa.send_message(chat_id, "⚠️ Gateway de pagamento inválido.")
        return
    


    # Depois envia o código Pix com o botão para verificar pagamento
    pix_code_box = f"<pre>{pix_code}</pre>"
    bot_conversa.send_message(
        chat_id,
        (
            "🚀 Finalize seu pagamento agora!\n\n"
            f"💎 Plano Selecionado: {description.strip()}\n"
            f"💵 Valor: R${amount:.2f}\n\n"
            "💠 Aqui está seu código Pix. Copie e pague no seu banco:\n"
            f"{pix_code_box}"
        ),
        parse_mode="HTML"
    )
    
    qr_code_url = f"https://quickchart.io/qr?text={pix_code}"  # URL do QR Code

     # Primeiro envia o QR Code
    bot_conversa.send_message(chat_id, "🔗 Aqui está seu QR Code. Escaneie e pague no seu banco:")
    bot_conversa.send_photo(chat_id, qr_code_url)

    # Adiciona o botão de verificar pagamento ao final
    markup = types.InlineKeyboardMarkup()
    pay_btn = types.InlineKeyboardButton("Verificar Pagamento", callback_data=f"verify_payment_downsell:{payment_id}")
    markup.add(pay_btn)
    bot_conversa.send_message(chat_id, "✅ Após realizar o pagamento, seu link será automaticamente disponibilizado aqui. Se pagou e o link ainda não apareceu, clique no botão Verificar Pagamento:", reply_markup=markup)
 
        #bot_conversa.send_message(chat_id, "🔗 Aqui está seu código Pix. Copie e pague no seu banco:", parse_mode="HTML")
        #bot_conversa.send_message(chat_id, pix_code_box, parse_mode="HTML", reply_markup=markup)

def clear_user_data(chat_id):
    user_plans.pop(chat_id, None)
    user_payment_methods.pop(chat_id, None)
    logging.debug(f"Dados temporários removidos para o chat_id: {chat_id}")
