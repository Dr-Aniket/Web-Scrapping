from config import db_config # This is the database configuration file
import pymysql
import colorama
import pickle

##########################################################################################################################################

brands_links_table = 'brands_links'

colorama.init()
RED = colorama.Fore.LIGHTRED_EX
CYAN = colorama.Fore.CYAN
GREEN = colorama.Fore.LIGHTGREEN_EX
YELLOW = colorama.Fore.YELLOW
LIGHTYELLOW = colorama.Fore.LIGHTYELLOW_EX
MAGENTA = colorama.Fore.LIGHTMAGENTA_EX
DARKGREEN = colorama.Fore.GREEN
BLUE = colorama.Fore.BLUE
RESET = colorama.Fore.RESET

width = 50

dbConfig = db_config

##########################################################################################################################################

def getDataFromSql(cursor, query):
    try:
        cursor.execute(query)
        records = cursor.fetchall()
    except Exception as e:
        records = None
        print(f'{RED}Error: {e}')
    return records

def listToDict(data, heads):
    dictData = {}
    for i, head in enumerate(heads):
        dictData[head] = [row[i] for row in data]
    return dictData

def getData(cursor, tableName, condition = None, Sample = None, Random = False):
    if condition:
        condition = f'WHERE {condition}'
    else:
        condition = ''
    data = getDataFromSql(cursor, f"SELECT * FROM {tableName} {condition}")

    if Random:
        from random import shuffle
        shuffle(data)

    data = data[:Sample]

    data = list(map(list, data))

    return data

def getHeadings(cursor, tableName):
    heads = [head[0] for head in getDataFromSql(cursor, f"describe {tableName}")]
    return heads
# id	brand_name	country	product_category	run	category_link	products_in_db	manual_count	month
def get_db_links(connection,brand,country,get_brand_name=False,search_in='brand_name',other_column=None):
    cursor = connection.cursor()
    condition = f"{search_in} REGEXP '{brand}' AND country REGEXP '{country}'"
    data = getData(cursor, brands_links_table, condition)
    heads = getHeadings(cursor, brands_links_table)
    data = listToDict(data, heads)

    urls = {}
    brands = []
    other_data = {}

    for i in range(len(data['product_category'])):
        category = data['product_category'][i].strip()
        link = data['category_link'][i]
        run = data['run'][i]
        brand_name = data['brand_name'][i]


        if not run:
            continue
        if brand_name not in brands:
            brands.append(brand_name)
            
        if category in urls:
            j = 1
            while True:
                if category + ' ' + str(j) in urls:
                    j += 1
                else:
                    urls[category + ' ' + str(j)] = link
                    break
        else:
            urls[category] = link

        if other_column:
            other_column_data = data[other_column][i]
            other_data[category] = other_column_data

    no_of_urls = len(urls)


    if no_of_urls == 0:
        print(f'{MAGENTA}No Links Found for {brand} in {country}')
        exit()
    else:
        brand = data['brand_name'][0]
        country = data['country'][0]
        if get_brand_name:
            print(f'{YELLOW}{brands} {MAGENTA}|{LIGHTYELLOW} {country}')
        else:
            print(f'{YELLOW}{brand} {MAGENTA}|{LIGHTYELLOW} {country}')
        show_urls(urls)

    if get_brand_name:
        return urls, brands
    else:
        if other_column:
            return urls, other_data
        else:
            return urls

def show_urls(urls):
    for url in urls:
        print(f'{CYAN}{url}{RESET} : {GREEN}{urls[url]}')

    print(RESET)

# connection = pymysql.connect(host=db_config["host"], user=db_config["user"], passwd=db_config["passwd"],database=db_config["database"], port=db_config["port"])

# get_db_links(connection,'PRIMARK','UK')
