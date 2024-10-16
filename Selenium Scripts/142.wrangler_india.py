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
import time
sleep = time.sleep
from threading import Thread, Event
from fake_useragent import UserAgent 
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
links = main_urls = scrapping_urls = main_url = urls = get_db_links(connection,'wrangler','india')

from bs4 import BeautifulSoup
def get_data(element):
    html = element.get_attribute('innerHTML')
    soup = BeautifulSoup(html, 'html.parser')
    data = soup.get_text("\n", strip=True)
    return data + '\n'

def get_price(value):
    if str(value).strip():
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

def quitDriver():
    global driver
    try:
        driver.quit()
    except:
        pass

def reset():
    global driver
    quitDriver()
    sleep(random.randint(1,4))
    driver = setup()
    return driver

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
    options.add_argument("--incognito");
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

def get_links():
    global driver
    for typ, url in scrapping_urls.items():
            driver = reset()
            statsData[typ] = {'total_unique_products': 0,'products_inserted': 0,'url': url}
            try:
                print("*" * 40)
                print("URL >>> ", url)
                driver.get(url)
                sleep(random.randint(5, 15))

                try:
                    total_number = eval(driver.find_element(By.XPATH, '//*[contains(@class,"plp-count")]').text.split()[0])
                    print('Total Expected Product Found',total_number)
                except:
                    pass

                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                sleep(1)

                try:
                    totalPages = driver.find_element(By.XPATH, '//*[contains(@class,"page_Count")]')
                    totalPages = get_data(totalPages)
                    totalPages = eval(re.findall(r'\d+',totalPages)[-1])
                except:
                    totalPages = 1
                    
                print(f'Toal Pages: {totalPages}')

                page = 1
                products = []
                links = []
                while page:
                    try:
                        products = driver.find_elements(By.XPATH, "//*[contains(@class,'prod-card')]//a")
                        links += [link.get_attribute("href") for link in products]
                        print(f'Links on page {page}: {len(links)}')
                        if page >= totalPages:
                            break

                        nextButton = driver.find_element(By.XPATH, '//*[contains(@class,"Next_button")]')
                        driver.execute_script("arguments[0].click();", nextButton)
                        sleep(5)
                        page += 1
                    except:
                        pass

                print("Total Links Found >>> ", len(links))
                links = list(set(links))
                print("Total Unique Links Found >>> ", len(links))
                statsData[typ]["total_unique_products"] += len(links)

            except Exception as e:
                print(f'Error in {typ}: {e}')
                print(f'SKIPPING {typ}')
                # traceback.print_exc()
                driver = reset()
            for link in links:
                try:
                    print("Link >> ", link)
                    try:
                        driver.get(link)
                        sleep(random.randint(3, 10))
                    except:
                        try:
                            driver.quit()
                        except:
                            pass
                        driver = setup()
                        driver.get(link)
                        sleep(random.randint(3, 10))

                    try:
                        title = driver.find_element(By.XPATH, "//*[contains(@class,'pdp-title')]/h1").get_attribute("textContent").strip()
                    except:
                        title = ''
                    print("Title >> ", title)

                    try:
                        try:
                            price = get_data(driver.find_element(By.XPATH, '//span[contains(@class,"line-through")]'))
                            dis_price = get_data(driver.find_element(By.XPATH, '//span[contains(@class,"pdp-price")]'))
                        except:
                            price = get_data(driver.find_element(By.XPATH, '//span[contains(@class,"pdp-price")]'))
                            dis_price = ""
                    except:
                        raise Exception("Price not found")
                    
                    price = get_price(price)
                    dis_price = get_price(dis_price)
                    dis_price, price = setPrices(dis_price, price)

                    print("Price >> ", price)
                    print("Discount >> ", dis_price)

                    # img
                    try:
                        image_url = driver.find_element(By.XPATH, '//*[contains(@class,"img-container")]/img').get_attribute("src").strip()
                    except:
                        image_url = ''

                    print("Image >> ", image_url)

                    # Desc
                    xpaths = ["//div[@class='col-lg-11']","//div[@class='row']","//div[@class='col']"]
                    desc = ''
                    for xpath in xpaths:
                        try:
                            desc += get_data(driver.find_elements(By.XPATH, xpath)[-1])    
                        except Exception as e:
                            # print(f'ERROR in DESC: {e}')
                            pass

                    print("Desc >> ", desc)

                    ty = typ.split(" ",1)

                    product_category = ty[0]
                    product_type = ty[-1]

                    price_usd = str(round(float(price) * float(usd_rate), 2))
                    # price_usd = price
                    print("Price USD >> ", price_usd)

                    local = "INR"

                    e_data = ("WRANGLER", link, title, product_category, product_type,
                              price,dis_price, local, price_usd, desc.strip(), image_url,
                              "INDIA", "")

                    Common.addData(Common.connection, [e_data])
                    print(f'Product Added')
                    print("-" * 35)
                    statsData[typ]["products_inserted"] += 1
                except Exception as e:
                    print(f"Error: {e}")
                    print(f'PRODUCT SKIPPED')
                    driver = reset()

if __name__ == "__main__":
    usd_rate = functions.get_conversion_rate('INR', 'USD')
    try:
        get_links()
    except Exception as e:
        print(f'Error: {e}')
        traceback.print_exc()

quitDriver()

######################### REPORT GENERATION #########################

from reportGenerator import *

try:
    print(f'Table: {dbConfig["table"]}')
except:
    dbConfig = db_config
    
print(f'Table: {dbConfig["table"]}')

currentFileName = os.path.basename(__file__)

brand, country = "Wrangler", "India"
data = makeDataFromDict(statsData, brand, country)

connection,cursor = connectToSqlDb()
insertDataInDb(connection, cursor, data, dbConfig['table'])
disconnectFromSqlDb(connection,cursor)
print(RESET)

finalReportString = getFinalDisplayString(statsData, currentFileName, brand, country)
print(finalReportString)