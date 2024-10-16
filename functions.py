import requests
import pymysql
from config import db_config
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator
def translate(message):
    return GoogleTranslator(source='auto', target='en').translate(message)

def get_conversion_rate(From, To="USD", on=None):
    def getDate(date=datetime.today(),delta = -1):
        date = datetime.strptime(date, '%Y-%m-%d')
        date = date + timedelta(delta)
        date = datetime.strftime(date, '%Y-%m-%d')
        return date

    def normalizeCode(code):
        code = code.replace(" ", "").strip().lower()
        if 'pound' in code:
            code = "pound"
        elif 'dollar' in code:
            code = "dollar"
        
        data = {
            "yen":"jpy",
            "euro":"eur",
            "pound":"gbp",
            "dollar":"usd",
            "rupee":"inr",
            "yuan":"cny",
            "won":"krw",
            "franc":"chf",
            "ringgit":"myr",
            "baht":"thb",
            "krona":"sek",
            "dinar":"kwd",
            "dirham":"aed",
            "lira":"try",
            "real":"brl",
            "peso":"mxn",
            "ruble":"rub",
            "rand":"zar",
            "shekel":"ils",
        }
        if code in data:
            code = data[code]
        return code.upper()
    
    From = normalizeCode(From)
    To = normalizeCode(To)

    if not on:
        date = datetime.today().strftime('%Y-%m-%d')
    else:
        date = on
        
    while True:
        url = f'https://raw.githubusercontent.com/Dr-Aniket/conversion-rates/Core/Rates/{date}.json'
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return data[To]/data[From]
        else:
            date = getDate(date,-1)

connection = pymysql.connect(host=db_config["host"], user=db_config["user"], passwd=db_config["passwd"],database=db_config["database"], port=db_config["port"])
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