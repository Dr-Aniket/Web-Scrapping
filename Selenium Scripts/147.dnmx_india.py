statsData = {}

from selenium import webdriver
from selenium.webdriver.common.by import By
from time import sleep
from config import db_config
import pymysql
import requests
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
import re
import functions
from bs4 import BeautifulSoup
from common import Common
import traceback
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
links = main_urls = scrapping_urls = main_url = urls = get_db_links(connection,'dnmx','india')

def setup():
    chrome_options = Options()
    chrome_options.add_argument("--window-size=1920,1080");
    chrome_options.add_argument("--no-sandbox");
    chrome_options.add_argument("--headless");
    chrome_options.add_argument("--disable-gpu");
    chrome_options.add_argument("--disable-crash-reporter");
    chrome_options.add_argument("--disable-extensions");
    chrome_options.add_argument("--disable-in-process-stack-traces");
    chrome_options.add_argument("--disable-logging");
    chrome_options.add_argument("--disable-dev-shm-usage");
    chrome_options.add_argument("--log-level=3");
    chrome_options.add_argument("--output=/dev/null");

    driver = webdriver.Chrome(options=chrome_options)
    driver.maximize_window()
    return driver

connection = pymysql.connect(host='143.244.131.20',user='scrapping_user',password='brands@2023',database='brands')
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

def get_links(source):
    prefix = "https://trends.ajio.com"
    regex = r"/dnmx-[a-zA-Z0-9-]+/p/\d+_[a-zA-Z0-9-]+"
    links = re.findall(regex, source)
    link = list(set(links))
    links = [prefix + i for i in link]
    return links

def scroll_to_end(driver,n = 30):
    for i in range(n):
        driver.execute_script("window.scrollBy(0, 1000);")
        sleep(1)
    # scroll to end
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    sleep(5)
        
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

def main():
    global main_urls, usd_rate    
    driver = setup()
    for category, url in main_urls.items():
            print(f'Category: {category}')
            statsData[category] = {'total_unique_products': 0,'products_inserted': 0,'url': url}
            print(f'URL: {url}')
            driver.get(url)
            sleep(10)
            print('Scrolling to get all products')
            scroll_to_end(driver)
            print(f'Extracting links')

            source = driver.page_source
            links = get_links(source)
            print(f'Total Links: {len(links)}')
            
            links = list(set(links))
            print(f'Total Unique Links: {len(links)}')

            statsData[category]["total_unique_products"] += len(links)
            for link in links:
                try:
                    print("Link >> ", link)
                    driver.get(link)
                    sleep(5)

                    # title
                    try:
                        title = driver.find_element(By.CLASS_NAME, "prod-name").text.strip()
                    except:
                        title = ''
                    print("Title >> ", title)

                    # price
                    # Discount
                    try:
                        price = driver.find_element(By.XPATH, "//div[@class='prod-price-sec']//span[@class='prod-cp']").text
                        dis_price = driver.find_element(By.XPATH,"//div[@class='prod-price-section ']//div[@class='prod-sp']").text
                    except:
                        price = driver.find_element(By.XPATH, "//div[@class='prod-price-section ']//div[@class='prod-sp']").text
                        dis_price = ""

                    price = get_price(price)
                    dis_price = get_price(dis_price)

                    print("Price >> ", price)
                    print("Discount >> ", dis_price)

                    # img
                    try:
                        image_url = driver.find_element(By.XPATH, "//img[@class='rilrtl-lazy-img img-alignment zoom-cursor rilrtl-lazy-img-loaded']")
                        driver.execute_script("arguments[0].click();", image_url)
                        sleep(0.5)
                        image_url = driver.find_element(By.XPATH, '//img[contains(@id,"silder-image")]').get_attribute('src')
                    except:
                        image_url = ''

                    print("Image >> ", image_url)

                    try:
                        load_mode = driver.find_element(By.XPATH, '//div[@class="other-info-toggle"]')
                        driver.execute_script("arguments[0].click();", load_mode)
                    except:
                        pass
                    sleep(0.5)
                    desc = ''
                    try:
                        xpath = '//section[@class="prod-desc"]'
                        ele = driver.find_element(By.XPATH, xpath)
                        desc = get_data(ele)
                    except:
                        pass

                    print("Desc >> ", desc)

                    ty = category.split(" ",1)

                    product_category = ty[0]
                    product_type = ty[-1]

                    price_usd = str(round(float(price) * float(usd_rate), 2))
                    # price_usd = price
                    print("Price USD >> ", price_usd)

                    local = "INR"

                    e_data = ("DNMX RELIANCE", link, title, product_category, product_type,
                              price,dis_price, local, price_usd, desc.strip(), image_url,
                              "INDIA", "")

                    Common.addData(Common.connection, [e_data])
                    statsData[category]["products_inserted"] += 1
                    print('Product Added')
                    print("-" * 35)
                except Exception as e:
                    print(e)
                    if links.count(link) < 3:
                        links.append(link)
                        
    driver.quit()

if __name__ == "__main__":
    usd_rate = functions.get_conversion_rate('INR', 'USD')

    try:
        main()
    except Exception as e:
        print(f'ERROR: {e}')
        traceback.print_exc()

######################### REPORT GENERATION #########################

from reportGenerator import *

try:
    print(f'Table: {dbConfig["table"]}')
except:
    dbConfig = db_config
    
print(f'Table: {dbConfig["table"]}')

currentFileName = os.path.basename(__file__)

brand, country = "DNMX RELIANCE", "INDIA"
data = makeDataFromDict(statsData, brand, country)

connection,cursor = connectToSqlDb()
insertDataInDb(connection, cursor, data, dbConfig['table'])
disconnectFromSqlDb(connection,cursor)
print(RESET)

finalReportString = getFinalDisplayString(statsData, currentFileName, brand, country)
print(finalReportString)