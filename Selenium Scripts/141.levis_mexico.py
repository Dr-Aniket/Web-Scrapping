statsData = {}

chrome = False
chrome = True

if chrome:
    from selenium.webdriver.chrome.options import Options
else:
    from selenium.webdriver.firefox.options import Options
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import requests
import pymysql
from selenium.webdriver.common.by import By
import urllib.parse
from selenium.webdriver.common.action_chains import ActionChains
import requests
import time
sleep = time.sleep
from threading import Thread, Event
import re
from common import Common
from fake_useragent import UserAgent
import traceback
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
links = main_urls = scrapping_urls = main_url = urls = get_db_links(connection,'levi','mexico')

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

productsXpath = '//a[@class="vtex-product-summary-2-x-clearLink h-100 flex flex-column"]'

def addData(list_for_upload):
    try:
        with connection.cursor() as cursor:
            sql = """INSERT INTO `brands_data` (`brand_name`, `product_link`, 
            `product_name`, `product_category`, `product_type`, `product_price`, 
            `discounted_price`, `price_unit`, `price_usd`, `product_description`, 
            `product_image`, `country`, `page_numer`) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            cursor.execute(sql, list_for_upload)

        connection.commit()

    except Exception as e:
        print(e)

from bs4 import BeautifulSoup
def get_data(element):
    html = element.get_attribute('innerHTML')
    soup = BeautifulSoup(html, 'html.parser')
    data = soup.get_text("\n", strip=True)
    return data + '\n'

def scroll_to_end():
    h = driver.execute_script("return document.body.scrollHeight")
    for i in range(0,h,h//20):
        driver.execute_script(f"window.scrollBy(0, {i});")
        sleep(0.5)

def scroll_down(pixels):
    for i in range(1, pixels, 10):
        driver.execute_script(f"window.scrollBy(0, {i});")
        sleep(0.01)
    sleep(0.5)

def quitDriver():
    global driver
    try:
        driver.quit()
    except:
        pass

def upload_data_into_db(url,pro_category,pro_type):
    global driver
    try:
        quitDriver()
        driver = setup()
        driver.get(url)
        time.sleep(10)
        print('Product URL: >>',url)

        try:
            name = driver.title.split('|')[0].strip()
            name = translate(name)
        except:
            name = ''
        print("Name: >>",name)
        
        try:
            image = driver.find_element(By.XPATH,'//meta[@property="og:image"]').get_attribute('content')
        except:
            image=''
        print("Image: >>",image)
        try:
            price_ele=driver.find_element(By.XPATH,'//div[contains(@class,"price items")]').text
            price_list=price_ele.split('$')
            if len(price_list)>2:
                old_price=eval(price_list[-1].split(' ')[0].replace(',',''))
                new_price=eval(price_list[1].replace(',',''))
                if old_price<new_price:
                    old_price,new_price=new_price,old_price
            else:
                old_price=eval(price_list[1].replace(',',''))
                new_price=''
        except:
            raise Exception("Price Not Found")
        
        print("Price: >>",old_price)
        print("Discounted Price: >>",new_price)
        
        h = driver.execute_script("return document.body.scrollHeight")
        scroll_down(int(h*0.8))

        for i in range(5):
            try:
                description = get_data(driver.find_element(By.XPATH,"//*[contains(@class,'pdp-details')]"))
                break
            except Exception as e:
                sleep(5)
        else:
            # print(f'Error in Description: {e}')
            description = ''
        description = translate(description)
        print("Description: >>",description)

        list_for_upload=[com_name,url,name,pro_category,
                        pro_type,old_price,new_price,'MXN',
                        round(old_price*cur_mul,2),description,image,country,'']

        addData(list_for_upload)
        print('Product Added')
        print('-'*50)
        statsData[typ]["products_inserted"] += 1
    except Exception as e:
        traceback.print_exc()
        print(f'Error: {e}')
        quitDriver()
        driver = setup()
        
com_name='LEVI STRAUSS AND CO.'
country='Mexico'

def load(driver,url):
    driver.get(url)
    time.sleep(10)
    print('URL:: >> ',url)
    try:
        time.sleep(2)
        driver.find_element(By.XPATH,'//button[contains(@id,"onetrust-accept")]').click()
    except:
        pass
    try:
        driver.find_element(By.XPATH,'//div[@title="Close"]').click()
    except:
        pass
    try:
        driver.find_element(By.XPATH,'//div[@title="Close"]').click()
    except:
        pass
    try:
        ele = driver.find_element(By.CLASS_NAME,'levimx-custom-newsletter-1-x-modal_wrapper')
        driver.execute_script(f"arguments[0].remove()",ele)
    except:
        pass
def quitDriver():
    global driver
    try:
        driver.quit()
    except:
        pass
def setup():
    global action
    user = UserAgent().random
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
    options.add_argument(f"user-agent={user}")
    if chrome:
        driver = webdriver.Chrome(options=options)
    else:
        driver = webdriver.Firefox(options=options)
    driver.maximize_window()
    action = ActionChains(driver)

    return driver

cur_mul = functions.get_conversion_rate('MXN','USD')
from random import shuffle
count_pro=1
for typ in main_url:
    try:
        quitDriver()
        driver = setup()
        pro_cat,pro_type = typ.split(' ',1)
        print(typ,' >>>>>>>>> START')
        url = main_url[typ]
        
        load(driver, url)
        
        list_of_pro_urls = []
        try:
            number_products = eval(driver.find_element(By.XPATH,'//div[contains(@class,"totalProducts")]/span').text.split(' ')[0])
            print(f'Number of Expected Products: {number_products}')
        except:
            number_products = None

        page = 1
        while page:
            try:
                print(f'Page: {page}')
                scroll_to_end()

                load_more = driver.find_element(By.XPATH,"//button[@class='vtex-button bw1 ba fw5 v-mid relative pa0 lh-solid br2 min-h-small t-action--small bg-action-primary b--action-primary c-on-action-primary hover-bg-action-primary hover-b--action-primary hover-c-on-action-primary pointer ']")
                
                driver.execute_script("arguments[0].click()",load_more)
                sleep(3)
                driver.execute_script("window.scrollTo(0, 0);")
                sleep(2)
                page += 1
            except:
                break

        products = driver.find_elements(By.XPATH,productsXpath)
        list_of_pro_urls = [product.get_attribute('href') for product in products]

        print(f'Total Products in {pro_cat} {pro_type}: {len(list_of_pro_urls)}')
        list_of_pro_urls = list(set(list_of_pro_urls))
        print(f'Total Unique Products in {pro_cat} {pro_type}: {len(list_of_pro_urls)}')
        statsData[typ] = {'total_unique_products': len(list_of_pro_urls),'products_inserted': 0,'url': url}

        shuffle(list_of_pro_urls)
        for pro_url in list_of_pro_urls[::-1]:
            print('\nProduct Number',count_pro)
            count_pro+=1
            upload_data_into_db(pro_url,pro_cat,pro_type)

    except Exception as e:
        print(f'Error in {typ}: {e}')
        print(f'SKIPPING {typ}')
        # traceback.print_exc()

print('Congratulations LEVI STRAUSS AND CO. Mexico Scraping is Complete.')

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
input(finalReportString)