import requests
import json
import pymysql
from config import db_config # this contains the database configuration
import logging
import os

class Common:
    logging.basicConfig(filename='db.log', filemode='w', format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')

    connection = pymysql.connect(host=db_config["host"], user=db_config["user"], passwd=db_config["passwd"],
                                 database=db_config["database"], port=db_config["port"])

    lang = {
        "eur": "eur",
        "hkd": "hkd",
        "cad": "cad",
        "inr": "inr",
        "aud": "aud",
        "gbp": "gbp",
        "sgd": "sgd",
        "try": "try",
        "sek": "sek",
        "pln": "pln",
        "cny": "cny",
        "chf": "chf"
    }

    @staticmethod
    def connect():
        Common.connection = pymysql.connect(host=db_config["host"], user=db_config["user"], passwd=db_config["passwd"],database=db_config["database"], port=db_config["port"])
        return Common.connection

    @staticmethod
    def addData(connection, data):
        try:
            with connection.cursor() as cursor:
                sql = "INSERT INTO `brands_data` (`brand_name`, `product_link`, `product_name`, `product_category`, `product_type`, `product_price`, `discounted_price`, `price_unit`, `price_usd`, `product_description`, `product_image`, `country`, `page_numer`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                cursor.executemany(sql, data)

            connection.commit()

        except Exception as e:
            logging.error(f"DB_Insertion_Error: {e}")
            print(e)
            return False
        
        return True

    @staticmethod
    def translate_to_english(source_lang="auto", target_lang="en", message="") -> str:
        try:
            with requests.get(
                    f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={source_lang}&tl={target_lang}&dt=t&q={message}") as response:
                data = json.loads(response.text)
                data = data[0]

                desc = ""

                for text in data:
                    desc += text[0]
            return desc
        except:
            return ""