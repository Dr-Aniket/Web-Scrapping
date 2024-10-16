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
import random
from langdetect import detect
import functions 

from common import Common
import traceback
import random
from bs4 import BeautifulSoup
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
links = main_urls = scrapping_urls = main_url = urls = get_db_links(connection,'diesel','india')

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
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    # options.add_argument("--disable-crash-reporter")
    # options.add_argument("--disable-extensions")
    # options.add_argument("--disable-in-process-stack-traces")
    # options.add_argument("--disable-logging")
    # options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--log-level=3")
    # options.add_argument("--output=/dev/null")
    options.add_argument("--incognito")
    # options.add_argument(f"user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.9999.999 Safari/537.36")
    if chrome:
        driver = webdriver.Chrome(options=options)
    else:
        driver = webdriver.Firefox(options=options)
    driver.maximize_window()
    action = ActionChains(driver)

    return driver

# Using this function we scroll at the bottom
def scroll(driver,NR): # NR mean number of restaurant
    i=0
    
    while i<NR: # repeat of loop following statement NR times
        i+=1
        time.sleep(0.1) # stop processing for two second
        driver.execute_script("window.scrollTo(0, window.scrollY + 2000)") # scroll 200 pixels
    
def addData(list_for_upload):
    try:
        with connection.cursor() as cursor:
            sql = """INSERT INTO `brands_data` (`brand_name`, `product_link`, 
            `product_name`, `product_category`, `product_type`, `product_price`, 
            `discounted_price`, `price_unit`, `price_usd`, `product_description`, 
            `fabric_composition`, `product_image`, `country`, `page_numer`) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            cursor.execute(sql, list_for_upload)
        connection.commit()

    except Exception as e:
        print(e)

def get_compo(data):
    include = ['body']
    remove = include + ['made','with','main','material']
    crop_before = [',']

    def crop(line):
        for char in crop_before:
            if char in line:
                line = line.split(char)[0]

    def clean_compo(data):
        data = data.lower()

        allow = ['%',' ','.']

        for word in remove:
            data = data.replace(word,'')

        final_data = ''
        for char in  data:
            if char in allow or char.isalpha() or char.isdigit():
                final_data += char

        return final_data.title().strip()

    def strip_end(line):
        if line[-1] != '.':
            line = ' '.join(line.split())
            return line
        return strip_end(line[:-1])

    def get_line(lines, check_include=True):
        for line in lines:
            if '%' in line and 'cotton' in line and (not check_include or bool([1 for word in include if word in line])):
                return line
        
        if check_include:
            return get_line(lines, False)
        else:
            return ''
    
    data = data.lower()
    
    line = get_line(data.split('\n'))
    
    line = clean_compo(line)
    line = crop(line)
    line = strip_end(line)
    return line
        
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

def upload_data_into_db(url,pro_category,pro_type):
    try:
        driver.get(url)
        time.sleep(10)

        try:
            driver.find_element(By.XPATH,'//*[@class="aeo-icon-close"]').click()
            time.sleep(2)
        except:
            pass
        try:
            driver.find_elements(By.XPATH,'//*[@class="aeo-icon-close"]')[1].click()
            time.sleep(2)
        except:
            pass
        try:
            driver.find_elements(By.XPATH,'//button[contains(@class,"reject-cookie")]')[1].click()
            time.sleep(2)
        except:
            pass

        print('Product URL:>>>>>>>',url)
        try:
            image=driver.find_element(By.XPATH,'//*[@id="parent"]/div[2]/div[2]/div[1]/div/div/div[1]/a/img').get_attribute('src')
            image = re.sub(r'\(w:\d+\)','(w:1080)',image)
        except Exception as e:
            image=''
        print('Image IRL:>>>>>>>>',image)
        
        try:
            name=driver.find_element(By.XPATH, '//h1[@class="product-title"]').text
        except:
            name = ''
        name = translate(name)

        print('Product Name:>>>>>>>',name)

        try:
            price_ele=driver.find_element(By.XPATH, '//p[@class="p-price"]').text
            if price_ele.count('MRP'):
                price_ele=price_ele.replace('MRP ','')
            if price_ele.count('₹')>1:
                price_list=price_ele.split(' ')
                old_price=get_price(price_list[0])
                new_price=get_price(price_list[1])
            else:
                old_price=get_price(price_ele)
                new_price=''
        except:
            raise Exception('Price not found')
        print('Discounted Price:>>>>>>>>',new_price,'\n','Product Price:>>>>>>>>',old_price)
        
        try:
            try:
                driver.find_element(By.XPATH, '//*[contains(text(),"Care instructions")]').click()
            except:
                driver.find_element(By.XPATH, '//*[contains(text(),"Care instructions")]').click()
        except:
            pass
        try:
            try:
                driver.find_element(By.XPATH, '//*[contains(text(),"Model Fit")]').click()
            except:
                driver.find_element(By.XPATH, '//*[contains(text(),"Model Fit")]').click()
        except:
            pass
        try:
            try:
                driver.find_element(By.XPATH, '//*[contains(text(),"Other Details")]').click()
            except:
                driver.find_element(By.XPATH, '//*[contains(text(),"Other Details")]').click()
        except:
            pass

        try:
            description=driver.find_element(By.XPATH, '//div[@class="product-collapsible-sections"]')
            description = get_data(description)
        except:
            description=''
        print('Product Description:>>>>>>>>',description)
        try:
            composition = get_compo(description)
        except:
            composition = ''
        print(f'Composition: {composition}')
        
        try:
            price = round(old_price*cur_mul,2)
        except Exception as e:
            print(e)
            print(f'USD Price Calculation Error\nSKIPPING PRODUCT')
        
        list_for_upload=[com_name,url,name,pro_category,
                        pro_type,old_price,new_price,'INR',
                        price,description,composition,image,country,'']
#         print(list_for_upload)
        addData(list_for_upload)
        print('Product Added')
        statsData[typ]["products_inserted"] += 1
        
    except Exception as e:
        print(e)
#        statsData[typ]["fail"] += 1

com_name='Diesel'
country='India'
cur_mul = functions.get_conversion_rate('inr')
print('USD Multiplier:>>>>>>>>',cur_mul)

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
        sleep(2)

    while 1:
        pro_no_data = driver.find_element(By.XPATH, '//div[@class="you-have-seen js_you-have-seen tt"]').text
        total_pro = int(pro_no_data.split()[-2])
        curr_pro = int(pro_no_data.split()[2])
        print(f'Products: [{curr_pro}/{total_pro}]',end='\r')
        if curr_pro >= total_pro:
            break
        scroll_to_end()

    print("Loaded All Products",' '*10)

driver = setup()

count_pro=1
for typ in main_url:
    try:
        pro_cat, pro_type = typ.split(' ',1)
        
        url = main_url[typ]
        print(f'{typ} URL::>>',url)
        driver.get(url)
        time.sleep(10)
        try:
            driver.find_element(By.XPATH,'//button[contains(@class,"accept-cookie")]').click()
            time.sleep(2)
        except:
            pass
        try:
            driver.find_element(By.XPATH, "//button[@class='button primary button-cookie']").click()
        except:
            pass
        try:
            driver.find_elements(By.XPATH,'//button[contains(@class,"close")]')[0].click()
            time.sleep(2)
        except:
            pass
        
        flag=True
        scroll_load_all(driver, 10, 0.5)

        products=driver.find_elements(By.XPATH,'//div[@class="title-body"]/a')
        list_of_pro_urls=[]
        for num in range(len(products)):
            try:
                pro_url=products[num].get_attribute('href')
                list_of_pro_urls.append(pro_url)
            except:
                continue

        list_of_pro_urls = list(set(list_of_pro_urls))

        print(f'Total Products in {pro_cat} {pro_type}: ',len(list_of_pro_urls))
        print('################### Scrapping Start ######################') 
        statsData[typ] = {'total_unique_products': len(list_of_pro_urls),'products_inserted': 0,'url': url}

        for pro_url in list_of_pro_urls:
            print('Product Number',count_pro)
            count_pro+=1
            upload_data_into_db(pro_url,pro_cat,pro_type)
        print(pro_cat,pro_type,' >>>>>>>>>> END')
    except Exception as e:
        print(f'ERROR in {typ}: {e}')
        print(traceback.format_exc())
        print(typ,' >>>>>>>>>> END')
        continue

try:
    driver.close()
except:
    pass

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