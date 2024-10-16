import scrapy

import sys
import os
import re
import pandas as pd
from datetime import datetime
from scrapy import Spider
import random

# Add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'common_lib')))

import  functions_for_call  # type: ignore
class TorridUsaScrapeSpider(scrapy.Spider):
    name = "torrid_usa_scrape"
    # proxies=functions_for_call.fetch_proxies('US')
    data=[]
    not_processed_urls=[]
    
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
    }  
    
    def start_requests(self):
        scraping_json = {
            'Women': {
                'Jeans': 'https://www.torrid.com/clothing/jeans/', 
                'Shorts': 'https://www.torrid.com/clothing/bottoms/shorts/jean-shorts/?', 
                'Jacket': 'https://www.torrid.com/clothing/jackets/jean-jackets-vests/'
                }
            }
        for category, items in scraping_json.items():
            for type_, url in items.items():
                # proxy = random.choice(self.proxies)
                yield scrapy.Request(url=url,headers=self.headers,callback=self.parse_page,
                                     meta={'category':category,'type':type_,'url':url,
                                        #    'proxy':proxy
                                           })
        
    def get_find_urls(self,response):
        base_url='https://www.torrid.com/product'
        text=response.xpath('//script[contains(text(),"cq_params.products")]/text()').getall()
        pattern = r"id:\s*'([^']*)'" 
        find_urls = [f"{base_url}/{re.search(pattern, t).group(1)}.html" for t in text] 
        return find_urls
    def get_total_urls(self,response):
        total_products=response.xpath('//div[@class="category-product-count"]/text()').get().replace('(','').split()[0]
        return int(total_products)
    def create_new_page_url(self,response,page):
        new_url = f"{response.url}?start={(page-1)*60}&sz={(page)*60}"
        return new_url
    def parse_page(self, response):
        find_urls = self.get_find_urls(response)
        if find_urls:
            total_products=self.get_total_urls(response)
            total_pages=int(total_products/len(find_urls))+2
            for page in range(1,total_pages):
                new_url =  self.create_new_page_url(response,page)
                # proxy = random.choice(self.proxies)
                yield scrapy.Request(url=new_url,
                                    headers=self.headers,
                                    callback=self.find_urls,
                                    meta={
                                        'category':response.meta['category'],
                                        'type':response.meta['type'],
                                        'page':page+1,
                                        # 'proxy':proxy
                                        },
                                        dont_filter=True,
                                    )

    def find_urls(self,response):
        find_urls = self.get_find_urls(response)
        print('Total URL Found::>>', len(find_urls))
        for url in find_urls:
            # proxy = random.choice(self.proxies)
            yield scrapy.Request(url=url,
                                headers=self.headers,
                                callback=self.get_data,
                                meta={
                                    'category':response.meta['category'],
                                    'type':response.meta['type'],
                                    'page':response.meta['page'],
                                    # 'proxy':proxy
                                    },
                                    dont_filter=True,
                                )


    def get_data(self,response):
        try:
            data_path = '//script[(contains(text(),"productID")) and (contains(text(),"AggregateRating"))]/text()'
            text =response.xpath(data_path).get()
            data = eval(text.strip())
            price_data_path ='//script[(contains(text(),"utag_data")) and (contains(text(),"page_name"))]/text()'
            price_text =response.xpath(price_data_path).get()
            price_text = price_text.strip().replace('\n',' ').replace('false','False').replace('true','True')
            price_text=price_text[price_text.index('{'):-1]
            price_data = eval(price_text)
            new_price = price_data['product_final_price'][0]
            old_price = price_data['product_price'][0]
            name=data['name']
            image=data['image'].replace('standard','desktop_main')
            description= data['description']
        except:
            self.not_processed_urls.append(response)
        try:
            self.data.append(
                            [
                                name,new_price,old_price,description,image,response.url,
                                response.meta['category'],response.meta['type'],response.meta['page']
                            ]
            )
        except:
            pass
        print(f"Data Collected Successfully")
        
    def get_not_p_data(self,list_of_response):
        for response in list_of_response:
            yield scrapy.Request(url=response.url,
                                headers=self.headers,
                                callback=self.get_data,
                                meta=response.meta
                                )

    def close(self,reason):
        self.get_not_p_data(self.not_processed_urls)
        if self.data:
            functions_for_call.insert_dataframe_to_sql(
                data = self.data,
                curr_symbol='$',
                brand_name='Torrid',
                country='USA'
                )
        
        