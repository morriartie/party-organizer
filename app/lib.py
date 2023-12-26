import configparser as cfg
import json

import pandas as pd


PESSOAS_DB = "parties/{token}/convidados.json"
ITEMS_DB = "parties/{token}/items.csv"

CODE_TO_PROD_NAME = {
    "cerveja": "Cerveja",
    "cachaca": "Cachaça",
    "salgados_e_doces": "Salgados e Doces",
    "refri_e_suco": "Refri e Suco" 
}


def add_person(name, checklist, token):
    '''
    {
    "cerveja":True,
    "cachaca":True,
    "salgados_e_doces":True,
    "refri_e_suco":True
    }
    '''
    name = name.lower().strip()
    d = json.loads(open(PESSOAS_DB.replace('{token}',token)).read())
    d[name] = checklist
    open(PESSOAS_DB.replace('{token}',token), 'w').write(json.dumps(d))
    return True

def load_person(name, token):
    name = name.lower().strip()
    d = json.loads(open(PESSOAS_DB.replace('{token}',token)).read())
    person_data = d.get(name)
    if person_data:
        return True, person_data
    else:
        return False, {}

def add_item(owner, product_name, quantity, category, unit_price, token):
    # Checking if the owner exists
    if not load_person(owner, token):
        return False, "Cadastro não encontrado"
    # Checking if the quantity is numeric
    try:
        int(quantity)
    except:
        return False, "Confira o valor 'quantidade'"
    # Checking if the unit price is numeric and reformat it
    try:
        float(unit_price)
    except:
        return False, "Confira o valor 'valor unitario'"
    #
    owner = owner.lower().strip()
    df = get_items(token)
    new_data = {"responsavel": [owner], "produto": [product_name], "quantidade": [quantity], "categoria": [category], "preco_unit": [unit_price]}
    df_new_data = pd.DataFrame(new_data)
    df_new = pd.concat([df, df_new_data], ignore_index=True)
    save_items(df_new, token)
    return True, ""

def get_product_category(product_name, token):
    df = get_items(token)
    return df[df['produto']==product_name]['categoria'].values[0]

def list_users(token):
    return list(json.loads(open(PESSOAS_DB.replace('{token}',token)).read()).keys())

def list_products(token):
    df = get_items(token)
    return list(df['produto'].values)

def get_user_categories(user, token):
    r, user_data = load_person(user, token)
    return [k for k,v in user_data.items() if v]

def get_consumers_for_product(product_name, token):
    category = get_product_category(product_name, token)
    users = list_users(token)
    consumers = []
    for user in users:
        selected_categories = get_user_categories(user, token)
        selected_categories = [CODE_TO_PROD_NAME[c] for c in selected_categories]
        if category in selected_categories:
            consumers.append(user)
    return consumers

def get_product_price(product_name, token):
    df = get_items(token)
    unit_price = df[df['produto']==product_name]['preco_unit'].iloc[0]
    quant = df[df['produto']==product_name]['quantidade'].iloc[0]
    total = unit_price * quant
    return unit_price, quant, total

def get_products_for_user(user, token):
    prod_list = []
    for prod in list_products(token):
        if user in get_consumers_for_product(prod, token):
            prod_list.append(prod)
    return prod_list

def get_amount_for_user(user, token):
    total_value = 0
    # products this user consumes
    products = get_products_for_user(user, token)
    # for each product, its fraction value is
    for prod in products:
        unit_price, quant, total = get_product_price(prod, token)
        consumers = get_consumers_for_product(prod, token)
        if user in consumers:
            price_per_consumer = total/len(consumers)
            total_value += price_per_consumer
    return total_value

def remove_product(df, quant, token):
    quant = int(quant)
    prod_name = df['produto'].iloc[0]
    prod_quant = df['quantidade'].iloc[0]
    max_rem = min(quant, prod_quant)
    new_quant = prod_quant - max_rem
    df = get_items(token)
    if new_quant == 0:
        df = df[df['produto']!=prod_name]
        save_items(df, token)
    else:
        df.loc[df['produto'] == prod_name, 'quantidade'] = new_quant 
    return prod_name, max_rem
        
def get_items(token):
    filename = ITEMS_DB.replace('{token}',token)
    df = pd.read_csv(filename)
    cols = [c for c in df.columns if 'nnamed' in c]
    for c in cols:
        df.drop(columns=c, inplace=True)
    return df

def save_items(df, token):
    filename = ITEMS_DB.replace('{token}',token)
    df.to_csv(filename, index=False)
