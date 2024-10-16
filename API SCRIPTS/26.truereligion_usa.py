from time import time as t
initial_time = t()
import requests
import html
import time
sleep = time.sleep
from threading import Thread, Event
import re
from fake_useragent import UserAgent
fake_agent = UserAgent()
from common import Common
import colorama
import traceback
import random
from bs4 import BeautifulSoup
import functions
from urllib.parse import quote
import aiohttp
import asyncio
from proxy import *
set_proxies()

from deep_translator import GoogleTranslator
def translate(message):
    return GoogleTranslator(source='auto', target='en').translate(message)

import pymysql
from config import db_config
connection = pymysql.connect(host=db_config["host"], user=db_config["user"], passwd=db_config["passwd"],database=db_config["database"], port=db_config["port"])
from db_links import *
main_urls,categories = get_db_links(connection,'true.*religion','usa',other_column='additional_info')

for cat in categories:
    print(f'{cat} : {categories[cat]}')

################################## Global Variables ##################################

colorama.init()
RED = colorama.Fore.LIGHTRED_EX
CYAN = colorama.Fore.CYAN
GREEN = colorama.Fore.LIGHTGREEN_EX
YELLOW = colorama.Fore.YELLOW
LIGHTYELLOW = colorama.Fore.LIGHTYELLOW_EX
MAGENTA = colorama.Fore.LIGHTMAGENTA_EX
DARKGREEN = colorama.Fore.GREEN
BLUE = colorama.Fore.BLUE
RESET = colorama.Fore.RESET

width = 50

################################## Tools ##################################

def add_to_db(connection,data:dict,table_name='brands_data'):
    stopWatchControl('start','Adding data to DB')

    heads = list(data.keys())
    values = list(zip(*data.values()))  # Transpose the dictionary values

    query = f"INSERT INTO {table_name} ({','.join(heads)}) VALUES ({','.join(['%s'] * len(heads))})"

    cursor = connection.cursor()
    try:
        cursor.executemany(query, values)
        connection.commit()
        print(f"Inserted {cursor.rowcount} rows into {table_name}")
    except Exception as e:
        print(f"Error inserting data: {e}")
    finally:
        cursor.close()

    stopWatchControl('stop')

def center_data(string):
        l = len(string)
        return ' '*((width-l)//2) + string

def convertSeconds(seconds):
    seconds = float(seconds)
    hours = int(seconds / 3600)
    seconds %= 3600
    minutes = int(seconds / 60)
    seconds %= 60

    time_str = f"[{hours}:{minutes}:{seconds:.2f}]"
    return time_str

def stopWatch(start_time, track_string = "Time Elapsed"):
    global updated
    while not updated:
        currentTime = time.time()
        time_taken = currentTime-start_time
        time_taken = convertSeconds(time_taken)
        print(f'{LIGHTYELLOW}{track_string}: {time_taken}  ',end='\r')
        
    print(f'{LIGHTYELLOW}{track_string}: {time_taken}  ',end='\n')

def stopWatchControl(command, DisplayString = "Time Elapsed"):
    global updated
    command = command.lower()
    if 'start' in command:
        updated = False
        Thread(target=stopWatch, args=(time.time(),DisplayString)).start()
    elif 'stop' in command:
        updated = True

################################## Visualization ##################################

def progressBar(total, current, start_time):
    # current += 1
    
    empty = RED+'░'
    filled = GREEN+'█'
    border = BLUE+'|'

    percent = (current/total)*100
    filled_count = int(percent)
    empty_count = 100-filled_count

    try:
        t = time.time()
        time_left = (t-start_time)*(total/current) - (t-start_time)
    except: 
        time_left = 0

    time_left = convertSeconds(time_left)
    print(f'\r{border}{filled*filled_count}{empty*empty_count}{border}{YELLOW} {percent:.2f}% [{current}/{total}] {CYAN}{time_left} {RESET}',end='')

    if percent == 100:
        time_left = convertSeconds(time.time()-start_time)
        print(f'\r{border}{filled*filled_count}{empty*empty_count}{border}{YELLOW} {percent:.2f}% [{current}/{total}] {CYAN}{time_left} {MAGENTA}\n',end=RESET)

def convertSeconds(seconds):
    seconds = float(seconds)
    hours = int(seconds / 3600)
    seconds %= 3600
    minutes = int(seconds / 60)
    seconds %= 60

    time_str = f"[{hours}:{minutes}:{seconds:.2f}]"
    return time_str

# Function to fetch product descriptions
async def get_desc(session, url,proxy):
    headers = {
        'User-Agent': fake_agent.random,
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'TE': 'Trailers'
    }
    try:
        async with session.get(url, headers=headers, proxy=proxy) as response:
            if response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                desc_div = soup.find('ul', {'class': 'pdp-collapse-sec clearfix'})
                desc = desc_div.get_text("\n", strip=True) if desc_div else ''
                # title = soup.find('title').get_text(strip=True)
                # print(f'{url} : {title}')
                return url, desc
            else:
                return url, ''
    except Exception as e:
        # traceback.print_exc()
        print(f"Error fetching {url}: {e}")
        return url, ''
    
# Function to fetch descriptions from all URLs
async def fetch_all(urls):
    proxies = get_random_proxies(100)
    async with aiohttp.ClientSession() as session:
        tasks = [get_desc(session, url,proxies[i%100]) for i,url in enumerate(urls)]
        return await asyncio.gather(*tasks)

def description_extraction(urls):
    try:
        loop = asyncio.get_event_loop()
        data = loop.run_until_complete(fetch_all(urls))
        
        final_data = {url: desc for url, desc in data}
        return final_data
    except Exception as e:
        print(f"An error occurred: {e}")

headers = {
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
  'Accept': 'application/json',
  'Accept-Language': 'en-US,en;q=0.9'
}

base_url = "https://c1wbqk.a.searchspring.io/api/search/search.json"

params = {
    'userId': 'bb80399f-c088-4ea3-ab85-0ee008ca20fd',
    'domain': 'https%3A%2F%2Fwww.truereligion.com%2FCATEGORY_LINK_PART%3Flang%3Ddefault',
    'sessionId': '3da870c1-aef7-4528-b5e3-61a9230ad803',
    'pageLoadId': '0a870edf-f0f7-4ad6-aba6-504000d0a3cd',
    'siteId': 'c1wbqk',
    'resultsFormat': 'native',
    'bgfilter.record_type': 'variant',
    'redirectResponse': 'full',
    'ajaxCatalog': 'Snap'
}

Brand = 'True Religion'
Country = 'USA'
Price_unit = 'USD'

def clean_html(input_text):
    # Unescape HTML entities
    unescaped_text = html.unescape(input_text)
    # Remove HTML tags
    clean_text = re.sub(r'<.*?>', '', unescaped_text)

    return clean_text.replace('&')

final_data = {
    'brand_name':[],
    'product_link':[],
    'product_name':[],
    'product_category':[],
    'product_type':[],
    'product_price':[],
    'discounted_price':[],
    'price_unit':[],
    'price_usd':[],
    'product_description':[],
    'product_image':[],
    'country':[],
    'page_numer':[]
}

def append_data(response, final_data,category):
    pro_cat, pro_typ = category.split(' ',1)
    for product in response.json()['results']:
        try:
            brand_name = Brand
            product_link = product['url']
            product_name = product['name']
            product_category = pro_cat
            product_type = pro_typ
            product_price = product['msrp']
            discounted_price = product['price']
            price_unit = Price_unit
            price_usd = product_price
            product_description = ''
            product_image = product['imageUrl'].replace('t_dfs_small','t_kiosk_large')
            country = Country
            page_numer = response.json()['pagination']['currentPage']
        except:
            continue

        for key in final_data:
            final_data[key].append(eval(key))

    return final_data

for category in categories:
    additonal_params = {
        'bgfilter.ss_category': f'DENIM>Shop All Denim>{categories[category]}'
    }
    params.update(additonal_params)

    next_page = 1

    st = t()

    from pyperclip import copy

    print(f'\n{CYAN}Category: {category}\n')
    while next_page:
        params.update({'page': next_page})
        response = requests.get(base_url, headers=headers, params=params)
        currentPage = response.json()['pagination']['currentPage']
        next_page = response.json()['pagination']['nextPage']

        final_data = append_data(response, final_data,category)
        progressBar(response.json()['pagination']['totalPages'],currentPage,st)

    print(RED,'* - '*30)

stopWatchControl('start','Fetching Descriptions')

for i in range(10):

    urls = [url for url in final_data['product_link'] if not final_data['product_description'][final_data['product_link'].index(url)]]

    print(f'\n{CYAN}Fetching Descriptions: Attempt {i+1} - {LIGHTYELLOW}{len(urls)} {CYAN} URLs\n')
    
    if len(urls) == 0:
        break

    print(f'\n{CYAN}URLs to fetch: {len(urls)}\n')
    
    batch_size = 100

    for i in range(0, len(urls), batch_size):
        url_batch = urls[i:i+batch_size]

        all_descs_data = description_extraction(url_batch)

        for idx, product_link in enumerate(final_data['product_link']):
            desc = all_descs_data.get(product_link, '')
            if desc:
                final_data['product_description'][idx] = desc

stopWatchControl('stop')

total_products = len(final_data['brand_name'])

# delete all the products that do not have the description
final_data = {key:[value for idx,value in enumerate(values) if final_data['product_description'][idx]] for key,values in final_data.items()}

final_total_products = len(final_data['brand_name'])

final_data = {key:[value for idx,value in enumerate(values) if final_data['product_description'][idx]] for key,values in final_data.items()}

################################## Adding Data to DB ##################################
add_to_db(connection,final_data,'brands_data')

complete_time = t()
sleep(1)

print(f'Total Products: {total_products}')
print(f'Final Total Products: {final_total_products}')
print(f'Products removed without description: {total_products-final_total_products}')
total_time_taken = complete_time - initial_time
total_time_taken = convertSeconds(total_time_taken)
print(f'{GREEN}Total Time Taken: {total_time_taken}{RESET}')