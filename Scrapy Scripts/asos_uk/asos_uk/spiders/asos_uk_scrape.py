from typing import Iterable
import scrapy

import sys
import os
import pandas as pd
from datetime import datetime
# Add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'common_lib')))

import  functions_for_call #type: ignore




class AsosUkScrapeSpider(scrapy.Spider):
    name = "asos_uk_scrape"
    headers = {
            'Cookie': 'browseCountry=IN;',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0'
        }
    data=[]
    not_processed_urls=[]
    def start_requests(self):
        
        scraping_json = {
                        "Men": {
                            "Jeans": "https://www.asos.com/men/jeans/cat/?cid=4208",
                            "Jacket": "https://www.asos.com/men/jackets-coats/cat/?cid=3606&currentpricerange=15-550&refine=attribute_1046:10811",
                            "Shorts": "https://www.asos.com/men/shorts/denim-shorts/cat/?cid=13138&ctaref=cat_header"
                        },
                        "Women": {
                            "Jeans": "https://www.asos.com/women/jeans/cat/?cid=3630",
                            "Bodysuit": "https://www.asos.com/women/jumpsuits-playsuits/denim-jumpsuits-playsuits/cat/?cid=19060&ctaref=cat_header",
                            "Jacket": "https://www.asos.com/women/coats-jackets/cat/?cid=2641&currentpricerange=15-550&refine=attribute_1046:10811",
                            "Shorts": "https://www.asos.com/women/shorts/denim-shorts/cat/?cid=10851&ctaref=cat_header",
                            "Skirt": "https://www.asos.com/women/skirts/denim-skirts/cat/?cid=15177&ctaref=cat_header"
                        }
                    }
        for category, items in scraping_json.items():
            for type_, url in items.items():
                yield scrapy.Request(url=url,headers=self.headers,callback=self.parse_page,
                                     meta={'category':category,'type':type_,'url':url})
        

    def parse_page(self, response):
        total_products=int(response.xpath('//*[contains(text(),"styles found")]/text()').get().split()[0].replace(',',''))
        url_path='//a[contains(@class, "productLink")]/@href'
        find_urls = response.xpath(url_path).getall()
        for page in range(1,int(total_products/len(find_urls))+2):
            url=f"{response.meta['url']}&page={page}"
            yield scrapy.Request(url=url,
                                headers=self.headers,
                                callback=self.find_urls,
                                meta={
                                    'category':response.meta['category'],
                                    'type':response.meta['type'],
                                    'page':page
                                    },
                                    dont_filter=True,
                                )
    def find_urls(self,response):
        url_path='//a[contains(@class, "productLink")]/@href'
        find_urls = response.xpath(url_path).getall()
        print('Total URL Found::>>', len(find_urls))
        for url in find_urls:
            yield scrapy.Request(url=url,
                                headers=self.headers,
                                callback=self.get_data,
                                meta={
                                    'category':response.meta['category'],
                                    'type':response.meta['type'],
                                    'page':response.meta['page']
                                    },
                                    dont_filter=True,
                                )
    

    def get_data(self,response):
        try:
            data_path = '//script[(@type="text/javascript") and (contains(text(),"productPrice"))]/text()'
            text =response.xpath(data_path).get()
            price_text = functions_for_call.get_values_between_string(t1='[',t2=']',text=text,find_word='config.stockPriceResponse')
            parse_url=response.url
            for i in price_text:
                if parse_url.count(str(i['productId'])):
                    new_price = i['productPrice']['current']['value']
                    old_price = i['productPrice']['previous']['value']
                    break
            products_text = functions_for_call.get_values_between_string(t1='{',t2='}',text=text,find_word='pdp.config.product = {"')

            name=products_text['name']
            
            image = next((i['url'] + '?$n_640w$&wid=513&fit=constrain' for i in products_text['images'] if 'imageType' in i.keys() and i['imageType'] == 'Standard1'), None)
            image=image.split('?')[0]+'?$n_1920w$&wid=1926&fit=constrain'
            description_text=functions_for_call.get_values_between_string(t1='{',t2='}',text=text,find_word='config.productDescription')
            replacements={'li':',','br':','}
            description= functions_for_call.extract_text_for_dic(description_text,replacements=replacements,list_of_not_wanted_keys=['careInfo'])
        except:
            self.not_processed_urls.append(response)
        try:
            product_code=products_text['productCode']
            description+=f'\nProduct Code: {product_code}'
        except:
            pass
        try:
            self.data.append(
                            [
                                name,new_price,old_price,description,image,parse_url,
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
                curr_symbol='£',
                brand_name='ASOS',
                country='UK'
                )
        
                                    
                                    
        
