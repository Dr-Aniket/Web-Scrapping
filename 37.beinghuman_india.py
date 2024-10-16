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
from urllib.parse import unquote

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
main_urls,categories = get_db_links(connection,'being','india',other_column='additional_info')

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

headers = {
    "accept": "*/*",
    "content-type": "application/json",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "origin": "https://beinghumanclothing.com",
    "referer": "https://beinghumanclothing.com/",
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "country": "en-in"
}

base_url = "https://engine.kartmax.in/api/fast/search/v1/b32e2ffeb77fad04ec54cdf13b1677d2/plp-special"

Brand = 'BEING HUMAN'
Country = 'INDIA'
Price_unit = 'INR'

conversion_rate = functions.get_conversion_rate('INR','USD')

def get_price(value):
    value = str(value)
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

def append_data(products, final_data,category):
    pro_cat, pro_typ = category.split(' ',1)
    print(f'{YELLOW}Total Products: {len(products)}\n')
    for product in products:
        try:
            brand_name = Brand
            product_link = 'https://beinghumanclothing.com/product/' + quote(product['url_key'], safe=':/')
            product_name =  product['name']
            product_category = pro_cat
            product_type = pro_typ
            product_price = get_price(product['price'])
            discounted_price = get_price(product['selling_price'])
            price_unit = Price_unit
            price_usd = round(product_price*conversion_rate,2)
            
            product_description = product['description']

            PRODUCT_SPECIFICATION = ['colour','fabric','fit','neck','composition','length','closure','manufacturing']

            product_description += '\n\n'
            for spec in PRODUCT_SPECIFICATION:
                if product[spec]:
                    try:
                        product_description += f'{spec}: {product[spec]}\n'
                    except:
                        pass
            product_description = product_description.strip().title()

            product_image = 'https://pictures.kartmax.in/cover/live/1080x1080/quality=10/' + quote(product['image'], safe=':/')
            country = Country
        except Exception as e:
            traceback.print_exc()
            print(f'{RED}Error: {e}')
            continue

        for key in final_data:
            final_data[key].append(eval(key))

    return final_data

# Function to fetch products for a given category
def fetch_products(category_uuid):
    all_products = []
    page = 1
    
    while True:
        # Define parameters for the request
        params = {
            "page": page,
            "count": 100,  # Adjust count based on API limits and requirements
            "sort_by": "rank",
            "sort_dir": "asc",
            "filter": "_category~Jeans",
            "fieldspecials": f"_uuid~{category_uuid}|overall_stock_status~in-stock",
            "country": "en-in"
        }


        print(f'Fetching page {page} for category {category}')

        # Make the GET request
        response = requests.get(base_url, headers=headers, params=params)
        
        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            products = data['result']['products']
            
            # If no more products, break the loop
            if not products:
                break
            
            # Add products to the all_products list
            all_products.extend(products)
            
            # Increment page number to get the next set of products
            page += 1
        else:
            break
    
    return all_products

for category in categories:
    print(f'\n{CYAN}Category: {category}\n')
    products = fetch_products(categories[category])
    final_data = append_data(products, final_data,category)

    print(RED,'* - '*30)

total_products = len(final_data['brand_name'])

################################## Adding Data to DB ##################################
add_to_db(connection,final_data,'brands_data')

complete_time = t()
sleep(1)

print(f'Total Products: {total_products}')
total_time_taken = complete_time - initial_time
total_time_taken = convertSeconds(total_time_taken)
print(f'{GREEN}Total Time Taken: {total_time_taken}{RESET}')