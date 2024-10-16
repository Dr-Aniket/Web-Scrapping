statsData = {}

#!/usr/bin/env python
# coding: utf-8

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import pymysql
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup

from config import db_config
connection = pymysql.connect(host=db_config["host"], user=db_config["user"], passwd=db_config["passwd"],database=db_config["database"], port=db_config["port"])
from db_links import *
links = main_urls = scrapping_urls = main_url = urls = get_db_links(connection,'patago','usa')

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

import re

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

def upload_data_into_db(url,pro_catgory,pro_type):
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
            driver.find_elements(By.XPATH,'//button[contains(text(),"Accept All Cookies")]')[1].click()
            time.sleep(2)
        except:
            pass
        print('Product URL::>>',url)

        image_ele=driver.find_element(By.XPATH,'//meta[@property="og:image"]')
        image=image_ele.get_attribute('content')
        image = image.replace(image[image.index('sw='):image.index('sh=')+6],'sw=1080&sh=1080')
        
        name=driver.find_element(By.XPATH,'//meta[@property="og:title"]').get_attribute('content')
        print('Image URL::>>',image)
        print('Title::>>',name)
        
        try:
            new_price, old_price = getPrices(get_data(driver.find_elements(By.XPATH,'//span[contains(@class,"config-price")]')[-1]))
        except Exception as e:
            print(f'Error in getting price: {e}')
            raise Exception('Price not found')
        
        print("Discounted Price::>>",new_price)
        print("Price::>>",old_price)

        try:
            description = get_data(driver.find_element(By.XPATH,'//*[contains(@itemprop,"description")]'))
            elements = driver.find_elements(By.XPATH,'//*[contains(@class,"accordion-group")]')
            for element in elements:
                description += get_data(element)
        except:
            description = ''
        print("Desc::>>",description)
        cur_mul=1
        list_for_upload=[com_name,url,name,pro_catgory,
                        pro_type,old_price,new_price,'USD',
                        round(old_price*cur_mul,2),description,image,country,'']
        addData(list_for_upload)
        print('Product Added')
        statsData[typ]["products_inserted"] += 1
    except Exception as e:
        print(e)
        pass

com_name='Patagonia Denim'
country='USA'

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument("user-agent=whatever you want")
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
## [~AB] Set window size to 1920x1080
chrome_options.add_argument('--window-size=1090,695')
chrome_options.add_argument('--log-level=3')
chrome_options.add_argument("--dns-prefetch-disable")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36")

driver = webdriver.Chrome(options=chrome_options)
driver.maximize_window()

count_pro=1
list_of_pro_urls=[]
for typ in urls:   
    url=main_url[typ]
    pro_cat,pro_type = typ.split(' ',1)
    driver.get(url)
    time.sleep(20)
    try:
        driver.find_element(By.XPATH,'//button[contains(text(),"Accept All Cookies")]').click()
        time.sleep(2)
    except:
        pass
    try:
        driver.find_elements(By.XPATH,'//button[contains(@class,"close")]')[0].click()
        time.sleep(2)
    except:
        pass
    
    flag=True
    # print('Loop Start: ')
    # scroll(driver,200)
        
    products=driver.find_elements(By.XPATH,'//div[contains(@class,"product-tile__cover")]/a')
    
    print('Products find.')
    
    for num in range(len(products)):
            try:
                pro_url=products[num].get_attribute('href')
                list_of_pro_urls.append(pro_url)
            except Exception as E:
                print('Error in url: ',pro_url,'\n',E)
                continue
    list_of_pro_urls=list(set(list_of_pro_urls))
                
    print('Total Products found ',len(list_of_pro_urls))           
    print('Scrapping Start') 
    statsData[typ] = {'total_unique_products': len(list_of_pro_urls),'products_inserted': 0,'url': url}
    for pro_url in list_of_pro_urls:
        print('Product Number',count_pro)
        count_pro+=1
        upload_data_into_db(pro_url,pro_cat,pro_type)

driver.close()

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