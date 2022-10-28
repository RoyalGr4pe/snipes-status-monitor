from requests import get
from json import load, loads, dump
from discord_webhook import DiscordWebhook, DiscordEmbed
from random import choice

import threading
import time
import sys
import os


countries = {
    'Netherlands': 'https://api.bazaarvoice.com/data/products.json?passkey=caF0jTMu2huVfNeLxlvhX31jXOUgB2gkTNndDyG5EJZ4Q&locale=nl_NL&allowMissing=true&apiVersion=5.4&filter=id:',
    'Germany': 'https://api.bazaarvoice.com/data/products.json?passkey=caPDtZZPBMwgOvcuYeVDzMZVPF2m88hQbgqKQW0cyTtv0&locale=de_DE&allowMissing=true&apiVersion=5.4&filter=id:',
    'France': 'https://api.bazaarvoice.com/data/products.json?passkey=cacWnTTJ3Ry7V1wosCErdWNm55wFU9asEbnuX7LCLtdzI&locale=fr_FR&allowMissing=true&apiVersion=5.4&filter=id:',
    'Spain': 'https://api.bazaarvoice.com/data/products.json?passkey=caZUqcxgiPAjkugeQqOILz7hpWO7Ud6gAtieYjgmoAXAY&locale=es_ES&allowMissing=true&apiVersion=5.4&filter=id:',
    'Portugal': 'https://api.bazaarvoice.com/data/products.json?passkey=caZUqcxgiPAjkugeQqOILz7hpWO7Ud6gAtieYjgmoAXAY&locale=pt_PT&allowMissing=true&apiVersion=5.4&filter=id:',
    'Poland': 'https://api.bazaarvoice.com/data/products.json?passkey=caRuCqh0XqsZk4jwzK3d7EAJVWZYPkvJer3yHY5bqyHMI&locale=pl_PL&allowMissing=true&apiVersion=5.4&filter=id:',
    'Belgium': 'https://api.bazaarvoice.com/data/products.json?passkey=caF0jTMu2huVfNeLxlvhX31jXOUgB2gkTNndDyG5EJZ4Q&locale=nl_BE&allowMissing=true&apiVersion=5.4&filter=id:',
    'Italy': 'https://api.bazaarvoice.com/data/products.json?passkey=caZUqcxgiPAjkugeQqOILz7hpWO7Ud6gAtieYjgmoAXAY&locale=it_IT&allowMissing=true&apiVersion=5.4&filter=id:',
    'Switzerland': 'https://api.bazaarvoice.com/data/products.json?passkey=cam4o8saRauRBuuzpkW7UU34ycefHB6ZINSAbzhjHkQ1M&locale=de_CH&allowMissing=true&apiVersion=5.4&filter=id:',
    'Croatia': 'https://api.bazaarvoice.com/data/products.json?passkey=caeVIl89UDA8aIvlhbPBoqyQH2KaP4sr1hKeyfI725i4I&locale=hr_HR&allowMissing=true&apiVersion=5.4&filter=id:',
}


def get_settings():  # Get all the data that is stored in settings.json
    with open('settings.json', 'r') as file:
        settings = load(file)
        file.close()

    return settings


settings = get_settings()
delay = settings['Delay']
country = settings['Country']
webhook_urls = settings['Webhook Urls']
headers = {'User-Agent': settings['User-Agent']}


def get_proxy():  # Gets all proxy in the proxy file and makes a list from them
    with open('proxies.txt', 'r') as proxy_file:
        proxy_list = [proxy.strip() for proxy in proxy_file.readlines()]
        proxy_file.close()

    # Chooses a random proxy from proxy_list
    if proxy_list != []:
        proxy_url = choice(proxy_list)

        # Splits user:pass:ip:port up
        proxy_items = proxy_url.split(':')

        username = proxy_items[2]
        password = proxy_items[3]
        ip = proxy_items[0]
        port = proxy_items[1]

        proxy = {
            'http': f'http://{username}:{password}@{ip}:{port}/',
        }
        return proxy
    else:
        return {}


def send_update(ID, status, content):  # Sends the update via discord
    name = content['Results'][0]['Name']
    brand = content['Results'][0]['Brand']['Name']
    product_url = content['Results'][0]['ProductPageUrl']
    image_url = content['Results'][0]['ImageUrl']

    if status in ['true', 'True', 'TRUE']:
        colour = '0x00ff00'
    else:
        colour = '0xff0000'

    webhook = DiscordWebhook(url=webhook_urls)

    embed = DiscordEmbed(title=name, url=product_url, color=colour)
    embed.set_thumbnail(url=image_url)
    embed.add_embed_field(name='Status', value=status, inline=True)
    embed.add_embed_field(name='Brand', value=brand, inline=True)
    embed.add_embed_field(name='ID', value=ID, inline=True)

    webhook.add_embed(embed)
    time.sleep(delay)
    webhook.execute()


def update_data(ID, status):  # Updates the status when it is changed
    with open('snipes_data.json', "r") as file:
        data = load(file)

    data[ID]['Active'] = status

    with open('snipes_data.json', 'w') as file:
        dump(data, file, indent=4)


def get_IDs():  # Get all the ids in snipes_ids.txt
    file = open('snipes_ids.txt', 'r')
    IDs = [ID.strip() for ID in file.readlines()]
    return IDs


def get_data():  # Gets the data from snipes_data.json
    with open('snipes_data.json', 'r') as data_file:
        # Reading from json file
        stored_data = load(data_file)
        data_file.close()

    return stored_data


def add_to_data(ID, content):  # Adds data to snipes_data.json
    if content['Results'] == []:
        data[ID] = {
            'Name': None,
            'Active': None
        }

    else:
        name = content['Results'][0]['Name']
        status = content['Results'][0]['Active']
        with open('snipes_data.json', "r") as file:
            data = load(file)

        data[ID] = {
            'Name': name,
            'Active': status
        }

    with open('snipes_data.json', 'w') as file:
        dump(data, file, indent=4)


def compare_data(ID, stored_data, content):  # Checking if the products status has changed
    status = content['Results'][0]['Active']
    #status = choice(['true', 'false'])

    if status != stored_data[ID]['Active']:
        update_data(ID=ID, status=status)
        send_update(ID=ID, status=status, content=content)


def main():
    proxies = get_proxy()
    IDs = get_IDs()
    for ID in IDs:
        url = countries[country]+ID
        try:
            response = get(url=url, headers=headers, proxies=proxies)
        except Exception as error:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            continue

        content = loads(s=response.content)

        stored_data = get_data()

        if ID in stored_data.keys():
            # If id in snipes_data.json then compare the data
            compare_data(ID=ID, stored_data=stored_data, content=content)
        else:
            # If id not in snipes_data.json then add it
            add_to_data(ID=ID, content=content)


print("""
------------------------------------------------------------------------------------------------
Information:

- If you wish to view the data stored for your ids, go into snipes_data.json.

- Please don't change any data in the json files while the program is running. Errors may occur!

- If a change occurs you will get an update via Discord not this terminal!

- If you don't understand why you got an error, please look it up before messaging me.
------------------------------------------------------------------------------------------------
""")

while True:
    def loadingAnimation(process):
        while process.is_alive():
            chars = ['.', '..', '...', '   ']
            for char in chars:
                sys.stdout.write('\r'+'Program Running'+char)
                time.sleep(0.4)
                sys.stdout.flush()

    try:
        loading_process = threading.Thread(target=main)
        loading_process.start()

        loadingAnimation(loading_process)
        loading_process.join()

    except Exception as error:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
