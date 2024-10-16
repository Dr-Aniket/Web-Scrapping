statsData = {}

chrome = 1

from selenium import webdriver
import time
from selenium.webdriver.common.by import By
import pymysql
if chrome:
    from selenium.webdriver.chrome.options import Options
else:
    from selenium.webdriver.firefox.options import Options
from fake_useragent import UserAgent
from selenium.webdriver.common.action_chains import ActionChains
import re
import functions
from config import db_config
from time import sleep
import traceback
import random

from config import db_config
connection = pymysql.connect(host=db_config["host"], user=db_config["user"], passwd=db_config["passwd"],database=db_config["database"], port=db_config["port"])
from db_links import *
links = main_urls = scrapping_urls = main_url = urls = get_db_links(connection,'warp','usa')


# Using this function we scroll at the bottom
def scroll(driver,NR): # NR mean number of restaurant
    i=0
    
    while i<NR: # repeat of loop following statement NR times
        i+=1
        time.sleep(0.1) # stop processing for two second
        driver.execute_script("window.scrollTo(0, window.scrollY + 2000)") # scroll 200 pixels

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

def addData(connect, uploadEntry,TRY = 3):
    global connection

    connection = connect
    try:
        with connection.cursor() as cursor:
            sql = """INSERT INTO `brands_data` (`brand_name`, `product_link`, 
            `product_name`, `product_category`, `product_type`, `product_price`, 
            `discounted_price`, `price_unit`, `price_usd`, `product_description`, 
            `product_image`, `country`, `page_numer`) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            cursor.execute(sql, uploadEntry)

        connection.commit()

        return True

    except Exception as e:
        print(e)
        if TRY:
            connection = pymysql.connect(host=db_config["host"], user=db_config["user"], passwd=db_config["passwd"],database=db_config["database"], port=db_config["port"])
            return addData(connection, uploadEntry,TRY-1)
        print(f'Product Not Added')
        raise Exception('Product Not Added')

def upload_data_into_db(url,pro_category,pro_type,TRY = 3):
    global driver
    try:
        driver.get(url)
        print(f'Link: {url}')
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
        
        try:
            image_ele = driver.find_element(By.XPATH, '//div[@class="photo"]')
            image = image_ele.get_attribute('style')
            image = re.search(r'url\("(.+)"\)', image).group(1)
            if 'http' not in image:
                image = 'https:' + image
        except Exception as e:
            image = ""

        print(f'Image: {image}')
        
        try:
            name = driver.title.split('|')[0]
        except:
            name = ''
        print(f'Name: {name}')
        
        try:
            price_ele=driver.find_element(By.XPATH,'//span[contains(@class,"price_main")]').text
            price_ele=price_ele.replace('FINAL SALE','')
            
            if price_ele.count('$')>1:
                price_ele_list=price_ele.split('$')
                new_price_ele=price_ele_list[2]
                old_price_ele=price_ele_list[1]
                try:
                    new_price=get_price(new_price_ele)
                    old_price=get_price(old_price_ele)
                except:
                    new_price=new_price_ele
                    old_price=old_price_ele
            else:
                new_price_ele=driver.find_element(By.XPATH,'//span[contains(@class,"price_main")]').text
                new_price_ele=new_price_ele.replace('$','')
                try:
                    new_price=get_price(new_price_ele)
                except:
                    new_price=new_price_ele
                old_price=new_price
        except:
            raise Exception('Price not found')
        
        if new_price==old_price:
            new_price=''
        print(f'Old Price: {old_price}')
        print(f'New Price: {new_price}')

        try:
            description_ele = driver.find_element(By.XPATH,'//div[contains(@class,"shop-description")]')
            description = get_data(description_ele)
        except:
            description = ''
        print(f'Description: {description}')
        cur_mul=1
        list_for_upload=[com_name,url,name,pro_category,
                        pro_type,old_price,new_price,'USD',
                        round(old_price*cur_mul,2),description,image,country,'']
        
        if addData(connection,list_for_upload):
            print('Product Added')
            statsData[typ]["products_inserted"] += 1
        else:
            raise Exception("Error in Uploading data")
    except Exception as e:
#        statsData[typ]["fail"] += 1
        print(f'Error in upload_data_into_db: {e}')
        driver = reset()
        if TRY:
            return upload_data_into_db(url,pro_category,pro_type,TRY-1)
        
com_name='Warp + Weft'
country='USA'

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

try:
    count_pro=1
    for typ in main_url:
        driver = reset()

        url = main_url[typ]
        driver.get(url)

        pro_cat, pro_type = typ.split(" ",1)

        time.sleep(10)

        try:
            ele = driver.find_element(By.XPATH,'//button[contains(@class,"close")]')
            driver.execute_script("arguments[0].click();", ele)
        except:
            pass

        try:
            driver.find_element(By.XPATH,'//a[@class="confirm"]').click()
        except:
            pass
        try:
            driver.find_elements(By.XPATH,'//button[contains(@class,"close")]')[0].click()
        except:
            pass
        
        try:
            ele = driver.find_element(By.XPATH,'//a[contains(@class,"confirm")]')
            driver.execute_script("arguments[0].click();", ele)
        except:
            pass

        print('Loop Start: ')
        scroll(driver,200)
        
        products = driver.find_elements(By.XPATH,'//a[@class="product-card-link"]')
        print('Products find.',len(products))
        list_of_pro_urls=[]
        for num in range(len(products)):
            try:
                pro_url=products[num].get_attribute('href')
                list_of_pro_urls.append(pro_url)
            except Exception as E:
                print('Error in url: ',pro_url,'\n',E)
                continue

        list_of_pro_urls = list(set(list_of_pro_urls))
        print(f'Number of Unique Products: {len(list_of_pro_urls)}')
        statsData[typ] = {'total_unique_products': len(list_of_pro_urls),'products_inserted': 0,'url': url}

        for pro_url in list_of_pro_urls:
            print('Product Number',count_pro)
            count_pro+=1
            upload_data_into_db(pro_url,pro_cat,pro_type)
except:
    traceback.print_exc()

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