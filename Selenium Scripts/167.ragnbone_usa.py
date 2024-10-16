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
links = main_urls = scrapping_urls = main_url = urls = get_db_links(connection,'rag.*bone','usa')

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
        print(f'Data Not Inserted in Data Base')

def load(url):
    driver.get(url)
    sleep(10)

    try:
        ele = driver.find_element(By.XPATH,'//button[@id="onetrust-accept-btn-handler"]')
        driver.execute_script("arguments[0].click();", ele)
    except:
        pass

    try:
        ele = driver.find_element(By.XPATH,'//a[contains(@id,"bx-close")]')
        driver.execute_script("arguments[0].click();", ele)
    except:
        pass

    try:
        ele = driver.find_element(By.XPATH,'//button[contains(@class,"close")]')
        driver.execute_script("arguments[0].click();", ele)
    except:
        pass

    try:
        eles = driver.find_elements(By.XPATH,'//span[contains(@class,"glClose")]')
        for ele in eles:
            driver.execute_script("arguments[0].click();", ele)
    except:
        pass

    try:
        eles = driver.find_elements(By.XPATH,'//button[contains(@aria-controls,"consent-dialog")]')
        for ele in eles:
            driver.execute_script("arguments[0].click();", ele)
    except:
        pass

    try:
        eles = driver.find_elements(By.XPATH,'//button[@data-click="close"]')
        for ele in eles:
            driver.execute_script("arguments[0].click();", ele)
    except:
        pass

    sleep(0.5)

def scroll_down(pixels):
    for i in range(1, pixels, 50):
        driver.execute_script(f"window.scrollBy(0, {i});")
        sleep(0.01)

def change_currency(driver):
    try:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        sleep(1)
        h = driver.execute_script("return document.body.scrollHeight")
        scroll_down(h)

        btn = driver.find_element(By.XPATH, '//div[contains(@class,"country-selector")]')

        # go to element
        ActionChains(driver).move_to_element(btn).perform()

        driver.execute_script("arguments[0].click();", btn)

        select = Select(driver.find_element(By.XPATH, '//select[contains(@id,"selectedCountry")]'))
        select.select_by_value('US')

        btn = driver.find_element(By.XPATH, '//input[contains(@class,"saveBtn")]')
        driver.execute_script("arguments[0].click();", btn)

        sleep(7)
    except Exception as e:
        print(f'Currency not changed: {e}')
        pass

def get_links(url, TRY = 3):
    global usd_rate
    global local
    def extract_links():
        elements = driver.find_elements(By.XPATH, '//a[@class="b-product_tile-image_link"]')
        links = [a.get_attribute('href') for a in elements]
        return links

    load(url)
    change_currency(driver)
    try:
        total = driver.find_element(By.XPATH,'//span[contains(@class,"results")]')
        total = total.text.split()[0]
        print(f'Total Expected Products: {total}')
    except:
        pass

    try:
        price = driver.find_element(By.XPATH,'//span[contains(@class,"price-item")]').text
        if '$' not in price:
            usd_rate = functions.get_conversion_rate('inr','usd')
            local = 'INR'
        else:
            raise Exception('USD PRICE')
    except Exception as e:
        local = 'USD'
        usd_rate = 1

    links = []
    
    page = 1
    while page:
        try:
            products = extract_links()
            links += products
            page += 1
            try:
                ele = driver.find_element(By.XPATH, '//a[contains(@class,"load_more")]')
                driver.execute_script("arguments[0].click();", ele)
                sleep(10)
            except:
                break
        except:
            break

    if len(links) == 0 and TRY > 0:
        links = get_links(url, TRY-1)

    return list(set(links))

def main():
    global main_urls    
    global usd_rate 
    global driver
    
    driver = setup()
    for category, url in main_urls.items():
            print(f'Category: {category}')
            statsData[category] = {'total_unique_products': 0,'products_inserted': 0,'url': url}
            print(f'URL: {url}')
            print(f'Extracting links')
            links = get_links(url)
            total_links = len(links)
            print(f'Total Links: {total_links}', ' '*100)
            statsData[category]["total_unique_products"] += total_links

            for product_number, link in enumerate(links):
                try:
                    link = link.split('?')[0]+'?gc=US'
                    print(f'Link: {link}')
                    load(link)

                    try:
                        title = driver.find_element(By.XPATH, '//h1[@class="b-product_details-name"]').text
                    except:
                        title = ''
                    print(f'Title: {title}')

                    try:
                        image = driver.find_element(By.XPATH,'//img[@id="product-image-0"]').get_attribute('src')
                        image = image.split('?')[0]
                        if 'http' not in image:
                            image_url = 'https:' + image
                        image_url = image
                    except Exception as e:
                        # print(f'Image URL not found: {e}')
                        image_url = ''
                    print(f'Image URL: {image_url}')

                    try:
                        try:
                            price = driver.find_element(By.XPATH,'//span[contains(@class,"b-price-item m-old")]').text
                            new_price = driver.find_element(By.XPATH,'//span[contains(@class,"b-price-item m-new")]').text
                        except:
                            price = driver.find_element(By.XPATH,'//span[contains(@class,"b-price-item")]').text
                            new_price = ''
                    except:
                        raise Exception('Price not found')

                    price = get_price(price)
                    new_price = get_price(new_price)
                    
                    print(f'Price: {price}')
                    print(f'New Price: {new_price}')

                    xpaths = ['//div[contains(@id,"product-details")]','//section[contains(@id,"size-and-fit-section")]','//section[contains(@id,"features-and-details-section")]']
                    desc = ''
                    for xpath in xpaths:
                        try:
                            element = driver.find_element(By.XPATH,xpath)
                            desc += get_data(element)
                        except:
                            pass

                    print(f'Description: {desc}')

                    ty = category.split(" ",1)

                    product_category = ty[0]
                    product_type = ty[-1]

                    try:
                        price_usd = str(round(float(price) * float(usd_rate), 2))
                    except:
                        raise Exception('Price not found')
                    
                    print("Price USD >> ", price_usd)

                    e_data = ("Rag & Bone", link, title, product_category, product_type,
                              price,new_price, local, price_usd, desc.strip(), image_url,"USA", "")

                    Common.addData(Common.connection, [e_data])
                    print('Product Added')
                    statsData[category]["products_inserted"] += 1

                    try:
                        print("-" * 35)
                        print(f'{product_number+1}/{total_links} [{(product_number+1)/total_links * 100:.2f}%] Done')
                        print("-" * 35)
                    except:
                        pass
                    
                except Exception as e:
                    print(e)
                    if links.count(link) < 3:
                        links.append(link)
  
    driver.quit()

driver = None

if __name__ == "__main__":
    usd_rate = 1

    try:
        main()
    except Exception as e:
        print(f'Error: {e}')
        traceback.print_exc()

######################### REPORT GENERATION #########################

from reportGenerator import *

try:
    print(f'Table: {dbConfig["table"]}')
except:
    dbConfig = db_config
    
currentFileName = os.path.basename(__file__)

brand, country = "Rag & Bone", "USA"
data = makeDataFromDict(statsData, brand, country)

connection,cursor = connectToSqlDb()
insertDataInDb(connection, cursor, data, dbConfig['table'])
disconnectFromSqlDb(connection,cursor)
print(RESET)

finalReportString = getFinalDisplayString(statsData, currentFileName, brand, country)
print(finalReportString)