from time import time as t
initial_time = t()

import requests

statsData = {}

chrome = False
chrome = True
from urllib.parse import urlparse, parse_qs

if chrome:
    from selenium.webdriver.chrome.options import Options
else:
    from selenium.webdriver.firefox.options import Options
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
import urllib.parse
from selenium.webdriver.common.action_chains import ActionChains
import requests
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
from deep_translator import GoogleTranslator
def translate(message):
    return GoogleTranslator(source='auto', target='en').translate(message)

import pymysql
from config import db_config
connection = pymysql.connect(host=db_config["host"], user=db_config["user"], passwd=db_config["passwd"],database=db_config["database"], port=db_config["port"])
from db_links import *
links = main_urls = scrapping_urls = main_url = urls = get_db_links(connection,'asos','usa')

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
    current += 1
    
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

# Function to extract additional parameters from the URL
def extract_params(url):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    return {key: value[0] for key, value in query_params.items()}

# Base URL for the API request
base_url = "https://www.asos.com/api/product/search/v2/categories/C_ID"

# Parameters for the request
default_params = {
    'offset': 0,
    'includeNonPurchasableTypes': 'restocking',
    'store': 'US',
    'lang': 'en-US',
    'currency': 'USD',
    'rowlength': 4,
    'channel': 'desktop-web',
    'country': 'US',
    'keyStoreDataversion': '11a1qu9-40',
    'advertisementsPartnerId': '100716',
    'advertisementsOptInConsent': 'false',
    'limit': 200  # Consider starting with a smaller limit if rate limiting is a concern
}

headers = {
    'Cookie': '_abck=45E608940C3CF96FEBFB41D743671A21~-1~YAAQvW0/F48yaN+QAQAALdfd/QwYsJXavKFkOZpTbA0PLetqZmQp25haboOLBi1Pt08stY+IpzksM0t0K8Z1r4BWuVSfpo49GrE4cNkS3rK02pzOpsBBK6VMdQQsCE/pPPOvCOaa91VIBbZ8l35ZkT595ForzptN83kKbxKR6P8U8c29b42uVL5vtfO6tLxQY+z9HSl3QUqXNh7dzSQmlRZI+pxts33ByxeGzD1pGElH/TbgW3fWStCNabOcyyqtw9sWGjFSXpVfEj5W822+ICwefMPQKZ/th9dsh1Bm1EAfeJ9hr0Y0zGhey4Pk+NbaeiKdMJKwYI4kbm8EdV0jK6XLrUWLcJm1vJsoH0KmHVS7cIF1E9oU4QXA~-1~-1~-1; ak_bmsc=119F53A6E3D0B9A96627EB036428200E~000000000000000000000000000000~YAAQvW0/F5AyaN+QAQAALdfd/RiEz4O/4r/NX+PC45VaTXkK58wkMQ8giBUZy7CgxJ+vXBqqW7kI5eQR7h7TwxvkFWkN53SMfFF3ImhVLL3ioDeUphw07uovjgEG/tJX89x9Ul4CR7KFFZvLTuwa7/eT2X018PIVyro6w8W8uFTVXrj+lENtLAEVhavK3VjN4zquKp+95T36D851WFWhCtennoiZtjeRQGzsaAK0DCX280xzsZWOc9MlKd8l9xnboaqxQAnFdqcZrsrB7At0Om66DmbjpWUCb6f9q4YYKbJLYl+qGCROHVuoxhZsevoIrXh/hcj9qnFjxsAviJH5qGW3iIlkJaPuxujQF4euDJyBbrOat3hRHGTH; bm_sz=B8DC7661F404BDCE0E248B6FEACEBDDF~YAAQvW0/F5EyaN+QAQAALdfd/RiLPaL0fzVkiUs89OVBt1zwIpmwoYiesEtJMO8PgzQDgIFQv6wdjLXwpv8u7WqTJcpuf2ZTYYN8HAhojJ+xc1gOolNcFzc2+JZiuAPG5zknAiib8C4Wj8PX8hefG/fWGnjt1+PrpGIXrmq4IcpIPbYhLqD1eYN5qiZs81oiZ1trOdrOxegg4G2mFkrJ86kfRBecuAczarGrq37XCzb9cl39Fwe5jvpD36rZU214KBYhCqES3b+C2uEyFQwNZgtXk7W/yMpdJXm0YWnPPpiDr3htza7E+kU/izaVnBYc5JsqXJORwODuBvjwSxsZiqz4XK1NvcSpAUXo~4535092~4469058'
}

def get_product(c_id, additional_params):
    all_products = []
    offset = 0
    url = base_url.replace('C_ID',c_id)
    while True:
        params = default_params.copy()
        params.update(additional_params)
        params['offset'] = offset
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            print(f"Failed to fetch data: {response.status_code}")
            break

        data = response.json()
        products = data.get('products', [])
        
        if not products:
            break

        all_products.extend(products)
        offset += len(products)  # Adjust offset for the next set of products
        print(f"Fetched {len(products)} products, total: {len(all_products)}")
    return all_products

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


def getPrices(html):
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
    
    def setPrices(price1, price2):
        price1 = price1 if str(price1).replace('.','').strip() else 0
        price2 = price2 if str(price2).replace('.','').strip() else 0
        prices = [price1, price2]
        prices.sort()
        if len(prices) == 1:
            prices = [0, prices[0]]
        return prices
    
    html = re.sub(r'\d+\.?\d*%', '', html)

    prices = re.findall(r'\d+\.?\d*',html.replace(',',''))
    prices = [get_price(price) for price in prices]
    prices.sort()
    new_price, price = setPrices(prices[0],prices[-1])
    if new_price == price:
        new_price = 0

    return new_price, price

# Function to fetch product descriptions
async def get_desc(session, url):
    headers = {
        'User-Agent': fake_agent.random,
    }
    try:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                desc_div = soup.find('div', {'id': 'productDescription'})
                desc = desc_div.get_text("\n", strip=True) if desc_div else 'NO DESCRIPTION'
                return url, desc
            else:
                return url, ''
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return url, ''

# Function to fetch descriptions from all URLs
async def fetch_all(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [get_desc(session, url) for url in urls]
        return await asyncio.gather(*tasks)

def description_extraction(urls):
    try:
        loop = asyncio.get_event_loop()
        data = loop.run_until_complete(fetch_all(urls))
        
        final_data = {url: desc for url, desc in data}
        return final_data
    except Exception as e:
        print(f"An error occurred: {e}")

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
    'country':[]
}

usd_rate = 1 # functions.get_conversion_rate('gbp', 'usd')
added_products = []

brand = 'Asos'
country = 'USA'
currency = 'USD'

for typ, url in scrapping_urls.items():
    try:
        pro_category, pro_typ = typ.split(' ',1)
        url = url.replace('refine=attribute_1046:','attribute_1046=')
        c_id = re.search(r'cid=(\d+)', url).group(1)
        additional_params = extract_params(url)
        additional_params.pop('cid', None)
        print(f'{typ}: {c_id} : {url}')

        all_products = get_product(c_id, additional_params)
        total = len(all_products)
        start_time = time.time()
        for current_product,product in enumerate(all_products):
            try:
                product_url = 'https://www.asos.com/us/'+product['url']
                if product_url in added_products:
                    continue
                # print(f'Product URL: {product_url}')

                product_name = product['name']
                # print(f'Product Name: {product_name}')
                product_price = product['price']['previous']['value']
                product_price_discounted = product['price']['current']['value']

                product_price_discounted, product_price = getPrices(f'{product_price} {product_price_discounted}')
                # print(f'Product Price: {product_price}')
                # print(f'Product Price Discounted: {product_price_discounted}')

                product_image = 'https://'+product['imageUrl']+'?wid=1080&fit=constrain'
                # print(f'Product Image: {product_image}')

                product_price_usd = str(round(float(product_price) * float(usd_rate), 2))
                # print(f'Product Price USD: {product_price_usd}')

                # # product_description = det_desc(product_url)
                # product_description = get_description(product_url,'//div[@id="productDescription"]//text()')
                product_description = ''
                # print(f'Product Description: {product_description}')

                # input('Press Enter to continue...')

                final_data['brand_name'].append(brand)
                final_data['product_link'].append(product_url)
                final_data['product_name'].append(product_name)
                final_data['product_category'].append(pro_category)
                final_data['product_type'].append(pro_typ)
                final_data['product_price'].append(product_price)
                final_data['discounted_price'].append(product_price_discounted)
                final_data['price_unit'].append(currency)
                final_data['price_usd'].append(product_price_usd)
                final_data['product_description'].append(product_description)
                final_data['product_image'].append(product_image)
                final_data['country'].append(country)
            except Exception as e:
                traceback.print_exc()
                print(f'Error in {product["id"]}: {e}')

            progressBar(total, current_product, start_time)

    except Exception as e:
        traceback.print_exc()
        print(f'Error in {typ} : {e}')
        # input("Press Enter to continue...")

stopWatchControl('start','Fetching Descriptions')

total_products = len(final_data['brand_name'])

for i in range(20):

    urls = [url for url in final_data['product_link'] if not final_data['product_description'][final_data['product_link'].index(url)]]

    if len(urls) == 1:
        print(urls)

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

# delete all the products that do not have the description
final_data = {key:[value for idx,value in enumerate(values) if final_data['product_description'][idx]] for key,values in final_data.items()}

final_total_products = len(final_data['brand_name'])

add_to_db(connection,final_data,'brands_data')

complete_time = t()
sleep(1)

print(f'Total Products: {total_products}')
print(f'Final Total Products: {final_total_products}')
print(f'Products removed without description: {total_products-final_total_products}')
total_time_taken = complete_time - initial_time
total_time_taken = convertSeconds(total_time_taken)
print(f'{GREEN}Total Time Taken: {total_time_taken}{RESET}')