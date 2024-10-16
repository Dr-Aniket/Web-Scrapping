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
from urllib.parse import unquote
from proxy import *
set_proxies()

from deep_translator import GoogleTranslator
def translate(message):
    return GoogleTranslator(source='auto', target='en').translate(message)

import pymysql
from config import db_config
connection = pymysql.connect(host=db_config["host"], user=db_config["user"], passwd=db_config["passwd"],database=db_config["database"], port=db_config["port"])
from db_links import *
main_urls = get_db_links(connection,'h&m','uk')

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
                desc_div = soup.find('div', {'class': 'a64c9d'})
                desc = desc_div.get_text("\n", strip=True) if desc_div else ''

                desc = desc.split('Care guide')[0].strip()
                return url, desc
            else:
                return url, ''
    except Exception as e:
        traceback.print_exc()
        print(f"Error fetching {url}: {e}")
        return url, ''
# Function to fetch descriptions from all URLs
async def fetch_all(urls):
    proxies = get_random_proxies(100)
    async with aiohttp.ClientSession() as session:
        tasks = [get_desc(session, url,proxies[i%len(proxies)]) for i,url in enumerate(urls)]
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
    'accept': 'application/json, text/javascript, */*; q=0.01',
    'accept-encoding': 'gzip, deflate, br, zstd',
    'accept-language': 'en-US,en;q=0.6',
    'cookie': 'akainst=APAC; AKA_A2=A; utag_main__sn=1; utag_main_ses_id=1722936942045%3Bexp-session; dep_sid=s_3905517190151657.1722936942048; utag_main_segment=normal%3Bexp-session; INGRESSCOOKIE=1722936951.1475129.903341|7bbf721d92a09b08c42eb8596390c8cc; JSESSIONID=44A8A0991627272F26F264241C5A42A7F25A96D79D9517F16D0CE1CE88CD466D70D4999F3B26F7BA02E2873571E8033DA40F121841FF86F4E1AB85024C9D82B1.hybris-ecm-web-6cbb74c66b-r8g26; userCookie=##eyJjYXJ0Q291bnQiOjB9##; ak_bmsc=6FDE2F6256D9D7D6DBFFAA2EF0E98D76~',
    'user-agent': fake_agent.random,
}

base_urls = [
    'CATEGORY_LINK/_jcr_content/main/productlisting.display.json',
    'CATEGORY_LINK/_jcr_content/main/productlisting_b887.display.json',
    'CATEGORY_LINK/_jcr_content/main/productlisting_5f18.display.json',
    'CATEGORY_LINK/_jcr_content/main/productlisting_169f.display.json'
    ]

params = {
    'sort': 'stock',
    'image-size': 'small',
    'image': 'model',
    'offset': 0,
    'page-size': 2000,
    'materials':'Denim'
}

Brand = 'H&M'
Country = 'UK'
Price_unit = 'GBP'

conversion_rate = functions.get_conversion_rate('GBP','USD')

def get_price(value):
    if value:
        value = value.replace(',','').replace(' ','')
        value = re.search(r'\d+\.?\d*',value)
        if value:
            value = value.group()
            value = eval(value)
        else:
            return ''   
    return value

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
}

def append_data(response, final_data,category):
    pro_cat, pro_typ = category.split(' ',1)
    products = response.json()['products']
    print(f'{YELLOW}Total Products: {len(products)}\n')
    for product in products:
        
        try:
            brand_name = Brand
            product_link = 'https://www2.hm.com/'+product['link']
            product_name =  product['title']
            product_category = pro_cat
            product_type = pro_typ
            product_price = get_price(product['price'])
            discounted_price = get_price(product['redPrice'])
            price_unit = Price_unit
            price_usd = round(product_price*conversion_rate,2)
            product_description = ''
            product_image = 'https:'+product['image'][0]['src'].replace('set=source','set=quality[100],source').replace('/style]','/main]')
            country = Country
        except Exception as e:
            print(f'{RED}Error: {e}')
            continue

        for key in final_data:
            final_data[key].append(eval(key))

    return final_data

for category in main_urls:
    print(f'\n{CYAN}Category: {category}\n')
    category_link = main_urls[category].split('.html')[0]

    for base_url in base_urls:
        category_api = base_url.replace('CATEGORY_LINK',category_link)
        print(f'{YELLOW}API: {category_api}\n')

        response = requests.get(category_api, headers=headers, params=params)
        
        if 'URL was not found' not in response.text:
            break

    final_data = append_data(response, final_data,category)

    print(RED,'* - '*30)

stopWatchControl('start','Fetching Descriptions')

total_products = len(final_data['brand_name'])

for i in range(70):

    urls = [url for url in final_data['product_link'] if not final_data['product_description'][final_data['product_link'].index(url)]]

    if len(urls) == 1:
        input(urls)

    print(f'\n{CYAN}Fetching Descriptions: Attempt {i+1} - {LIGHTYELLOW}{len(urls)} {CYAN} URLs\n')
    
    if len(urls) == 0:
        break
    elif len(urls) < 0.05*total_products and i>15:
        break

    print(f'\n{CYAN}URLs to fetch: {len(urls)}\n')
    
    batch_size = 200

    for i in range(0, len(urls), batch_size):
        url_batch = urls[i:i+batch_size]

        all_descs_data = description_extraction(url_batch)

        for idx, product_link in enumerate(final_data['product_link']):
            desc = all_descs_data.get(product_link, '')
            if desc:
                final_data['product_description'][idx] = desc

stopWatchControl('stop')

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