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
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
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
from fake_useragent import UserAgent
from common import Common
import traceback
import random
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
links = main_urls = scrapping_urls = main_url = urls = get_db_links(connection,'h&m','uae')

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


def scroll(driver,NR): # NR mean number of restaurant
    i=0
    while i<NR: # repeat of loop following statement NR times
        i+=1
        time.sleep(0.1) # stop processing for two second
        driver.execute_script("window.scrollTo(0, window.scrollY + 50)") # scroll 200 pixels

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

def upload_data_into_db(url,pro_catgory,pro_type,country_name,currency_name,currency_iso_symbol,check_symbol, TRY=3):
    global driver
    try:
        driver.get(url)
        time.sleep(10)
        
        try:
            driver.find_element(By.XPATH,'//span[@class="subbox-close"]').click()
        except:
            pass
        
        print('Product URL:>>>>>>>',url)
        try:
            driver.find_element(By.XPATH,'//*[@class="aeo-icon-close"]').click()
        except:
            pass
        try:
            driver.find_element(By.XPATH,'//button[contains(@class,"button_accept")]').click()
        except:
            pass
        try:
            driver.find_elements(By.XPATH,'//div[@class="close_btn_thick"]')[1].click()
        except:
            pass
        try:
            driver.find_elements(By.XPATH,'//button[contains(@class,"reject-cookie")]')[1].click()
        except:
            pass
        try:
            image_ele=driver.find_element(By.XPATH,'//meta[@name="og:image"]')
            image=image_ele.get_attribute('content')
        except:
            try:
                image_ele=driver.find_element(By.XPATH,'//meta[@property="og:image"]')
                image=image_ele.get_attribute('content')
            except:
                image_ele=driver.find_element(By.XPATH,'//div[@id="product-zoom-container"]/div/figure[2]/div/img')
                image=image_ele.get_attribute('data-zoom-url')
        
        print('Image IRL:',image)
        try:
            name=driver.find_element(By.XPATH,'//div[@class="content__title_wrapper"]/h1').text
        except:
            pass
        print('Product Name:>>>>>>>',name)
        name = translate(name)

        try:
            prices = driver.find_elements(By.XPATH,'//span[@class="price-amount"]')
            if len(prices) == 0:
                raise Exception("Price Not Found")
            elif len(prices) == 1:
                old_price = get_price(prices[0].text)
                new_price = ''
            else:
                prices = prices[1:]
                if len(prices) == 1:
                    old_price = get_price(prices[0].text)
                    new_price = ''
                else:
                    old_price = get_price(prices[0].text)
                    new_price = get_price(prices[1].text)
        except:
            raise Exception("Price Not Found")        
        print('Discounted Price:',new_price)
        print('Product Price:',old_price)

        description = ''
        try:
            ele = driver.find_element(By.XPATH,'//div[@class="magazine-desc-wrapper"]')
            description += get_data(ele)
        except:
            pass

        try:
            more = driver.find_element(By.XPATH,'//div[@class="pdp-overlay-details"]')
            more.click()
            # driver.execute_script("arguments[0].click();",more)
            time.sleep(2)
            ele = driver.find_element(By.XPATH,'//div[contains(@class,"attribute-sliderbar")]')
            description += get_data(ele)
        except:
            pass

        description = description.replace('DETAILS\nDETAILS\n','\n')

        # description = translate(description)
        print('Product Description:',description)
        
        list_for_upload=[com_name,url,name,pro_catgory,
                        pro_type,old_price,new_price,currency_name,
                        round(old_price*cur_mul,2),description,image,country_name,'']
        addData(list_for_upload)
        print('Product Added')
        statsData[typ]["products_inserted"] += 1
    except Exception as e:
        print(f'Error: {e}')
        driver = reset()
        if TRY>0:
            upload_data_into_db(url,pro_catgory,pro_type,country_name,currency_name,currency_iso_symbol,check_symbol,TRY-1)

    print(f'------------------------ Product {count_pro} Scrapped ------------------------')
    
com_name='H&M'
country = 'UAE'
currency = 'AED'
currency_iso = 'aed'
check_sym = 'AED'
cur_mul = functions.get_conversion_rate(currency_iso)

driver = setup()

try:
    count_pro=1
    for typ in main_url:
        try:
            pro_cat,pro_type = typ.split(' ',1)
            print(country,pro_cat,pro_type,': START')
            url = main_url[typ]

            statsData[typ] = {'total_unique_products': 0,'products_inserted': 0,'url': url}

            print('URL >> ',url)
            try:
                driver.get(url)
                time.sleep(10)
            except:
                continue
            
            try:
                driver.find_element(By.XPATH,'//button[@id="onetrust-reject-all-handler"]').click()
            except:
                pass

            try:
                total = driver.find_elements(By.XPATH,'//span[@class="ais-Stats-text"]')[-1]
                total = re.findall("\d+",total.text)
                total = max([int(ele) for ele in total])
                print(f'Total Expected Products: {total}')
            except:
                pass

            list_of_pro_urls = []

            page = 1
            print(f'Page: {page}')
            while page:
                scroll(driver,40)
                try:
                    list_of_pro_urls += [ele.get_attribute('href') for ele in driver.find_elements(By.XPATH,'//a[@class="list-product-gallery product-selected-url"]')]
                    ele = driver.find_element(By.XPATH,'//button[@rel="next"]')
                    driver.execute_script(f'arguments[0].click();',ele)
                    page += 1
                    print(f'Page: {page}')
                    time.sleep(2)
                except Exception as e:
                    break

            print(f'Total Products Found: {len(list_of_pro_urls)}')
            list_of_pro_urls = list(set(list_of_pro_urls))
            print(f'Total Unique Links: {len(list_of_pro_urls)}')

            print(f'------------------------ Scrapping the Products ------------------------')
            statsData[typ]["total_unique_products"] = len(list_of_pro_urls)
        except Exception as e:
            print(f'Error in {typ}: {e}')
            continue

        for pro_url in list_of_pro_urls:
            print('Product Number',count_pro)
            count_pro += 1
            upload_data_into_db(pro_url,pro_cat,pro_type,country,currency,currency_iso,check_sym)
        print(country,pro_cat,pro_type,'  END')
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

brand, country = com_name, country
data = makeDataFromDict(statsData, brand, country)

connection,cursor = connectToSqlDb()
insertDataInDb(connection, cursor, data, dbConfig['table'])
disconnectFromSqlDb(connection,cursor)
print(RESET)

finalReportString = getFinalDisplayString(statsData, currentFileName, brand, country)
print(finalReportString)