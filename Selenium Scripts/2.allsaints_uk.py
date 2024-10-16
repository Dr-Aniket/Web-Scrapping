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
import pymysql
import urllib.parse
from selenium.webdriver.common.action_chains import ActionChains
import requests
from fake_useragent import UserAgent
import time
sleep = time.sleep
from threading import Thread, Event
import re
from common import Common
import traceback
import random
from langdetect import detect
import functions 
from functions import *
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
links = main_urls = scrapping_urls = main_url = urls = get_db_links(connection,'saints','UK')

from bs4 import BeautifulSoup
def get_data(element):
    html = element.get_attribute('innerHTML')
    soup = BeautifulSoup(html, 'html.parser')
    data = soup.get_text("\n", strip=True)
    return data + '\n'

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

def addData(data):
    try:
        with connection.cursor() as cursor:
            sql = "INSERT INTO `brands_data` (`brand_name`, `product_link`, `product_name`, `product_category`, `product_type`, `product_price`, `discounted_price`, `price_unit`, `price_usd`, `product_description`, `product_image`, `country`, `page_numer`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            cursor.executemany(sql, data)

        connection.commit()

    except Exception as e:
        print(e)

def get_links():
    driver = setup()
    def click(element):
        try:
            driver.execute_script("arguments[0].click();", element)
            return True
        except:
            return False
        
    for typ, url in urls.items():

        print("*" * 40)
        print("URL >>> ", url)
        driver.get(url)
        sleep(10)
        
        try:
            driver.find_element(By.XPATH, '//button[contains(text(),"ACCEPT ALL")]').click()
        except:
            pass
        try:
            driver.find_element(By.XPATH, '//select[contains(@id,"countrySelector_country")]').click()

            driver.find_element(By.XPATH, '//option[@data-id="allsaints-uk-GB"]').click()
            sleep(2)
            driver.find_element(By.XPATH, '//*[contains(text(),"Confirm")]').click()
            sleep(2)
        except:
            pass

        sleep(10)
        try:
            close_buttons = driver.find_elements(By.XPATH, '//button[@class="b-dialog-close"]')
        except:
            pass
        for cb in close_buttons:
            try:
                driver.execute_script("arguments[0].click();",cb)
                sleep(0.2)
            except:
                continue
                
        try:
            driver.find_element(By.XPATH, '//*[contains(text(),"Accept all")]').click()
            sleep(2)
        except:
            pass
        
        elemets = driver.find_elements(By.XPATH, '//div[contains(@class,"b-load_more")]/a')
        for ele in elemets:
            click(ele)
            sleep(0.2)

        products = driver.find_elements(By.XPATH, '//a[contains(@class,"product_tile-image_link")]')
        print('Total products: ',len(products))
        links = [product.get_attribute("href") for product in products]
        links = list(set(links))
        print('Total unique products: ',len(links))
        statsData[typ] = {'total_unique_products': len(links) ,'products_inserted': 0,'url': url}
        for product_link in links:
            try:
                print("Link >> ", product_link)

                # driver.get(product_link)
                # sleep(5)

                script = f"window.open('{product_link}','_blank');"
                driver.execute_script(script)
                sleep(3)

                driver.switch_to.window(driver.window_handles[1])
                sleep(3)

                try:
                    driver.find_element(By.XPATH, "//span[@class='icon-ramskull_close popup-display']").click()
                except:
                    pass

                for i in range(10):
                    try:
                        title = driver.find_element(By.XPATH, '//h1[@class="b-product_details-name"]').text
                        break
                    except:
                        sleep(1)
                        continue
                else:
                    title = ''    
                print("Title >> ", title)

                image_url = driver.find_element(By.XPATH,'//img[@id="product-image-0"]').get_attribute("src")
                print("Image >> ", image_url)

                price_ele = driver.find_element(By.XPATH, '//div[@class="b-price"]').text
                if price_ele.count('£')>1:
                    price_list=price_ele.split('\n')
                    price=eval(price_list[1].replace('£',''))
                    dis_price=eval(price_list[-1].replace('£',''))

                else:
                    price_list=price_ele.split('\n')
                    price=eval(price_list[-1].replace('£',''))
                    dis_price=''

                print("Price >> ", price)
                print("Discounted Price >> ", dis_price)

                print("Loading Description")


                try:
                    driver.find_element(By.XPATH,'//*[@id="product-details-btn-1"]').click()
                except:
                    print("Not Clicked")
                    pass

                try:
                    details = driver.find_element(By.XPATH, '//*[@data-id="descriptions"]')
                    desc = get_data(details)
                except:
                    desc = ''

                desc = desc.split('RETURNS',1)[-1].replace('Toggle visibility','').split('Made in:')[0].strip()

                print(f'Description >> {desc}')
                
                ty = typ.split(" ",1)

                product_category = ty[0]
                product_type = ty[-1]

                driver.close()

                driver.switch_to.window(driver.window_handles[0])
                sleep(1)

                price_usd = str(round(float(price) * float(usd_rate), 2))
                print("Price USD >> ", price_usd)

                local = "GBP"

                e_data = ("All Saints Jeans", product_link, title, product_category, product_type,
                          price,dis_price, local, price_usd, desc.strip(), image_url,
                          "UK", "")
                addData([e_data])
                
                print('Product Added')
                print("-" * 35)
                statsData[typ]['products_inserted'] += 1
            
            except Exception as e:
                print(f'Error: [{e}]')
                continue
        
    driver.quit()

if __name__ == "__main__":
    usd_rate = functions.get_conversion_rate('gbp')
    get_links()

######################### REPORT GENERATION #########################

from reportGenerator import *

try:
    print(f'Table: {dbConfig["table"]}')
except:
    dbConfig = db_config
    
print(f'Table: {dbConfig["table"]}')

currentFileName = os.path.basename(__file__)

brand, country = "All Saints Jeans", "UK"
data = makeDataFromDict(statsData, brand, country)

connection,cursor = connectToSqlDb()
insertDataInDb(connection, cursor, data, dbConfig['table'])
disconnectFromSqlDb(connection,cursor)
print(RESET)

finalReportString = getFinalDisplayString(statsData, currentFileName, brand, country)
print(finalReportString)