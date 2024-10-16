import requests # pip install requests
import os
import zipfile # pip install zipfile
import fnmatch # pip install fnmatch
from lxml import html # pip install lxml
import re 
import json 
import time
import pandas as pd # pip install pandas
import numpy as np # pip install numpy
import pymysql # pip install pymysql
from scrapy.selector import Selector # pip install scrapy
from datetime import datetime  
from selenium import webdriver # pip install selenium
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random
import logging # pip install logging
try:
    from translator import TRANSLATE # type: ignore
    print(f'AWS Translator Imported')
except Exception as e:
    print(f'AWS Translator Not Imported: {e}')
    print(f'Google Translator Imported')
    from deep_translator import GoogleTranslator # pip install deep-translator
    def TRANSLATE(message,source='auto',target='en'):
        return GoogleTranslator(source=source, target=target).translate(message)
    
import colorama # pip install colorama

colorama.init()
RED = colorama.Fore.RED
GREEN = colorama.Fore.GREEN
BLUE = colorama.Fore.BLUE
RESET = colorama.Fore.RESET
logging.getLogger('selenium').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('scrapy.core.engine').disabled = True
logging.getLogger('scrapy').setLevel(logging.WARNING)
logging.basicConfig(level=logging.ERROR)

def find_base_path():
    # get the current files Global Address
    current_file_name = os.path.realpath(__file__)

    # get the Directory name of the current file
    current_dir = os.path.dirname(current_file_name)

    # get the Directory which contains the common_lib
    while True:
        if 'common_lib' in os.listdir(current_dir):
            break
        current_dir = os.path.dirname(current_dir)
    
    return current_dir

base_path=find_base_path()
common_lib_path = os.path.join(base_path, 'common_lib')

def insert_dataframe_to_sql(data : list,
                            curr_symbol: str,
                            brand_name: str,
                            country: str,
                            translate :bool =False,
                            name_translate: bool=False,
                            source_lang: str = "auto",
                            ):
    """
    Inserts a pandas DataFrame into a SQL table using pymysql.
    
    :param df: pandas DataFrame to be inserted
    :param table_name: Name of the table where the data will be inserted
    :param db_config: Dictionary containing database connection parameters. Example:
                      {
                          'host': 'localhost',
                          'user': 'username',
                          'password': 'password',
                          'database': 'database_name'
                      }
    """
    curr_symbol=curr_symbol
    curr_iso=get_currency_code(curr_symbol)
    curr_mul=get_exchange_rate(curr_iso)
    curr_iso=get_currency_symbol_for_db(curr_iso)
    curr_iso=get_currency_symbol_via_country(country,curr_iso)
    df=pd.DataFrame(
        data,
        columns=["product_name",
                 "discounted_price",
                 "product_price",
                 "product_description",
                 "product_image",
                 "product_link",
                 "product_category",
                 "product_type",
                 "page_numer"
                 ]
                 )
    try:
        df[["product_price","discounted_price"]]=df[["product_price","discounted_price"]].replace('',0).fillna(0)
        df = df.apply(adjust_prices, axis=1)
        df[["product_price","discounted_price"]]=df[["product_price","discounted_price"]].replace(0,'')
        df['product_description']=df['product_description'].apply(normalize_text)
        df['product_name']=df['product_name'].apply(normalize_text)
        if name_translate:
            df['product_name']=df['product_name'].apply(TRANSLATE,source=source_lang)
        if translate:
            df['product_description']=df['product_description'].apply(TRANSLATE,source=source_lang)

        df["brand_name"]=brand_name
        df["price_unit"]=curr_iso
        df["price_usd"]=round(df["product_price"].astype(float)*curr_mul,2)
        df["country"]=country
        df["created_at"]=datetime.now()
        df["updated_at"]=df["created_at"]
        df=df.replace(np.nan,None)
        df=df.fillna('')
        df=df.drop_duplicates()
        df['product_price'] = df['product_price'].astype(float)
    except Exception as e:
        print(RED,"Error",e)
        print('There IS some Issue in transformation.',RESET)
        exit()

    # Establishing the connection
    db_config = get_db_config()
    connection = pymysql.connect(
            host=db_config['host'],
            user=db_config['user'],
            password=db_config['passwd'],
            database=db_config['database'],
            port=db_config['port']
        )

    table_name='brands_data'
    try:
        with connection.cursor() as cursor:
            # Creating table if it does not exist
            create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                {', '.join([f'{col} TEXT' for col in df.columns])}
            )
            """
            cursor.execute(create_table_query)
            # Deleting data from table based on brand_name and country
            delete_query = f"DELETE FROM {table_name} WHERE brand_name = %s AND country = %s"
            cursor.execute(delete_query, (brand_name, country))
            # Inserting data into table
            insert_query = f"INSERT INTO {table_name} ({', '.join(df.columns)}) VALUES ({', '.join(['%s'] * len(df.columns))})"
            cursor.executemany(insert_query, df.values.tolist())
        
        # Committing the transaction
        connection.commit()
        print('Data load in DB successfully.')
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally:
        connection.close()

def get_currency_symbol_for_db(x):
    dic={
        'JPY':'YEN',
        'EUR':'EURO'
        }
    if x in dic.keys():
        return dic[x]
    else:
        return x
def get_currency_symbol_via_country(country,symbol):
    dic={'Norway':'NOK',
         'Sweden':'SEK',
         }
    if country in dic.keys():
        return dic[country]
    else:
        return symbol
    
def adjust_prices(row):
    pl = [row['product_price'],row['discounted_price']]
    pl.sort()
    row['discounted_price'], row['product_price'] = pl
    if row['discounted_price']==row['product_price']:
        row['discounted_price']=''
    return row
def normalize_text(text):
    # Replace &nbsp; with a newline
    text = text.replace('&nbsp;', '\n')
    
    text = text.replace('&rdquo;', 'inches ')
    # Remove HTML tags
    text = re.sub(r'<.*?>', ' ', text)
    
    # Replace other common HTML entities with spaces
    text = re.sub(r'&amp;|&lt;|&gt;|&quot;|&#39;', ' ', text)
    
    # Replace multiple spaces with a single space
    text = re.sub(r'\s{2,}', ' ', text)
    
    # Replace multiple newlines with a single newline
    text = re.sub(r'\n+', '\n', text)
    
    # Remove spaces before or after newlines
    text = re.sub(r'\s*\n\s*', '\n', text)
    
    # Remove any leading or trailing whitespace
    text = text.strip()

    return text

def replace_tags(html_content, replacements):
    """
    Replaces specified HTML tags in the content with their corresponding replacements.
    
    Args:
        html_content (str): The HTML content to process.
        replacements (dict): A dictionary where keys are HTML tags to replace and values are their replacements.

    Returns:
        str: The content with specified HTML tags replaced.
    """
    for tag, replacement in replacements.items():
        # Create a regex pattern to match the HTML tag
        tag_pattern = re.compile(rf'<{tag}\s*/?>|</{tag}>', re.IGNORECASE)
        html_content = tag_pattern.sub(replacement, html_content)
    
    # Remove any remaining HTML tags
    clean_text = re.sub(r'<.*?>', '', html_content)
    return clean_text.strip()


def get_values_between_string(t1, t2, text, find_word,remove=False):
    """
    Extracts and evaluates a substring between two delimiters (t1 and t2) that follows a specified word (find_word).

    Args:
        t1 (str): The starting delimiter.
        t2 (str): The ending delimiter.
        text (str): The text to search within.
        find_word (str): The word to find before extracting the substring.

    Returns:
        Any: The evaluated result of the extracted substring, or None if an error occurs.
    """
    try:
        # Find the index of the first occurrence of find_word in the text
        first_index = text.index(find_word)
        
        # Slice the text to start from the find_word
        text = text[first_index:]
        
        # Find the first occurrence of t1 after find_word
        start_index = text.index(t1)
        text = text[start_index:]
        
        count_t1 = 0
        count_t2 = 0
        
        # Iterate through the text to find the matching t1 and t2
        for i in range(len(text)):
            # If the counts of t1 and t2 match and t1 has been encountered at least once, break the loop
            if count_t1 == count_t2 and count_t1 != 0:
                break
            
            # Increment count_t1 if the current character is t1
            if text[i] == t1:
                count_t1 += 1
            
            # Increment count_t2 if the current character is t2
            if text[i] == t2:
                count_t2 += 1
        
        # Extract the text between the delimiters and replace JSON-like values with Python equivalents
        text = text[:i].replace('null', 'None').replace('false', 'False').replace('true', 'True')
        if remove:
            text=text[1:-1]
        try:
            # Evaluate and return the extracted text
            return eval(text)
        except:
            print("Issue in EVAL. So return Text only")
            return text
    
    except ValueError as ve:
        # Handle ValueError, e.g., when find_word is not found in the text
        print(f"ValueError: {ve}")
        return None
    except SyntaxError as se:
        # Handle SyntaxError, e.g., if eval encounters a syntax error
        print(f"SyntaxError: {se}")
        return None
    except Exception as e:
        # Handle any other exceptions
        print(f"An error occurred: {e}")
        return None
def get_all_values_between_string(t1, t2, text, find_word,remove=False):
    """
    Extracts and evaluates all substrings between two delimiters (t1 and t2) that follow each occurrence of a specified word (find_word).

    Args:
        t1 (str): The starting delimiter.
        t2 (str): The ending delimiter.
        text (str): The text to search within.
        find_word (str): The word to find before extracting substrings.

    Returns:
        List[Any]: A list of evaluated results of the extracted substrings, or an empty list if no results are found or an error occurs.
    """
    results = []

    # Count occurrences of find_word
    find_word_count = text.count(find_word)

    for _ in range(find_word_count):
        # Call the existing function to get values
        value = get_values_between_string(t1, t2, text, find_word,remove)
        if value is not None:
            results.extend(value if isinstance(value, list) else [value])
        
        # Remove the processed segment and find the next occurrence
        start_index = text.find(find_word)
        if start_index != -1:
            text = text[start_index + len(find_word):]
        else:
            break
    
    return results


def get_values_by_xpath(html_content, url_xpath):
    """
    Extracts URLs from an HTML response using a specified XPath expression.

    Args:
        response (requests.Response): The HTTP response object containing the HTML content.
        url_xpath (str): The XPath expression to find the desired URLs.

    Returns:
        list: A list of URLs extracted from the HTML content.
    """
    # Decode the response content to a string
    # This converts the raw bytes of the response content into a string
    
    # Parse the HTML content
    # This creates an element tree from the HTML content which can be queried using XPath
    tree = html.fromstring(html_content)
    
    # Extract URLs using the provided XPath expression
    # The XPath expression is used to find all matching elements and their href attributes
    urls = tree.xpath(url_xpath)
    
    return urls


def get_value_from_dict(data, keys):
    """
    Extracts a value from a dictionary based on a list of keys.

    Args:
        data (dict): The dictionary to traverse.
        keys (list): A list of keys to traverse the dictionary.

    Returns:
        The extracted value from the dictionary or None if not found.
    """
    try:
        for key in keys:
            data = data[key]
        return data
    except (KeyError, TypeError) as e:
        print(f"An error occurred: {e}")
        return None


def get_values_by_json(json_data, dic_values):
    """
    Extracts a list of URLs from a JSON response based on a list of keys.

    Args:
        response (requests.Response): The HTTP response object containing the JSON content.
        dic_values (list): A list of keys to traverse the JSON data.

    Returns:
        A list of extracted URLs from the JSON data or an empty list if not found.
    """
    try:
        
        # Initialize the list to hold extracted URLs
        values = []
        
        # Iterate over each dictionary in the JSON list
        for item in json_data:
            val = get_value_from_dict(item, dic_values)
            if val is not None:
                values.append(val)
        
        return values
    
    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        # Handle possible exceptions and return an empty list
        print(f"An error occurred: {e}")
        return []



def extract_text_for_dic(dic, replacements={}, list_of_not_wanted_keys=[]):
    """
    Extracts and cleans the descriptions from the given dictionary, excluding specified keys.
    
    Args:
        dic (dict): The dictionary containing description data.
        replacements (dict): A dictionary where keys are HTML tags to replace and values are their replacements.
        list_of_not_wanted_keys (list): A list of keys to exclude from processing.
    
    Returns:
        str: Concatenated descriptions or None if not available.
    """
    if dic:
        list_of_descriptions = []
        
        for key, value in dic.items():
            if key in list_of_not_wanted_keys:
                continue  # Skip the keys that are not wanted
            
            if isinstance(value, list):
                if value:
                    # Join list items with spaces
                    clean_list_content = ' '.join([str(item) for item in value])
                    list_of_descriptions.append(f"{key}: {replace_tags(clean_list_content, replacements)}")
                else:
                    # Convert empty list to a space
                    list_of_descriptions.append(f"{key}: {' '}")
            elif not isinstance(value, bool) and value is not None:
                list_of_descriptions.append(f"{key}: {replace_tags(value, replacements)}")
        
        return '\n'.join(list_of_descriptions) if list_of_descriptions else None
    else:
        return None


def get_exchange_rate(from_currency: str) -> float:
    if from_currency=='USD':
        return 1
    url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
    response = requests.get(url)
    to_currency='USD'
    if response.status_code == 200:
        data = response.json()
        if to_currency in data['rates']:
            return data['rates'][to_currency]
        else:
            raise ValueError(f"Currency {to_currency} not found in exchange rates.")
    else:
        raise ConnectionError(f"Failed to get exchange rates: {response.status_code}")

def get_currency_code(symbol):
    currency_symbols = {
        "$": "USD",
        "€": "EUR",
        "£": "GBP",
        "¥": "JPY",
        "₹": "INR",
        "₽": "RUB",
        "₩": "KRW",
        "₪": "ILS",
        "₫": "VND",
        "฿": "THB",
        "₴": "UAH",
        "₦": "NGN",
        "R$": "BRL",
        "A$": "AUD",
        "C$": "CAD",
        "NZ$": "NZD",
        "HK$": "HKD",
        "S$": "SGD",
        "CHF": "CHF",
        "ZAR": "ZAR",
        "TL":"TRY",
        "kr": "DKK", 
        "zł": "PLN",
        "SGD":"SGD",
        "MX$":"MXN",
        "C¥":'CNY',
    }
    return currency_symbols.get(symbol)
def convert_string_for_eval(x):
    return (x
        .replace('null', 'None')      # Replace JavaScript null with Python None
        .replace('false', 'False')    # Replace JavaScript false with Python False
        .replace('true', 'True')      # Replace JavaScript true with Python True
        .replace('undefined', 'None') # Replace JavaScript undefined with Python None
        .replace('NaN', 'float("nan")')  # Replace JavaScript NaN with Python NaN
        .replace('Infinity', 'float("inf")')  # Replace JavaScript Infinity with Python Infinity
        .replace('function', 'lambda')  # Replace JavaScript functions with Python lambdas (basic cases)
        .replace('var ', '')  # Remove JavaScript var keyword
        .replace('let ', '')  # Remove JavaScript let keyword
        .replace('const ', '')  # Remove JavaScript const keyword
        .replace('new ', '')  # Remove JavaScript new keyword (for object creation)
        .replace('console.log', '')  # Remove JavaScript console.log calls
    )
def fetch_proxies(country_code='ALL'):
    print('Proxy collecting')
    with open(common_lib_path+'\\token_webshare.txt', 'r') as file:
        token = file.read()
    response = requests.get(
        "https://proxy.webshare.io/api/v2/proxy/list/?mode=direct&page=1&page_size=100",
        headers={"Authorization": f"Token {token}"}
    )
    data = response.json()
    proxies = []

    for item in data['results']:
        if country_code=='ALL':
            proxy = f"http://{item['username']}:{item['password']}@{item['proxy_address']}:{item['port']}"
            proxies.append(proxy)
        else:
            if item['country_code']==country_code:
                proxy = f"http://{item['username']}:{item['password']}@{item['proxy_address']}:{item['port']}"
                proxies.append(proxy)

    print('Proxy collecting Done')
    
    # Save the proxies to a file or update the Scrapy settings directly
    return proxies


def create_proxyauth_extension(proxy_host, proxy_port, proxy_username, proxy_password, scheme='http', plugin_path=None):
    if plugin_path is None:
        plugin_path = 'proxyauth_plugin.zip'

    manifest_json = """
    {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Proxy Auth Plugin",
        "permissions": [
            "proxy",
            "tabs",
            "unlimitedStorage",
            "storage",
            "<all_urls>",
            "webRequest",
            "webRequestBlocking"
        ],
        "background": {
            "scripts": ["background.js"]
        },
        "minimum_chrome_version": "22.0.0"
    }
    """

    background_js = f"""
    var config = {{
            mode: "fixed_servers",
            rules: {{
            singleProxy: {{
                scheme: "{scheme}",
                host: "{proxy_host}",
                port: parseInt({proxy_port})
            }},
            bypassList: ["localhost"]
            }}
        }};
    chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{}});
    function callbackFn(details) {{
        return {{
            authCredentials: {{
                username: "{proxy_username}",
                password: "{proxy_password}"
            }}
        }};
    }}
    chrome.webRequest.onAuthRequired.addListener(
                callbackFn,
                {{urls: ["<all_urls>"]}},
                ['blocking']
    );
    """

    with zipfile.ZipFile(plugin_path, 'w') as zp:
        zp.writestr('manifest.json', manifest_json)
        zp.writestr('background.js', background_js)

    return plugin_path


def create_firefox_proxy_auth_extension(proxy_host, proxy_port, proxy_username, proxy_password):
    """Create a Firefox proxy authentication extension."""
    manifest_json = """
    {
        "manifest_version": 2,
        "version": "1.0.0",
        "name": "Firefox Proxy Auth Extension",
        "permissions": [
            "proxy",
            "webRequest",
            "webRequestBlocking",
            "<all_urls>"
        ],
        "background": {
            "scripts": ["background.js"]
        },
        "minimum_chrome_version": "22.0"
    }
    """

    background_js = f"""
    var config = {{
        mode: "fixed_servers",
        rules: {{
            singleProxy: {{
                scheme: "http",
                host: "{proxy_host}",
                port: parseInt({proxy_port})
            }},
            bypassList: ["localhost"]
        }}
    }};
    chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{}});
    function callbackFn(details) {{
        return {{
            authCredentials: {{
                username: "{proxy_username}",
                password: "{proxy_password}"
            }}
        }};
    }}
    chrome.webRequest.onAuthRequired.addListener(
        callbackFn,
        {{urls: ["<all_urls>"]}},
        ["blocking"]
    );
    """

    plugin_path = os.path.join(os.getcwd(), 'firefox_proxy_auth_plugin.zip')
    
    with zipfile.ZipFile(plugin_path, 'w') as zp:
        zp.writestr("manifest.json", manifest_json)
        zp.writestr("background.js", background_js)
    
    return plugin_path
def launch_browser(proxy=None,
                   headless=False, 
                   browser_type='chrome'):
    if browser_type == 'chrome':
        chrome_options = ChromeOptions()
        if headless:
            chrome_options.add_argument('--headless')  # Optional: run in headless mode
        chrome_options.add_argument('--no-sandbox')  # Optional: required for headless mode on some systems
        chrome_options.add_argument('--disable-dev-shm-usage')  # Optional: to overcome resource limitations
        
        if proxy:
            proxy_details = proxy.split('@')
            credentials, proxy_address = proxy_details[0], proxy_details[1]
            username_password = credentials.replace('http://', '').split(':')
            username, password = username_password[0], username_password[1]
            ip_port = proxy_address.split(':')
            ip, port = ip_port[0], ip_port[1]

            # Create proxy auth extension
            plugin_path = create_proxyauth_extension(ip, port, username, password)
            chrome_options.add_extension(plugin_path)
        
        service = ChromeService(f'{base_path}/common_lib/chromedriver.exe')
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver

    elif browser_type == 'firefox':
        firefox_options = FirefoxOptions()
        if headless:
            firefox_options.add_argument('--headless')  # Run in headless mode
        
        if proxy:
            proxy_details = proxy.split('@')
            credentials, proxy_address = proxy_details[0], proxy_details[1]
            username_password = credentials.replace('http://', '').split(':')
            username, password = username_password[0], username_password[1]
            ip_port = proxy_address.split(':')
            ip, port = ip_port[0], ip_port[1]

            # Create proxy auth extension
            plugin_path = create_firefox_proxy_auth_extension(ip, port, username, password)
            firefox_options.set_preference("network.proxy.type", 1)
            firefox_options.set_preference("network.proxy.http", ip)
            firefox_options.set_preference("network.proxy.http_port", int(port))
            firefox_options.set_preference("network.proxy.ssl", ip)
            firefox_options.set_preference("network.proxy.ssl_port", int(port))
            firefox_options.set_preference("network.proxy.socks", ip)
            firefox_options.set_preference("network.proxy.socks_port", int(port))
            firefox_options.set_preference("network.proxy.socks_remote_dns", True)
            firefox_options.set_preference("network.proxy.no_proxies_on", "")

            # Add the proxy auth extension
            firefox_options.add_argument(f"-profile {plugin_path}")
        
        service = FirefoxService(f'{base_path}/common_lib/geckodriver.exe')
        driver = webdriver.Firefox(service=service, options=firefox_options)
        return driver
    else:
        raise ValueError(f"Unsupported browser_type: {browser_type}")



def wait_for_element_by_xpath(driver, xpath, timeout=60):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.XPATH, xpath))
    )


def get_response_with_browser(list_of_proxies:list = [None],
                              url=None,
                              xpath_for_wait : str ='//div',
                              time_wait=0.01,
                              headless=False,
                              browser_type='chrome'):
        proxy = random.choice(list_of_proxies)
        driver = launch_browser(proxy=proxy,
                                headless=headless,
                                browser_type=browser_type)
        if type(url)==str:
            driver.get(url)
            time.sleep(time_wait)
            wait_for_element_by_xpath(driver,xpath_for_wait )
            response = driver.page_source
            driver.quit()
            response = Selector(text=response)
            return response
        elif type(url)==list:
            response_list=[]
            for u in url:
                driver.get(u)
                time.sleep(time_wait)
                wait_for_element_by_xpath(driver,xpath_for_wait )
                response = driver.page_source
                response = Selector(text=response)
                response_list.append(response)
            driver.quit()
            return response_list
        
def save_response(response):
    with open('response.html', 'w', encoding='utf-8') as file:
            file.write(response.text)
    
def get_cookies_with_browser(url,headless=False,proxy=None):
    driver=launch_browser(headless=headless,proxy=proxy)
    driver.get(url)
    driver.implicitly_wait(5)
    cookies = driver.get_cookies()
    driver.quit()
    return cookies

def find_key_path(json_obj, target_key, current_path=None):
    if current_path is None:
        current_path = []

    if isinstance(json_obj, dict):
        for key, value in json_obj.items():
            if key == target_key:
                return current_path + [key]
            elif isinstance(value, (dict, list)):
                result = find_key_path(value, target_key, current_path + [key])
                if result is not None:
                    return result

    elif isinstance(json_obj, list):
        for index, item in enumerate(json_obj):
            result = find_key_path(item, target_key, current_path + [index])
            if result is not None:
                return result

    return None
def find_all_key_paths(json_obj, target_key, current_path=None):
    if current_path is None:
        current_path = []

    paths = []

    if isinstance(json_obj, dict):
        for key, value in json_obj.items():
            if key == target_key:
                paths.append(current_path + [key])
            elif isinstance(value, (dict, list)):
                paths.extend(find_all_key_paths(value, target_key, current_path + [key]))

    elif isinstance(json_obj, list):
        for index, item in enumerate(json_obj):
            paths.extend(find_all_key_paths(item, target_key, current_path + [index]))

    return paths


def get_db_config():
    with open(common_lib_path+'\\db_config.txt') as base_file:
        config = base_file.read()
    return eval(config)


def script_config_data(brand,country,test=False):
    brand=brand.replace('_',' ')
    print("Brand Name::>>",brand)
    print("Country ::>>",country)
    # Define your database connection parameters
    db_config = get_db_config()
    connection = pymysql.connect(
            host=db_config['host'],
            user=db_config['user'],
            password=db_config['passwd'],
            database=db_config['database'],
            port=db_config['port']
        )

    try:
        with connection.cursor() as cursor:
            # Define the SQL query to fetch the configuration data
            sql_query = f"SELECT product_category,category_link FROM brands_links WHERE brand_name=%s and country=%s"

            # Execute the query with the provided db_id
            cursor.execute(sql_query,(brand,country))

            # Fetch the row from the executed query
            result = cursor.fetchall()
            data= list(result)
            scraping_json = {}
            print("Total Len of files founded::>>",len(data))
            assert len(data)!=0,"Data Not Found"
            # Process each row in the data
            for category_type, url in data:
                # Split the category_type into words
                words = category_type.split()

                # The first word is the category, the rest is the product type
                category = words[0]
                product_type = ' '.join(words[1:])

                # Initialize the category in the dictionary if not already present
                if category not in scraping_json:
                    scraping_json[category] = {}

                # Add the product type and URL to the corresponding category
                scraping_json[category][product_type] = url
                if test:
                    break

            # Check if result is not None

            

            return scraping_json
            
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    finally:
        # Close the database connection
        connection.close()


def get_db_data(brand,country,table_name):
    db_config = get_db_config()
    connection = pymysql.connect(
            host=db_config['host'],
            user=db_config['user'],
            password=db_config['passwd'],
            database=db_config['database'],
            port=db_config['port']
        )
    with connection.cursor() as cursor:
        # Define the SQL query to fetch the configuration data
        if country=='all':
            sql_query = f"SELECT * FROM {table_name} WHERE brand_name=%s" 
            cursor.execute(sql_query,(brand))
        else:   
            sql_query = f"SELECT * FROM {table_name} WHERE brand_name REGEXP %s AND country = %s"
            cursor.execute(sql_query,(brand,country))

        # Fetch column names
        column_names = [desc[0] for desc in cursor.description]

        # Fetch all rows of the query result
        result = cursor.fetchall()

        # Combine column names with data
        data = [dict(zip(column_names, row)) for row in result]
        df = pd.DataFrame(data)
        return df
    
def get_qc_data(brand,country='all'):    
    brands_data=get_db_data(brand,country,'brands_data')
    brands_links=get_db_data(brand,country,'brands_links')
    brands_links.columns
    brands_links['cat']=brands_links['product_category']
    brands_data['cat'] = brands_data['product_category'] + ' ' + brands_data['product_type']
    group_df = brands_data.groupby(by=['cat'],as_index=False).size()
    result_df = group_df.merge(brands_links,on='cat',how='outer')
    return result_df[['brand_name','country','cat','category_link','manual_count','size']]


        