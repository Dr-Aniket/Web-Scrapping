statsData = {}

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
import re
from config import db_config

from config import db_config
connection = pymysql.connect(host=db_config["host"], user=db_config["user"], passwd=db_config["passwd"],database=db_config["database"], port=db_config["port"])
from db_links import *
links = main_urls = scrapping_urls = main_url = urls = get_db_links(connection,'carhartt','usa')

from time import sleep

# Using this function we scroll at the bottom
def scroll(driver,NR): # NR mean number of restaurant
    i=0
    
    while i<NR: # repeat of loop following statement NR times
        i+=1
        time.sleep(0.1) # stop processing for two second
        driver.execute_script("window.scrollTo(0, window.scrollY + 200)") # scroll 200 pixels
def scroll_down(pixels):
    for i in range(1, int(pixels), 10):
        driver.execute_script(f"window.scrollBy(0, {i});")
        sleep(0.01)

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

def get_composition(desc):
    desc += '\n'
    def find(word, text):
        index = None
        for i in range(len(text)):
            if text[i] == word[0] and text[i:i+len(word)] == word:
                index = i
                
        return index

    def clean_composition( compo ):
        compo = compo.lower()
        print(compo)
        materials = 'Elasta,ELASTAN,elastane,lycra,spandex,polyester,viscose,rayon,fibers,cotton,Polyurethane,elastomultiester,Lyocell,nylonwide,hemp,ELASTHEN,Tencel,elasterell'
        materials = materials.lower().split(',')

        mat_ind = {}
        for material in materials:
            if material in compo:
                ind = find(material,compo)
                if not ind:
                    continue
                mat_ind[ind] = len(material)
        max_ind = max(mat_ind.keys())
        max_ind = max_ind + mat_ind[max_ind]
        compo = compo[:max_ind]

        return compo
       
    exp = "[0-9]{1,3}\.?[0-9]{0,3} ?%.{0,40}cotton.+\n"

    match = re.search(exp, desc, re.IGNORECASE)
    if match:
        compo = match.group(0)
        compo = clean_composition(compo)
        return compo
    else:
        return None
    
from bs4 import BeautifulSoup
def get_data(element):
    html = element.get_attribute('innerHTML')
    soup = BeautifulSoup(html, 'html.parser')
    data = soup.get_text("\n", strip=True)
    return data + '\n'

def get_compo(data):
    include = ['shell']
    remove = include + ['made','with','main','material']
    
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
    line = get_composition(line)
    line = strip_end(line)
    return line

def upload_data_into_db(url,pro_catgory,pro_type):
    try:
        driver.get(url)
        time.sleep(10)
        try:
            driver.find_element(By.XPATH,'//*[@class="aeo-icon-close"]').click()
            # time.sleep(2)
        except:
            pass
        try:
            driver.find_elements(By.XPATH,'//div[@class="close_btn_thick"]')[1].click()
            # time.sleep(2)
        except:
            pass
        try:
            driver.find_elements(By.XPATH,'//button[contains(@class,"reject-cookie")]')[1].click()
            # time.sleep(2)
        except:
            pass
    
        try:
            image_ele=driver.find_element(By.XPATH,'//img[@class="main-static-image"]')
            image=image_ele.get_attribute('src')
            image = re.sub(r'&wid=\d+&hei=\d+','&wid=1080&hei=1080',image)
        except:
            image = ''

        name=driver.title.split('|')[0] 
        
        price_ele=driver.find_element(By.XPATH,'//div[@class="prices"]').text

        if price_ele.count('$')>1 and price_ele.count('-')==0:
            old_price_ele=driver.find_element(By.XPATH,'//div[contains(@class,"strike-through")]').text
            new_price_ele=driver.find_element(By.XPATH,'//div[contains(@class,"product-price")]').text
            try:
                new_price=get_price(new_price_ele)
                old_price=get_price(old_price_ele)
            except:
                new_price=new_price_ele
                old_price=old_price_ele



        elif price_ele.count('$')>2 and price_ele.count('-')>0:
            old_price_ele=driver.find_element(By.XPATH,'//div[contains(@class,"strike-through")]').text
            if old_price_ele.count('-')>0:
                old_price_ele=old_price_ele[:old_price_ele.index('-')-1]
            new_price_ele=driver.find_element(By.XPATH,'//div[contains(@class,"product-price")]').text
            if new_price_ele.count('-')>0:
                new_price_ele=new_price_ele[:new_price_ele.index('-')-1]
            try:
                new_price=get_price(new_price_ele)
                old_price=get_price(old_price_ele)
            except:
                new_price=new_price_ele
                old_price=old_price_ele
        else:
            new_price_ele=driver.find_element(By.XPATH,'//div[@class="prices"]').text
            
            old_price_ele=driver.find_element(By.XPATH,'//div[@class="prices"]').text
            if old_price_ele.count('-')>0:
                old_price_ele=old_price_ele[:old_price_ele.index('-')-1]
            if new_price_ele.count('-')>0:
                new_price_ele=new_price_ele[:new_price_ele.index('-')-1]
            try:
                new_price=get_price(new_price_ele)
                old_price=get_price(old_price_ele)
            except:
                new_price=new_price_ele
                old_price=old_price_ele
        print('New:',new_price)
        print('Old:',old_price)
        if new_price>old_price:
            new_price,old_price=old_price,new_price
        if new_price==old_price:
            new_price=''

        # page_source_text=driver.page_source
        # features_text=page_source_text[page_source_text.index('Features'):]
        # data=features_text[:features_text.index('</ul>')]
        # description=re.sub(r'<.*?>', '', data)
            
        scroll_down(200)
        try:
            description = get_data(driver.find_element(By.XPATH,'//div[@class="content"]'))
        except Exception as e:
            print(f'Error: {e}')
            description = ''
                
        try:
            composition = get_compo(description)
        except:
            composition = ''
        print(f'Composition: {composition}')

        cur_mul=1
        list_for_upload=[com_name,url,name,pro_catgory,
                        pro_type,old_price,new_price,'USD',
                        round(old_price*cur_mul,2),description,composition,image,country,'']
#         print(list_for_upload)
        addData(list_for_upload)
        print('Product Added')
        statsData[typ]["products_inserted"] += 1
    except Exception as e:
#        statsData[typ]["fail"] += 1
        print(e)
        pass

com_name='CARHARTT'
country='USA'

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--log-level=3')
chrome_options.add_argument('--window-size=1920x1080')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(options=chrome_options)
driver.maximize_window()

count_pro=1
for typ in main_url:    
    # typ = f'{pro_cat} {pro_type}'
    url=main_url[typ]
    pro_cat, pro_type = typ.split(' ',1)
    driver.get(url)
    time.sleep(20)
    try:
        driver.find_element(By.XPATH,'//div[@class="close_btn_thick"]').click()
        time.sleep(2)
    except:
        pass
    try:
        driver.find_elements(By.XPATH,'//button[contains(@class,"close")]')[0].click()
        time.sleep(2)
    except:
        pass

#     driver.get_screenshot_as_file('Carhartt usa First Page.png')
    flag=True
    print('Loop Start: ')
    scroll(driver,10)
#     driver.get_screenshot_as_file('Carhartt usa Second Page.png')
    list_of_pro_urls=[]
    while flag:
        try:
            driver.find_element(By.XPATH,'//div[@class="show-more-btn"]/button').click()
        except:
            flag=False
        
    products=driver.find_elements(By.XPATH,'//div[@class="info-container"]/a')
    print('Products find.')
    
    for num in range(len(products)):
        try:
            pro_url=products[num].get_attribute('href')
            list_of_pro_urls.append(pro_url)
        except:
#             print('Error in : ',num)
            continue
    print('Total Product find ',len(list_of_pro_urls))           
    print('Scrapping Start') 
    list_of_pro_urls = set(list_of_pro_urls)
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