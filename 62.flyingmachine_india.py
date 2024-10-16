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
import json
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
main_urls = get_db_links(connection,'flying','india')

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

                product = str(soup.prettify()).split('window.DATA=')
                product = product[-1]
                product = product.split('</script>')
                product = product[0].strip()
                product = json.loads(product)
                product = product['ProductStore']['PdpData']['mainStyle']
                compos = ''
                for key,value in product['finerDetails']['compositionAndCare'].items():
                    compos += '\n'.join(value) if type(value) == list else value + '\n'
                specs = ''
                for key,value in product['finerDetails']['specs'].items():
                    specs += '\n'.join(value) if type(value) == list else value + '\n'
                desc = compos + '\n\n' + specs

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
    len_of_proxies = len(proxies)
    async with aiohttp.ClientSession() as session:
        tasks = [get_desc(session, url,proxies[i%len_of_proxies]) for i,url in enumerate(urls)]
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
    "accept": "application/json",
    "content-type": "application/json",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "origin": "https://flyingmachine.nnnow.com",
    "referer": "https://flyingmachine.nnnow.com/",
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "bbversion": "v2",
    "clientsessionid": "1726132312989",  # Replace with a valid session ID if necessary
    "correlationid": "790190af-c032-40e1-b70a-7b3652f9e298",  # Replace with a valid correlation ID if necessary
    "module": "odin"
}

base_url = "https://api.nnnow.com/d/apiV2/listing/products"

Brand = 'FLYING MACHINE'
Country = 'INDIA'
Price_unit = 'INR'

conversion_rate = functions.get_conversion_rate('INR','USD')

def fetch_products(category):
    all_products = []
    page = 1
    while True:
        payload = {
            "deeplinkurl": f"/{category}?p={page}&cid=tn_{category.replace('-', '_')}",
            "brandDetails": {
                "isBrandJourney": True,
                "legalBrandNames": ["Flying Machine", "Flying Machine Women", "FM Boys"],
                "parentBrand": "Flying Machine"
            }
        }
        print(f'{GREEN}PAGE: {CYAN}{page}')
        # Make the POST request
        response = requests.post(base_url, headers=headers, json=payload)
        
        # Check if the request was successful
        if response.status_code == 200:
            try:
                # Parse the JSON response
                data = response.json()
                products = data['data']['styles']['styleList']
                
                # If no more products, break the loop
                if not products:
                    break
                
                # Add products to the all_products list
                all_products.extend(products)
                
                # Increment page number to get the next set of products
                page += 1
                
            # except json.JSONDecodeError:
            except Exception as e:
                print(f'{e}')
                print("Failed to parse JSON response")
                break
        else:
            print(f"Request failed with status code {response.status_code}")
            break

    return all_products

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

def append_data(products, final_data,category):
    pro_cat, pro_typ = category.split(' ',1)
    print(f'{YELLOW}Total Products: {len(products)}\n')
    for product in products:
        
        try:
            brand_name = Brand
            product_link = 'https://flyingmachine.nnnow.com' + product['url']
            product_name =  product['name']
            product_category = pro_cat
            product_type = pro_typ
            product_price = product['mrpRange']['min']
            discounted_price = product['sellingPriceRange']['min']
            price_unit = Price_unit
            price_usd = round(product_price*conversion_rate,2)
            product_description = ''
            product_image = product['imagePath'].replace('medium', 'large')
            country = Country
        except Exception as e:
            print(f'{RED}Error: {e}')
            continue

        for key in final_data:
            final_data[key].append(eval(key))

    return final_data

for category in main_urls:
    print(f'\n{CYAN}Category: {category}\n')
    category_link = main_urls[category].split('/')[-1]

    products = fetch_products(category_link)

    final_data = append_data(products, final_data,category)

    print(RED,'* - '*30)

stopWatchControl('start','Fetching Descriptions')

total_products = len(final_data['brand_name'])

for i in range(5):

    urls = [url for url in final_data['product_link'] if not final_data['product_description'][final_data['product_link'].index(url)]]

    print(f'\n{CYAN}Fetching Descriptions: Attempt {i+1} - {LIGHTYELLOW}{len(urls)} {CYAN} URLs\n')
    
    if len(urls) == 0:
        break
    elif len(urls) < 0.05*total_products and i>15:
        break

    print(f'\n{CYAN}URLs to fetch: {len(urls)}\n')
    
    batch_size = 99

    for i in range(0, len(urls), batch_size):
        print(f'\n{YELLOW}Batch {i//batch_size+1} - {i} to {i+batch_size}\n')
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