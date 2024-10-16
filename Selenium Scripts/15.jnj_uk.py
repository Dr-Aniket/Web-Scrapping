statsData = {}

chrome = False
chrome = True

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import pymysql
from selenium.webdriver.common.by import By
if chrome:
    from selenium.webdriver.chrome.options import Options
else:
    from selenium.webdriver.firefox.options import Options
import urllib.parse
from selenium.webdriver.common.action_chains import ActionChains
import requests
import time
sleep = time.sleep
from threading import Thread, Event
import re
from googletrans import Translator
translator = Translator()
from common import Common
import random
from langdetect import detect
import functions 
from urllib.parse import quote
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

from config import db_config
connection = pymysql.connect(host=db_config["host"], user=db_config["user"], passwd=db_config["passwd"],database=db_config["database"], port=db_config["port"])
from db_links import *
links = main_urls = scrapping_urls = main_url = urls = get_db_links(connection,'jack','UK')


def get_price(value):
    if value:
        value = value.replace(',','').replace(' ','')
        value = re.search(r'\d+.\d+',value).group()
        value = eval(value)
    return value

def addData(connect, uploadEntry,TRY = 3):
    global connection

    connection = connect
    try:
        with connection.cursor() as cursor:
            sql = """INSERT INTO `brands_data` (`brand_name`, `product_link`, 
            `product_name`, `product_category`, `product_type`, `product_price`, 
            `discounted_price`, `price_unit`, `price_usd`, `product_description`, 
            `product_image`, `country`, `page_numer`) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            cursor.execute(sql, uploadEntry)

        connection.commit()

        return True

    except Exception as e:
        print(e)
        if TRY:
            connection = pymysql.connect(host=db_config["host"], user=db_config["user"], passwd=db_config["passwd"],database=db_config["database"], port=db_config["port"])
            return addData(connection, uploadEntry,TRY-1)
        print(f'Product Not Added')
        raise Exception('Product Not Added')

from bs4 import BeautifulSoup
def get_data(element):
    html = element.get_attribute('innerHTML')
    soup = BeautifulSoup(html, 'html.parser')
    data = soup.get_text("\n", strip=True)
    return data + '\n'

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
    
    prices = re.findall(r'\d+\.?\d*',html.replace(',',''))
    prices = [get_price(price) for price in prices]
    prices.sort()
    new_price, price = setPrices(prices[0],prices[-1])
    if new_price == price:
        new_price = 0

    return new_price, price

def upload_data_into_db(url,pro_category,pro_type):
    try:
        driver.get(url)
        time.sleep(10)
        print(url)

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        sleep(1)
        driver.execute_script("window.scrollTo(0, 0);")
        sleep(1)

        try:
            name = driver.find_element(By.XPATH, '//meta[@property="og:title"]').get_attribute("content").split('|')[0]
        except:
            name = ''

        print('Name: ',name)

        try:
            image = driver.find_element(By.XPATH,'//meta[@property="og:image"]').get_attribute("content").split('&crop=')[0]
        except:
            image = ''
        print('Image URL: ',image)

        try:
            priceElement = driver.find_element(By.XPATH,'//div[contains(@class,"product-price")]')
            new_price, old_price = getPrices(get_data(priceElement))
        except:
            raise Exception('No Price Found')

        print("Price >> ", old_price)
        print("Discounted Price >> ", new_price)
        
        try:
            description = get_data(driver.find_element(By.XPATH,'//*[@id="__layout"]/div/main/div/div/article[2]/div[6]'))
        except:
            description = ''

        print('Description: ',description)
    
        list_for_upload=[com_name,url,name,pro_category,
                        pro_type,old_price,new_price,'GBP',
                        round(old_price*cur_mul,2),description,image,country,'']

        addData(connection,list_for_upload)
        print('Product Added')
        statsData[typ]['products_inserted'] += 1
    except Exception as e:
        print(e)
        pass

com_name='Jack and Jones'
country='UK'
cur_mul = functions.get_conversion_rate('GBP', 'USD')

def setup():
    global action
    options = Options()
    options.add_argument("--window-size=1920,1080");
    options.add_argument("--no-sandbox");
    options.add_argument("--headless");
    options.add_argument("--disable-gpu");
    options.add_argument("--disable-crash-reporter");
    options.add_argument("--disable-extensions");
    options.add_argument("--disable-in-process-stack-traces");
    options.add_argument("--disable-logging");
    options.add_argument("--disable-dev-shm-usage");
    options.add_argument("--log-level=3");
    options.add_argument("--output=/dev/null");

    if chrome:
        driver = webdriver.Chrome(options=options)
    else:
        driver = webdriver.Firefox(options=options)
    driver.maximize_window()
    action = ActionChains(driver)

    return driver

count_pro=1
for typ in main_urls:
    driver=setup()
    def scroll_down(pixels):
        for i in range(1, pixels, 10):
            driver.execute_script(f"window.scrollBy(0, {i});")
            sleep(0.01)

    url=main_urls[typ]
    print(typ,'URL:>',url)
    driver.get(url)
    time.sleep(20)
    pro_cat, pro_type = typ.split(' ',1)
    try:
        driver.find_element(By.XPATH,'//button[@id="onetrust-reject-all-handler"]').click()
    except:
        pass
    time.sleep(10)
    try:
        iframe=driver.find_element(By.XPATH,'//span[contains(@id,"forme")]/iframe')
        driver.switch_to.frame(iframe)
        driver.find_element(By.XPATH,'//div[@data-id="Element187"]').click()
        time.sleep(2)
        driver.switch_to.default_content()
    except:
        pass
    
    driver.switch_to.default_content()
    try:
        driver.find_element(By.XPATH,'//span[contains(text(),"Reject All")]').click()
    except:
        pass

    sleep(5)

    try:
        counter = driver.find_element(By.XPATH, '//span[@class="counter"]')
        total = int(counter.text.split()[0])
        print(f'Total Expected Products: {total}')
    except:
        pass

    page_number=1
    products_list=[]
    products_no = []
    while page_number:
        h = driver.execute_script("return document.body.scrollHeight")
        scroll_down(h)
        sleep(1)
        products = driver.find_elements(By.XPATH,'//div[contains(@class,"product-tile-info")]//a')
        products = [a.get_attribute('href') for a in products]
        products_list.extend(list(products))
        products_no.append(len(set(products_list)))
        print(f'Products on page {page_number}: {len(products)}')

        if sum(products_no[-3:]) == 3*products_no[-1]:
            break

        try:
            load_more = driver.find_element(By.XPATH,'//li[@class="paginator__item paginator__item--arrow-right"]/a')
            driver.execute_script("arguments[0].click();", load_more)
            # load_more.click()
            page_number+=1
            sleep(5)
        except Exception as e:
            print(f'Error: {e}')
            break

    print(f'Total Product links found: {len(products_list)}')
    products_list = list(set(products_list))
    print(f'Total Unique Product links found: {len(products_list)}')
    statsData[typ] = {'total_unique_products': len(products_list),'products_inserted': 0,'url': url}

    for pro_url in products_list:
        print('Product Number',count_pro)
        count_pro+=1
        upload_data_into_db(pro_url,pro_cat,pro_type)

driver.close()
print('Congratulations Jack and Jones UK Scraping is Complete.')   

######################### REPORT GENERATION #########################

from reportGenerator import *

try:
    print(f'Table: {dbConfig["table"]}')
except:
    dbConfig = db_config
    
print(f'Table: {dbConfig["table"]}')

currentFileName = os.path.basename(__file__)

brand, country = com_name, country
data = makeDataFromDict(statsData, brand, country)

connection,cursor = connectToSqlDb()
insertDataInDb(connection, cursor, data, dbConfig['table'])
disconnectFromSqlDb(connection,cursor)
print(RESET)

finalReportString = getFinalDisplayString(statsData, currentFileName, brand, country)
print(finalReportString)