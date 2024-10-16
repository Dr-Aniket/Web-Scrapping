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

def translate(message):
    def clean_string(input_string):
        # Remove non-UTF-8 characters
        return re.sub(r'[^\x00-\x7F]+', '', input_string)
    
    if message:

        translatedMessage = ''
        for line in message.split('\n'):
            try:
                translatedMessage += Common.translate_to_english(message=quote(line)) + '\n'
            except:
                pass
        message = translatedMessage

    return clean_string(message.strip())

import pymysql
from config import db_config
connection = pymysql.connect(host=db_config["host"], user=db_config["user"], passwd=db_config["passwd"],database=db_config["database"], port=db_config["port"])
from db_links import *
main_urls,categories = get_db_links(connection,'wrangler','india',other_column='additional_info')

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
    'accept': 'application/json, text/plain, */*',
    'accept-encoding': 'gzip, deflate, br, zstd',
    'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.6',
    'cookie':'AWSALBAPP-1=_remove_; AWSALBAPP-2=_remove_; AWSALBAPP-3=_remove_; _atstrkid=28023128973; _atftrkid=79168088298; connect.sid=s%3AUAWmhCf0yuUH9smFYGE_13ZhItzl2v3w.yoTputJi%2FZQ9EkpjReai7V9yiJjDlehSuUpfzb4C4vA; _gcl_au=1.1.249796329.1723723905; _ga=GA1.1.1496139148.1723723905; _fbp=fb.1.1723723906169.60313753165635242; _dd_s=rum=0&expire=1723729743477; _ga_M93TZENSQV=GS1.1.1723728629.2.1.1723728844.48.0.0; _uetsid=8a4084d05aff11ef9abf3d95bdf51004; _uetvid=949e8010846311ee89fcd3b87c30a885; AWSALBTG=wwny2nxXBQkB9nGhbt9Bn0OPpnAq3a074LzJ8a6OMZ9tQPAPPYTnk4ZdbNIoIdkwYnt5OGpAN1HJjUs4xONOnZNUmGzgy65vY4jpEH2Qao267Tgojuo4y9kup8ak7yJHtXv3PVLyhWgf22fhKcOt1WR44vl8cwkW1kQ1R3V4uAs+; AWSALBAPP-0=AAAAAAAAAACSujfXu1VVPiYPSqkn6OPTvRCmFknBJXtZ+DE5ePSCTgue8q4eKoZXUyBVqPk75ffHTr+pFl2kYSO0D+3nY4qamwQMPp0xVEjkI26EI7f+1xfI31mOlqp8a3G9GR/1aYma0NM=',
    'user-agent': fake_agent.random,
}

base_url = 'https://www.wrangler.in/api/v1/filteredProducts'

Brand = 'WRANGLER'
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

def append_data(response, final_data,category):
    pro_cat, pro_typ = category.split(' ',1)
    products = response.json()['data']
    print(f'{YELLOW}Total Products: {len(products)}\n')
    for product in products:
        try:
            brand_name = Brand
            product_link = 'https://www.wrangler.in/products/' + product['sku']
            product_name =  product['extra_attributes']['meta_title']
            product_category = pro_cat
            product_type = pro_typ
            product_price = get_price(product['mrp'])
            discounted_price = get_price(product['price'])
            price_unit = Price_unit
            price_usd = round(product_price*conversion_rate,2)
            product_description = product['description']
            other_details = re.sub(' [a-z]+_?[a-z]+:', lambda a: '\n'+a.group().strip(), product['nested_search'])
            product_description += '\n' + other_details.replace(':',': ').replace('_',' ').title() + '\nMaterial: ' + product['extra_attributes']['material']

            product_description = unquote(product_description).title()

            product_image = product['image'][0]
            country = Country
        except Exception as e:
            traceback.print_exc()
            print(f'{RED}Error: {e}')
            continue

        for key in final_data:
            final_data[key].append(eval(key))

    return final_data

for category in categories:
    print(f'\n{CYAN}Category: {category}\n')
    
    parameters = '?query={"categories.id":"category_id"}'.replace('category_id',categories[category]) + '&limit=1'

    category_api = base_url + parameters

    category_api = quote(category_api,safe=':/?&=')

    print(f'{YELLOW}Category API: {category_api}\n')

    response = requests.get(category_api, headers=headers)
    total_products = response.json()['totalCount']

    category_api = category_api.replace('limit=1','limit='+str(total_products))

    response = requests.get(category_api, headers=headers)
    
    final_data = append_data(response, final_data,category)

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