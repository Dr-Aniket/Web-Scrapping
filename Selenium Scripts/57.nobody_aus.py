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
from googletrans import Translator
translator = Translator()
from common import Common
import traceback
from fake_useragent import UserAgent
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
links = main_urls = scrapping_urls = main_url = urls = get_db_links(connection,'nobody','aus')

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
    options.add_argument(f"user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.9999.999 Safari/537.36")
    if chrome:
        driver = webdriver.Chrome(options=options)
    else:
        driver = webdriver.Firefox(options=options)
    driver.maximize_window()
    action = ActionChains(driver)

    return driver

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

def get_links():
    driver = setup()
    for typ, url in urls.items():
        try:
            print("*" * 40)
            print("URL >>> ", url)
            driver.get(url)
            sleep(5)

            try:
                driver.find_element(By.XPATH, "//button[@class='needsclick klaviyo-close-form kl-private-reset-css-Xuajs1']").click()
                sleep(1)
            except:
                pass

            try:
                driver.find_element(By.XPATH, "//a[@class='cc-btn cc-dismiss']").click()
                sleep(1)
            except:
                pass

            while True:

                try:
                    temp = driver.find_element(By.XPATH, "//button[@class='btn btn-secondary px-8']")
                    action.move_to_element(temp)
                    action.perform()
                    sleep(5)
                    temp.click()
                    sleep(2)
                    print("Loading More Data...")
                except:
                    break

            products = driver.find_elements(By.XPATH, "//a[@class='flex flex-col'][1]")
            links = [product.get_attribute("href") for product in products]
            links = list(set(links))
            print("Total Products >> ", len(links))
            statsData[typ] = {'total_unique_products': len(links),'products_inserted': 0,'url': url}
        except Exception as e:
            print(f'Error in {typ}: {e}')
            
        for product_link in links:
            try:
                print("Link >> ", product_link)

                try:
                    ele = driver.find_element(By.XPATH, '//*[@id="nico-skinny-midnight-black"]/div[14]/div')
                    driver.execute_script("arguments[0].remove();", ele)
                except:
                    pass

                with requests.get(product_link, headers={"User-Agent": UserAgent().random}) as response:
                    soup = BeautifulSoup(response.content, "html.parser")

                    try:
                        title = soup.find("h1", {"class": "product-single__title"}).getText().strip()
                    except:
                        try:
                            title = soup.find("title").getText().strip()
                        except:
                            title = ""
                    print("Title >> ", title)

                    try:
                        prices_ele = soup.find("span", {"class": "product__price"}).getText().strip()
                    except:
                        raise Exception("PRICE NOT FOUND")
                    
                    dis_price, price = getPrices(prices_ele)
                    print("Price >> ", price)
                    print("Discount >> ", dis_price)

                    try:
                        image_url = soup.find("a", {"class": "zoom-js"})['href']
                        if 'http' not in image_url:
                            image_url = f'https:{image_url}'
                    except:
                        image_url = ''
                    print("Image >> ", image_url)

                    try:
                        desc1 = soup.find("div", {"class": "desktop-product-description"}).getText().strip()
                    except:
                        desc1 = ""
                    
                    try:
                        desc2 = soup.find_all("div", {"class": "product-info-hide"})[1].getText().strip()
                    except:
                        desc2 = ""
                    
                    desc = desc1 + '\n' + desc2

                    print(desc)

                ty = typ.split(" ", 1)

                product_category = ty[0]
                product_type = ty[-1]

                price_usd = str(round(float(price) * float(usd_rate), 2))
                # price_usd = price
                print("Price USD >> ", price_usd)

                local = "AUD"
                dis_price = ""

                e_data = ("Nobody Jeans", product_link, title, product_category, product_type,
                        price,
                        dis_price, local, price_usd, desc.strip(), image_url,
                        "Australia", "")

                Common.addData(Common.connection, [e_data])

                print("-" * 35)
                print("Data Added")
                print("-" * 35) 
                statsData[typ]["products_inserted"] += 1
            except:
                print(traceback.format_exc())
                continue

    driver.quit()

if __name__ == "__main__":
    usd_rate = functions.get_conversion_rate('aud', 'usd')
    try:
        get_links()
    except Exception as e:
        traceback.print_exc()
        print(f'ERROR: {e}')

######################### REPORT GENERATION #########################

from reportGenerator import *

try:
    print(f'Table: {dbConfig["table"]}')
except:
    dbConfig = db_config
    
print(f'Table: {dbConfig["table"]}')

currentFileName = os.path.basename(__file__)

brand, country = "Nobody Jeans", "Australia"
data = makeDataFromDict(statsData, brand, country)

connection,cursor = connectToSqlDb()
insertDataInDb(connection, cursor, data, dbConfig['table'])
disconnectFromSqlDb(connection,cursor)
print(RESET)

finalReportString = getFinalDisplayString(statsData, currentFileName, brand, country)
print(finalReportString)