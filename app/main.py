import streamlit as st
import lib


remap_item = {
"refri_e_suco":"Refri e Suco",
"salgados_e_doces":"Salgados e Doces",
"cachaca":"Cachaça",
"cerveja":"Cerveja"
}


# Function for the Subscription Page
def subscription_page():
    st.title("Inscrição")

    # Text input for name
    nome = st.text_input("Nome:")
    token = st.text_input("token (veja no grupo): ")

    if token != "galeradalaje":
        st.error("token invalido, pergunte para (98)98270-0001")
    else:
        st.success("token válido")

    # Checkboxes for various consumable items
    st.write("O que vai consumir:")
    cerveja = st.checkbox("Cerveja")
    cachaca = st.checkbox("Cachaça")
    salgados_doces = st.checkbox("Salgados e Doces")
    refri_suco = st.checkbox("Refri e Suco")

    if st.button("Salvar"):
        d = {"cerveja": cerveja, "cachaca": cachaca, "salgados_e_doces": salgados_doces, "refri_e_suco": salgados_doces}
        lib.add_person(nome, d)
        st.success("Dados salvos com sucesso!")
        

# Function for the Subscription Status Page
def subscription_status_page():
    st.title("Seus dados:")

    nome = st.text_input("Nome cadastrado:")
    nome = nome.lower().strip()

    if st.button("Carregar Dados"):
        # Fetching data using the load_person function
        r, preferences = lib.load_person(nome)

        if r:
            st.write(f"Consumos:")
            for item, value in preferences.items():
                #st.write(f"{item}: {'Sim' if value else 'Não'}")
                st.checkbox(item.capitalize(), value, disabled=True)
            st.write("(Edite na aba de inscrição)")
        else:
            st.warning("Nome não encontrado.")

        categorias = [remap_item[v] for v,k in lib.load_person(nome)[1].items() if k]

        df = lib.get_items()
        df['total'] = df['preco_unit'] * df['quantidade']
        df = df[df['categoria'].isin(categorias)]
        st.title("Contribuições:")
        own_df = df[df['responsavel']==nome]
        st.dataframe(own_df)
        st.title("Custo total das contribuições:")
        own_total_value = sum(own_df['total'])
        st.title(f"R$ {own_total_value:.2f}".replace(',','.'))
        st.title("Lista de consumíveis disponíveis:")
        available_df = df[df['categoria'].isin(categorias)]
        st.dataframe(available_df)
        st.title("Valor total da parte:")
        #available_df['total'] = available_df['preco_unit'] * available_df['quantidade']
        total_value = lib.get_amount_for_user(nome)
        st.title(f"R$ {total_value:.2f}".replace('.',','))
        st.title("Valor a ser pago (total - gastos):")
        st.title(f"R$ {total_value-own_total_value:.2f}")
        st.title("Pix:")
        st.image("pix.jpeg")

# Function for the Add Items Page
def add_items_page():
    st.title("Adicione produtos que você vai levar:")

    nome = st.text_input("Nome:")
    if st.button("Verificar"):
        r, preferences = lib.load_person(nome)
        if r:
            st.success("cadastro encontrado")
        else:
            st.error("cadastro não encontrado")  
    prod_name = st.text_input("Nome do produto:")
    quant = st.text_input("Quantidade: ")
    category = st.selectbox('Categoria: ', ["Cerveja", "Cachaça", "Salgados e Doces", "Refri e Suco"])
    unit_value = st.text_input("Valor unitário")
    if st.button("Inserir"):
        r, msg = lib.add_item(nome, prod_name, quant, category, unit_value)
        if not r:
            st.error(msg)
        else:
            st.success("Produto adicionado com sucesso")

def check_items_page():
    st.title("Itens da festa:")
    st.dataframe(lib.get_items())
    st.title("Valor total:")
    df = lib.get_items()
    df['total'] = df['preco_unit'] * df['quantidade']
    total_val = sum(df['total'])
    st.title(f"R$ {total_val:.2f}".replace(".",","))

def remove_items_page():
    nome = st.text_input("Nome cadastrado:")
    df = lib.get_items()
    items = df[df['responsavel']==nome]['produto'].values
    selecao = st.selectbox("Item a ser removido:", items)
    quant = st.text_input("Quantidade:")
    df_u = df[df['responsavel']==nome]
    selected_df = df_u[df_u['produto']==selecao]
    st.dataframe(selected_df)
    if st.button("remover"):
        prod_name, units = lib.remove_product(selected_df, quant)
        st.success(f"Retirado {units} unidades do produto {prod_name}")


def main():
    st.sidebar.title("Navegação")
    page = st.sidebar.radio("Go to", ("Inscrição", "Conta", "Adicionar Item", "Remover Item", "Verificar Itens"))

    if page == "Inscrição":
        subscription_page()
    elif page == "Conta":
        subscription_status_page()
    elif page == "Adicionar Item":
        add_items_page()
    elif page == "Remover Item":
        remove_items_page()
    elif page == "Verificar Itens":
        check_items_page()

if __name__ == "__main__":
    main()
