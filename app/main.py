from datetime import datetime as dt
import configparser as cfg
import os

import streamlit as st

import lib


remap_item = {
"refri_e_suco":"Refri e Suco",
"salgados_e_doces":"Salgados e Doces",
"cachaca":"Cachaça",
"cerveja":"Cerveja"
}


def info_page(token):
    text = lib.get_info(token)
    st.markdown(text)

# Function for the Subscription Page
def subscription_page(token):
    st.title("Inscrição")

    # Text input for name
    default_value = ''
    if 'nome' in st.session_state:
        default_value = st.session_state.nome
    nome = st.text_input("Nome:", value=default_value)

    # Checkboxes for various consumable items
    st.write("O que vai consumir:")
    cerveja = st.checkbox("Cerveja")
    cachaca = st.checkbox("Cachaça")
    salgados_doces = st.checkbox("Salgados e Doces")
    refri_suco = st.checkbox("Refri e Suco")

    vegan = st.checkbox("Dieta vegana")

    if st.button("Salvar"):
        st.session_state.nome = nome
        d = {"consumo":{"cerveja": cerveja, "cachaca": cachaca, "salgados_e_doces": salgados_doces, "refri_e_suco": refri_suco}, "vegano":vegan}
        lib.add_person(nome, d, token)
        st.success("Dados salvos com sucesso!")
        lib.system_message(f"{nome} entrou na festa!", token)
        

# Function for the Subscription Status Page
def subscription_status_page(token):
    st.title("Seus dados:")

    default_value = ''
    if 'nome' in st.session_state:
        default_value = st.session_state.nome
    nome = st.text_input("Nome cadastrado:", value=default_value)
    nome = nome.lower().strip()

    if st.button("Carregar Dados"):
        st.session_state.nome = nome
        # Fetching data using the load_person function
        r, preferences = lib.load_person(nome, token)
        consumo = preferences['consumo']
        vegan = preferences['vegano']

        if r:
            st.write(f"Consumos:")
            for item, value in consumo.items():
                #st.write(f"{item}: {'Sim' if value else 'Não'}")
                st.checkbox(item.capitalize(), value, disabled=True)
            st.write("(Edite na aba de inscrição)")
        else:
            st.warning("Nome não encontrado.")

        st.checkbox("vegano", vegan, disabled=True)

        categorias = [remap_item[v] for v,k in lib.load_person(nome, token)[1]['consumo'].items() if k]

        df = lib.get_items(token)
        df['total'] = df['preco_unit'] * df['quantidade']

        #df = df[df['categoria'].isin(categorias)]

        st.title("Contribuições:")
        own_df = df[df['responsavel']==nome]
        st.dataframe(own_df)

        st.title("Custo total das contribuições:")
        own_total_value = sum(own_df['total'])
        st.title(f"R$ {own_total_value:.2f}".replace(',','.'))

        st.title("Lista de consumíveis disponíveis:")
        available_df = df[df['categoria'].isin(categorias)]
        if vegan:
            available_df = available_df[available_df['vegano']==True]
        st.dataframe(available_df)

        st.title("Valor total da parte:")
        #available_df['total'] = available_df['preco_unit'] * available_df['quantidade']
        total_value = lib.get_amount_for_user(nome, token)
        st.title(f"R$ {total_value:.2f}".replace('.',','))

        st.title("Valor a ser pago (total - gastos):")
        st.title(f"R$ {total_value-own_total_value:.2f}")
        st.title("Pix:")
        st.image(f"parties/{token}/pix.jpeg")
        config = cfg.ConfigParser()
        config.read(f'parties/{token}/info.conf')
        pix_key = config['DEFAULT']['pix_key']

        st.write("chave pix:")
        st.write(pix_key)

# Function for the Add Items Page
def add_items_page(token):
    st.title("Adicione produtos que você vai levar:")

    default_value = ''
    if 'nome' in st.session_state:
        default_value = st.session_state.nome
    nome = st.text_input("Nome:", value=default_value)

    if st.button("Verificar"):
        r, preferences = lib.load_person(nome, token)
        if r:
            st.success("cadastro encontrado")
        else:
            st.error("cadastro não encontrado")  
    prod_name = st.text_input("Nome do produto:")
    quant = st.text_input("Quantidade: ")
    category = st.selectbox('Categoria: ', ["Cerveja", "Cachaça", "Salgados e Doces", "Refri e Suco"])
    unit_value = st.text_input("Valor unitário")
    vegan = st.checkbox("Vegano")
    if st.button("Inserir"):
        r, msg = lib.add_item(nome, prod_name, quant, category, unit_value, vegan, token)
        if not r:
            st.error(msg)
        else:
            st.success("Produto adicionado com sucesso")
            lib.system_message(f"{nome} adicionou {quant} unidade(s) do produto {prod_name}", token)

def check_items_page(token):
    df = lib.get_items(token)
    st.title("Itens da festa:")
    st.dataframe(df)
    st.title("Valor total:")
    df['total'] = df['preco_unit'] * df['quantidade']
    total_val = sum(df['total'])
    st.title(f"R$ {total_val:.2f}".replace(".",","))

def list_atendees(token):
    df = lib.list_users_detailed(token)
    st.dataframe(df)


def remove_items_page(token):
    default_value = ''
    if 'nome' in st.session_state:
        default_value = st.session_state.nome
    nome = st.text_input("Nome cadastrado:", value=default_value)

    df = lib.get_items(token)
    items = df[df['responsavel']==nome]['produto'].values
    selecao = st.selectbox("Item a ser removido:", items)
    quant = st.text_input("Quantidade:")
    df_u = df[df['responsavel']==nome]
    selected_df = df_u[df_u['produto']==selecao]
    st.dataframe(selected_df)
    if st.button("remover"):
        prod_name, units = lib.remove_product(selected_df, quant, token)
        st.success(f"Retirado {units} unidades do produto {prod_name}")
        lib.system_message(f"{nome} retirou {units} unidade(s) do produto {prod_name}", token)

def chat_page(token):
    chat = lib.load_chat(token)
    st.session_state.messages = chat
    # Always display chat history
    #if "messages" not in st.session_state:
    #    st.session_state.messages = []

    for message in st.session_state.messages:
        is_assistant = message["role"]
        reference = "**SYSTEM** @ "
        if 'user' in message:
            reference = f"**{message['user']}** @ "
        time = ''
        if 'time' in message:
            time = f"*{message['time']}*"
        with st.chat_message(message["role"]):
            st.caption(f"{reference.upper()} {time}")
            st.markdown(message["content"])

    if 'nome' in st.session_state:
        nome = st.session_state.nome
    else:
        nome = ''

    if nome:
        prompt = st.chat_input("Type your message")
        if prompt:
            lib.user_message(nome, prompt, token)
            st.experimental_rerun()
    else:
        nome = st.text_input("Nome:")
        if st.button("Verificar"):
            r, pref = lib.load_person(nome, token)
            if r:
                st.session_state.nome = nome
                valid_name = True


def main():
    available_tokens = os.listdir('parties')
    token = st.sidebar.text_input("token (veja no grupo): ")
    valid_token = token in available_tokens

    if not valid_token:
        st.sidebar.error(f"token invalido, pergunte para (98)98270-0001")
    else:
        st.sidebar.success("token válido")

    if valid_token:
        st.sidebar.title("Navegação")
        page = st.sidebar.radio("Go to", ("Info", "Inscrição", "Conta", "Adicionar Item", "Remover Item", "Lista de Convidados", "Verificar Itens", "Chat"))

        if page == "Info":
            info_page(token)
        elif page == "Inscrição":
            subscription_page(token)
        elif page == "Conta":
            subscription_status_page(token)
        elif page == "Adicionar Item":
            add_items_page(token)
        elif page == "Remover Item":
            remove_items_page(token)
        elif page == "Lista de Convidados":
            list_atendees(token)
        elif page == "Verificar Itens":
            check_items_page(token)
        elif page == "Chat":
            chat_page(token)

if __name__ == "__main__":
    main()

