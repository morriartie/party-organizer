from datetime import datetime as dt
import configparser as cfg
import json
import os

import pandas as pd


PESSOAS_DB = "parties/{token}/convidados.json"
ITEMS_DB = "parties/{token}/items.csv"
CHAT_DB = "parties/{token}/chat.json"
INFO_FILE = "parties/{token}/info.md"
CATEGORIES_FILE = "parties/{token}/categories.json"

#CODE_TO_PROD_NAME = {
#    "cerveja": "Cerveja",
#    "cachaca": "Cachaça",
#    "salgados_e_doces": "Salgados e Doces",
#    "refri_e_suco": "Refri e Suco" 
#}

CATEGORIAS = [
    "Cerveja",
    "Gin",
    "Whisky",
    "Rum",
    "Vodka",
    "Champagne",
    "Suco",
    "Salgados",
    "Doce",
    "Refri",
    "Vinho",
    "Água",
    "Utensílios",
    "ETC",
]

#PROD_NAME_TO_CODE = {v:k for k,v in CODE_TO_PROD_NAME.items()}

def add_person(name, user_data, token):
    name = name.lower().strip()
    d = load_clients(token)
    d[name] = user_data

    creation = str(dt.now()).split('.')[0]
    if name in list_users(token):
        person_data = load_person(name, token)[1]
        if 'creation' in person_data:
            creation = person_data['creation']
    d[name]['creation'] = creation

    save_clients(d, token)
    return True

def load_person(name, token):
    name = name.lower().strip()
    d = load_clients(token)
    person_data = d.get(name)
    if person_data:
        return True, person_data
    else:
        return False, {}

def add_item(owner, product_name, quantity, category, unit_price, vegan, token):
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
    new_data = {"responsavel": [owner], "produto": [product_name], "quantidade": [quantity], "categoria": [category], "preco_unit": [unit_price], "vegano":[vegan]}
    df_new_data = pd.DataFrame(new_data)
    df_new = pd.concat([df, df_new_data], ignore_index=True)
    save_items(df_new, token)
    return True, ""

def get_product_category(product_name, token):
    df = get_items(token)
    return df[df['produto']==product_name]['categoria'].values[0]

def list_users(token):
    return list(load_clients(token).keys())

def list_products(token):
    df = get_items(token)
    return list(df['produto'].values)

def get_user_categories(user, token):
    r, user_data = load_person(user, token)
    return [k for k,v in user_data['consumo'].items() if v]

def is_user_vegan(user, token):
    r, user_data = load_person(user, token)
    return user_data['vegano']

def is_product_vegan(product_name, token):
    df = get_items(token)
    return df[df['produto']==product_name]['vegano'].values[0] == True

def get_consumers_for_product(product_name, token):
    category = get_product_category(product_name, token)
    users = list_users(token)
    prod_vegan = is_product_vegan(product_name, token)
    consumers = []
    for user in users:
        selected_categories = get_user_categories(user, token)
        is_vegan = is_user_vegan(user, token)
        selected_categories = [c for c in selected_categories]
        if category not in selected_categories:
            continue
        if is_vegan and not prod_vegan:
            continue
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
        save_items(df, token)
    return prod_name, max_rem

def list_users_detailed(token):
    clients = load_clients(token)
    categories = CATEGORIAS #[v for k,v in CODE_TO_PROD_NAME.items()]
    columns = ["Nome", *categories, "Vegano", "Criacao"]
    d = {v:[] for v in columns}
    for client in clients:
        d["Nome"].append(client)
        d["Criacao"].append(clients[client]['creation'])
        d["Vegano"].append(clients[client]['vegano'])
        for category in categories:
            v = clients[client]['consumo'].get(category)
            if v:
                d[category].append(v)
            else:
                d[category].append(False)
    return pd.DataFrame(d)

def user_message(user, message, token):
    timestamp = ':'.join(str(dt.now()).split(':')[:2])
    chat = load_chat(token)
    chat.append({"role":"user", "user":user ,"content":f"{message}", "time":timestamp})
    save_chat(chat, token)

def system_message(message, token):
    timestamp = ':'.join(str(dt.now()).split(':')[:2])
    chat = load_chat(token)
    chat.append({"role":"assistant", "content":message, "time":timestamp})
    save_chat(chat, token)

def get_info(token):
    path = INFO_FILE.replace('{token}',token) 
    filename = path.split('/')[-1]
    exists = filename in os.listdir(f'parties/{token}/')
    if not exists:
        default_text = "<- Acesse o menu da lateral"
        open(path,'w').write(DEFAULT_TXT)
        return DEFAULT_TXT
    return open(path).read()

def save_chat(chat, token):
    return open(CHAT_DB.replace('{token}',token),'w').write(json.dumps(chat))
    
def load_chat(token):
    fname = CHAT_DB.split('/')[-1]
    exists = fname in os.listdir(f'parties/{token}/')
    if not exists:
        return []
    content = open(CHAT_DB.replace('{token}',token)).read()
    return json.loads(content)

    
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

def load_clients(token):
    return json.loads(open(PESSOAS_DB.replace('{token}',token)).read())

def save_clients(d, token):
    open(PESSOAS_DB.replace('{token}',token), 'w').write(json.dumps(d))
    return True
