import time
from datetime import datetime, timedelta
import logging
from config import GROUP_ID, user_plans, PLANS,NOTIFICATION_IDS,PLANS_DOWNSELL
import json

def generate_group_link(bot_gestao, chat_id):
    """
    Gera um link dinâmico do grupo VIP utilizando o bot de gestão
    e adiciona as informações do usuário ao arquivo JSON
    """
    try:
        # Define o tempo de expiração do link (1 hora)
        expire_time = timedelta(minutes=10)  # Tempo de expiração do link
        invite_link = bot_gestao.create_chat_invite_link(
            chat_id=GROUP_ID,
            member_limit=1  # Um único uso
        )
        logging.info(f"Link gerado com sucesso: {invite_link.invite_link}")

        # Obter o plano selecionado pelo usuário
        selected_plan = user_plans.get(chat_id)
        if not selected_plan:
            bot_gestao.send_message(chat_id, "⚠️ Não foi possível identificar o plano selecionado. Entre em contato com o suporte.")
            return None

        # Obter a duração e o valor do plano a partir do dicionário PLANS
        plan_info = PLANS.get(selected_plan)
        if not plan_info:
            bot_gestao.send_message(chat_id, "⚠️ Não foi possível identificar as informações do plano. Entre em contato com o suporte.")
            return None

        plan_value = plan_info[0]  # O valor do plano
        plan_duration = plan_info[2]  # A duração do plano em dias
        expiry_date = datetime.now() + timedelta(days=plan_duration)

        # Armazena as informações no arquivo JSON
        user_data = {
            "chat_id": chat_id,
            "plan": selected_plan,
            "expiry_date": expiry_date.strftime("%Y-%m-%d"),
            "acquisition_date": datetime.now().strftime("%Y-%m-%d"),
            "plan_value": plan_value
        }

        file_path = 'users.json'

        try:
            # Tenta abrir o arquivo JSON para leitura
            with open(file_path, "r") as file:
                data = json.load(file)  # Lê os dados existentes
        except (FileNotFoundError, json.JSONDecodeError):
            # Se o arquivo não existir ou estiver vazio/corrompido, cria uma lista vazia
            data = []

        # Adiciona o novo usuário à lista
        data = [user for user in data if user['chat_id'] != chat_id]  # Remove duplicatas
        data.append(user_data)

        # Salva os dados atualizados no arquivo JSON
        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)

        logging.info(f"Novo usuário adicionado ao grupo VIP - ID: {chat_id}, Plano: {selected_plan}, Expira em: {expiry_date.strftime('%Y-%m-%d')}")

        # Envia uma mensagem com as informações ao administrador ou ao próprio usuário
        notification_message = (
            f"🎉 *Novo usuário adicionado ao grupo VIP!*\n\n"
            f"📊 **Detalhes da Transação:**\n"
            f"👤 **ID do Usuário:** {chat_id}\n"
            f"💳 **Plano Selecionado:** {selected_plan}\n"
            f"💵 **Valor do Plano:** R${plan_value:.2f}\n"
            f"📅 **Data de Aquisição:** {user_data['acquisition_date']}\n"
            f"⏳ **Data de Expiração:** {expiry_date.strftime('%Y-%m-%d')}"
        )

        # Envia a mensagem para o administrador (ou você pode enviar para o próprio usuário, se preferir)
        for admin_id in NOTIFICATION_IDS:
            try:
                bot_gestao.send_message(
                    admin_id,
                    notification_message,
                    parse_mode="Markdown"
                )
            except Exception as e:
                logging.error(f"Erro ao notificar o administrador {admin_id}: {e}")

        # Retorna o link gerado
        return invite_link.invite_link

    except Exception as e:
        logging.error(f"Erro ao gerar o link do grupo: {e}")
        bot_gestao.send_message(chat_id, "⚠️ Ocorreu um erro ao gerar o link de acesso. Por favor, tente novamente mais tarde.")
        return None

    

def generate_group_link_donwsell(bot_gestao, chat_id):
    """
    Gera um link dinâmico do grupo VIP utilizando o bot de gestão
    e adiciona as informações do usuário ao arquivo JSON
    """
    try:
        # Define o tempo de expiração do link (1 hora)
        expire_time = timedelta(minutes=10)  # Tempo de expiração do link
        invite_link = bot_gestao.create_chat_invite_link(
            chat_id=GROUP_ID,
            member_limit=1  # Um único uso
        )
        logging.info(f"Link gerado com sucesso: {invite_link.invite_link}")

        # Obter o plano selecionado pelo usuário
        selected_plan = user_plans.get(chat_id)
        if not selected_plan:
            bot_gestao.send_message(chat_id, "⚠️ Não foi possível identificar o plano selecionado. Entre em contato com o suporte.")
            return None

        # Obter a duração e o valor do plano a partir do dicionário PLANS
        plan_info = PLANS_DOWNSELL.get(selected_plan)
        if not plan_info:
            bot_gestao.send_message(chat_id, "⚠️ Não foi possível identificar as informações do plano. Entre em contato com o suporte.")
            return None

        plan_value = plan_info[0]  # O valor do plano
        plan_duration = plan_info[2]  # A duração do plano em dias
        expiry_date = datetime.now() + timedelta(days=plan_duration)

        # Armazena as informações no arquivo JSON
        user_data = {
            "chat_id": chat_id,
            "plan": selected_plan,
            "expiry_date": expiry_date.strftime("%Y-%m-%d"),
            "acquisition_date": datetime.now().strftime("%Y-%m-%d"),
            "plan_value": plan_value
        }

        file_path = 'users.json'

        try:
            # Tenta abrir o arquivo JSON para leitura
            with open(file_path, "r") as file:
                data = json.load(file)  # Lê os dados existentes
        except (FileNotFoundError, json.JSONDecodeError):
            # Se o arquivo não existir ou estiver vazio/corrompido, cria uma lista vazia
            data = []

        # Adiciona o novo usuário à lista
        data = [user for user in data if user['chat_id'] != chat_id]  # Remove duplicatas
        data.append(user_data)

        # Salva os dados atualizados no arquivo JSON
        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)

        logging.info(f"Novo usuário adicionado ao grupo VIP - ID: {chat_id}, Plano: {selected_plan}, Expira em: {expiry_date.strftime('%Y-%m-%d')}")

        # Envia uma mensagem com as informações ao administrador ou ao próprio usuário
        notification_message = (
            f"🎉 *Novo usuário adicionado ao grupo VIP!*\n\n"
            f"📊 **Detalhes da Transação:**\n"
            f"👤 **ID do Usuário:** {chat_id}\n"
            f"💳 **Plano Selecionado:** {selected_plan}\n"
            f"💵 **Valor do Plano:** R${plan_value:.2f}\n"
            f"📅 **Data de Aquisição:** {user_data['acquisition_date']}\n"
            f"⏳ **Data de Expiração:** {expiry_date.strftime('%Y-%m-%d')}"
        )

        # Envia a mensagem para o administrador (ou você pode enviar para o próprio usuário, se preferir)
        for admin_id in NOTIFICATION_IDS:
            try:
                bot_gestao.send_message(
                    admin_id,
                    notification_message,
                    parse_mode="Markdown"
                )
            except Exception as e:
                logging.error(f"Erro ao notificar o administrador {admin_id}: {e}")

        # Retorna o link gerado
        return invite_link.invite_link

    except Exception as e:
        logging.error(f"Erro ao gerar o link do grupo: {e}")
        bot_gestao.send_message(chat_id, "⚠️ Ocorreu um erro ao gerar o link de acesso. Por favor, tente novamente mais tarde.")
        return None

    

 
        



def send_group_link(bot_gestao, chat_id):
    """
    Envia um link dinâmico do grupo VIP para o usuário.
    Gera o link no momento do pagamento aprovado.
    """
    # ID do grupo VIP (substitua pelo ID correto do seu grupo)
    group_id = GROUP_ID  # Exemplo: substitua pelo ID real do grupo

 # Tente criar o link de convite dinâmico
    try:
        invite_link = bot_gestao.create_chat_invite_link(
            chat_id=group_id,
            expire_date=int((datetime.now() + timedelta(minutes=15)).timestamp()),  # Expira em 15 minutos
            member_limit=1  # Limita o link para um único uso (1 clique)
        )

        # Envia o link para o cliente
        bot_gestao.send_message(chat_id, f"✅ Pagamento aprovado! Clique no link abaixo para entrar no grupo VIP:\n{invite_link.invite_link}")
         # Notifica os administradores sobre a venda
        # Obter informações do plano do usuário
        selected_plan = user_plans.get(chat_id, "Desconhecido")
        plan_info = PLANS.get(selected_plan, (0, "Plano Desconhecido", 0))
        price = plan_info[0]

        # Notifica os administradores sobre a venda
        for admin_id in NOTIFICATION_IDS:
            try:
                bot_gestao.send_message(
                    admin_id,
                    f"🎉 *VENDA REALIZADA COM SUCESSO!* 🎉\n\n"
                    "📊 **Detalhes da Transação:**\n"
                    f"👤 **Usuário:** [ID {chat_id}](tg://user?id={chat_id})\n"
                    f"💵 Valor: R${price:.2f}",
                    parse_mode="Markdown"
                )
            except Exception as e:
                print(f"Erro ao notificar administrador {admin_id}: {e}")


    except Exception as e:
        bot_gestao.send_message(chat_id, "⚠️ Ocorreu um erro ao gerar o link de acesso. Por favor, tente novamente mais tarde.")
        print(f"Erro ao criar o link de convite: {e}")
        return
    
    
    # Obter o plano selecionado pelo usuário
    selected_plan = user_plans.get(chat_id)
    if not selected_plan:
        bot_gestao.send_message(chat_id, "⚠️ Não foi possível identificar o plano selecionado. Entre em contato com o suporte.")
        return

    # Obter a duração do plano a partir do dicionário PLANS
    plan_info = PLANS.get(selected_plan)
    if not plan_info:
        bot_gestao.send_message(chat_id, "⚠️ Não foi possível identificar as informações do plano. Entre em contato com o suporte.")
        return

    # Calcula a data de expiração
    plan_duration = plan_info[2]  # Terceiro elemento do dicionário PLANS deve ser a duração em dias
    expiry_date = datetime.now() + timedelta(days=plan_duration)

    # Armazena as informações no arquivo JSON
    user_data = {
        "chat_id": chat_id,
        "plan": selected_plan,
        "expiry_date": expiry_date.strftime("%Y-%m-%d")
    }

    file_path = 'users.json'
    #user_data = {"id": user_id, "plan": selected_plan}
    
    try:
        # Tenta abrir o arquivo JSON para leitura
        with open(file_path, "r") as file:
            data = json.load(file)  # Lê os dados existentes
    except (FileNotFoundError, json.JSONDecodeError):
        # Se o arquivo não existir ou estiver vazio/corrompido, cria uma lista vazia
        data = []

    # Adiciona o novo usuário à lista
    data.append(user_data)

    # Salva os dados atualizados no arquivo JSON
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)

    #print(f"Dados salvos para o usuário {user_id} no plano {selected_plan}")
    
def send_group_link_downsell(bot_gestao, chat_id):
    """
    Envia um link dinâmico do grupo VIP para o usuário.
    Gera o link no momento do pagamento aprovado.
    """
    # ID do grupo VIP (substitua pelo ID correto do seu grupo)
    group_id = GROUP_ID  # Exemplo: substitua pelo ID real do grupo

 # Tente criar o link de convite dinâmico
    try:
        invite_link = bot_gestao.create_chat_invite_link(
            chat_id=group_id,
            expire_date=int((datetime.now() + timedelta(minutes=15)).timestamp()),  # Expira em 15 minutos
            member_limit=1  # Limita o link para um único uso (1 clique)
        )

        # Envia o link para o cliente
        bot_gestao.send_message(chat_id, f"✅ Pagamento aprovado! Clique no link abaixo para entrar no grupo VIP:\n{invite_link.invite_link}")
         # Notifica os administradores sobre a venda
        # Obter informações do plano do usuário
        selected_plan = user_plans.get(chat_id, "Desconhecido")
        plan_info = PLANS_DOWNSELL.get(selected_plan, (0, "Plano Desconhecido", 0))
        price = plan_info[0]

        # Notifica os administradores sobre a venda
        for admin_id in NOTIFICATION_IDS:
            try:
                bot_gestao.send_message(
                    admin_id,
                    f"🎉 *VENDA REALIZADA COM SUCESSO!* 🎉\n\n"
                    "📊 **Detalhes da Transação:**\n"
                    f"👤 **Usuário:** [ID {chat_id}](tg://user?id={chat_id})\n"
                    f"💵 Valor: R${price:.2f}",
                    parse_mode="Markdown"
                )
            except Exception as e:
                print(f"Erro ao notificar administrador {admin_id}: {e}")


    except Exception as e:
        bot_gestao.send_message(chat_id, "⚠️ Ocorreu um erro ao gerar o link de acesso. Por favor, tente novamente mais tarde.")
        print(f"Erro ao criar o link de convite: {e}")
        return
