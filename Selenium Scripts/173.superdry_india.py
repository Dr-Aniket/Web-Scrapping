statsData = {}

chrome = True

from selenium import webdriver
from selenium.webdriver.common.by import By
from time import sleep
from config import db_config
import pymysql
import requests
from threading import Thread, Event

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
from bs4 import BeautifulSoup
from common import Common
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

from bs4 import BeautifulSoup
def get_data(element):
    html = element.get_attribute('innerHTML')
    soup = BeautifulSoup(html, 'html.parser')
    data = soup.get_text("\n", strip=True)
    return data + '\n'

from config import db_config
connection = pymysql.connect(host=db_config["host"], user=db_config["user"], passwd=db_config["passwd"],database=db_config["database"], port=db_config["port"])
from db_links import *
links = main_urls = scrapping_urls = main_url = urls = get_db_links(connection,'superdry','india')

from fake_useragent import UserAgent
if chrome:
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service as ChromeService
    from webdriver_manager.chrome import ChromeDriverManager
else:
    from selenium.webdriver.firefox.options import Options
    from selenium.webdriver.firefox.service import Service as FirefoxService
    from webdriver_manager.firefox import GeckoDriverManager

def setup():
    global action
    user = UserAgent().random
    options = Options()
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-crash-reporter")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-in-process-stack-traces")
    options.add_argument("--disable-logging")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--incognito")
    options.add_argument("--log-level=3")
    options.add_argument("--output=/dev/null")
    options.add_argument(f"user-agent={user}")

    # For headless mode
    options.add_argument("--headless=new")

    # Additional options to make headless less detectable
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option('useAutomationExtension', False)
    options.add_experimental_option('excludeSwitches', ['enable-automation'])

    if chrome:
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    else:
        driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()), options=options)

    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.execute_script("window.navigator.chrome = { runtime: {} };")
    driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
    driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")

    driver.maximize_window()
    action = ActionChains(driver)

    return driver

def scroll_to_end(driver,fac = 20, wait = 0.5):
    try:
        h = driver.execute_script("return document.body.scrollHeight")
        for i in range(0, h, h//fac):
            driver.execute_script(f"window.scrollTo(0, {i});")
            sleep(wait)
    except:
        pass

    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

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


def scroll_load_all(driver,fac = 20, wait = 0.5):
    def scroll_to_end():
        try:
            h = driver.execute_script("return document.body.scrollHeight")
            for i in range(0, h, h//fac):
                driver.execute_script(f"window.scrollTo(0, {i});")
                sleep(wait)
        except:
            pass

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        sleep(0.5)

    def scrolling_animation(event):
        i = 1
        c = 6
        loader = '|/-\\'
        while i:
            if event.is_set():
                break
            print(f'{loader[i%4]} Scrolling{"."*((i%c))}{" "*c}',end = '\r')
            i += 1
            sleep(0.1)
    
    event = Event()
    Thread(target = scrolling_animation, args = (event,)).start()

    i = 1
    while i:
        try:
            h = driver.execute_script("return document.body.scrollHeight")
            scroll_to_end()
            try:
                driver.find_element(By.XPATH, "//*[contains(text(), 'Show more products')]").click()
                sleep(1)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            except:
                pass
            new_h = driver.execute_script("return document.body.scrollHeight")
            # print(f'Scroll {i} >> {h} >> {new_h}',end='\r')
            try:
                driver.find_element(By.XPATH, "//*[contains(text(), 'All Products Listed')]")
            except:
                pass
            if h == new_h:
                break
            i += 1
        except:
            break
    event.set()

    print("Loaded All Products",' '*10)

def get_links():
    driver = setup()
    for typ, url in urls.items():

        print("*" * 40)
        print("URL >>> ", url)
        driver.get(url)
        sleep(5)

        try:
            pros = driver.find_elements(By.XPATH, '//*[@class="category-total-item"]').text.split()[0]
            print("Total Products >> ", pros)
        except:
            pass

        scroll_load_all(driver, fac=20, wait=0.5)

        products = driver.find_elements(By.XPATH,'//h4[@class="product-name"]//a')
        i = 0
        links = [product.get_attribute("href") for product in products]
        links = list(set(links))
        print(f'Total unique links: {len(links)}')
        statsData[typ] = {'total_unique_products': len(links),'products_inserted': 0,'url': url}

        for product_link in links:
            try:
                i += 1
                print("Sr no :", i)

                print("Link >> ", product_link)

                driver.get(product_link)
                sleep(5)

                title = driver.find_element(By.XPATH, "//h1").text.strip()
                print("Title >> ", title)

                try:
                    price_ele = driver.find_element(By.XPATH, '//*[contains(@class,"price-container")]')
                    price_ele = get_data(price_ele).lower().split('save')[0]
                except:
                    raise Exception("Price not found")

                dis_price, price = getPrices(price_ele)

                print("Price >> ", price)
                print("Discounted Price >> ", dis_price)

                try:
                    image_url = driver.find_element(By.XPATH,'//a[contains(@class,"popup-image")]').get_attribute('href')
                except:
                    image_url = ''
                print("Image >> ", image_url)

                xpaths = ['//div[@class="product-description"]']
                desc = ''
                for xpath in xpaths:
                    try:
                        desc += get_data(driver.find_element(By.XPATH, xpath))
                    except:
                        pass
                tabs = driver.find_elements(By.XPATH, '//div[@class="panel panel-default"]')
                tabs = [tabs[0],tabs[2]]

                for tab in tabs:
                    try:
                        desc += get_data(tab)
                    except:
                        pass

                print("Description >> ", desc)

                ty = typ.split(" ",1)

                product_category = ty[0]
                product_type = ty[-1]

                price_usd = str(round(float(price) * float(usd_rate), 2))
                # price_usd = price
                print("Price USD >> ", price_usd)

                local = "INR"

                e_data = ("Superdry", product_link, title, product_category, product_type,
                          price,dis_price, local, price_usd, desc.strip(), image_url,"INDIA", "")

                Common.addData(Common.connection, [e_data])
                print("Product Added")
                statsData[typ]["products_inserted"] += 1

                print('-' * 150)
            except Exception as e:
                print(f'Error >> {e}')                
                if links.count(product_link) < 3:
                    links.append(product_link)

    driver.quit()

if __name__ == "__main__":
    usd_rate = functions.get_conversion_rate('inr')
    get_links()

######################### REPORT GENERATION #########################

from reportGenerator import *

try:
    print(f'Table: {dbConfig["table"]}')
except:
    dbConfig = db_config
    
print(f'Table: {dbConfig["table"]}')

currentFileName = os.path.basename(__file__)

brand, country = "Superdry", "India"
data = makeDataFromDict(statsData, brand, country)

connection,cursor = connectToSqlDb()
insertDataInDb(connection, cursor, data, dbConfig['table'])
disconnectFromSqlDb(connection,cursor)
print(RESET)

finalReportString = getFinalDisplayString(statsData, currentFileName, brand, country)
print(finalReportString)