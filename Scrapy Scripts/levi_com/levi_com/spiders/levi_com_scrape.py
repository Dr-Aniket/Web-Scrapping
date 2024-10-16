import scrapy
import json
import requests
import sys
import os
import random
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'common_lib')))

import  functions_for_call # type: ignore

class LeviComScrapeSpider(scrapy.Spider):
    name = "levi_com_scrape"
    proxies=functions_for_call.fetch_proxies('BD')
    brand_name='LEVI STRAUSS AND CO.'
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9',
        'priority': 'u=0, i',
        'sec-ch-ua': '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
    }

    countries = {
            # 'Denmark': {'country_name': 'DK', 'country_en_code': 'en', 'currency_symbol': 'kr', 'source_lang': 'da'},
            # 'USA': {'country_name': 'US', 'country_en_code': 'en_US', 'currency_symbol': '$', 'source_lang': 'en'},
            # 'UK': {'country_name': 'GB', 'country_en_code': 'en_GB', 'currency_symbol': '£', 'source_lang': 'en'},
            # 'France': {'country_name': 'FR', 'country_en_code': 'en', 'currency_symbol': '€', 'source_lang': 'fr'},
            # 'Finland': {'country_name': 'FI', 'country_en_code': 'en', 'currency_symbol': '€', 'source_lang': 'fi'},
            # 'Germany': {'country_name': 'DE', 'country_en_code': 'en', 'currency_symbol': '€', 'source_lang': 'de'},
            # 'Italy': {'country_name': 'IT', 'country_en_code': 'en', 'currency_symbol': '€', 'source_lang': 'it'},
            # 'Netherlands': {'country_name': 'NL', 'country_en_code': 'en', 'currency_symbol': '€', 'source_lang': 'nl'},
            # 'Norway': {'country_name': 'NO', 'country_en_code': 'en', 'currency_symbol': 'kr', 'source_lang': 'no'},
            'Poland': {'country_name': 'PL', 'country_en_code': 'en', 'currency_symbol': 'zł', 'source_lang': 'pl'},
            'Sweden': {'country_name': 'SE', 'country_en_code': 'en', 'currency_symbol': 'kr', 'source_lang': 'sv'},
            'Spain': {'country_name': 'ES', 'country_en_code': 'en', 'currency_symbol': '€', 'source_lang': 'es'},
        }
    

    data = {}
    not_processed_urls = {}
    def start_requests(self):
        
        for country_code, details in self.countries.items():

            self.data[country_code] = []  # Initialize empty list for each country
            self.not_processed_urls[country_code] = []  # Initialize empty list for each country
            scraping_json=functions_for_call.script_config_data(
                brand=self.brand_name,country=country_code
            )
            for category, items in scraping_json.items():
                for type_, url in items.items():
                    proxy=random.choice(self.proxies)
                    formatted_url=url
                    yield scrapy.Request(url=formatted_url, 
                                        #  headers=self.headers, 
                                        callback=self.parse_page,
                                        meta={'category': category, 'type': type_, 
                                            'url': formatted_url, 'country_code': country_code,
                                            'proxy':proxy})

    def get_find_urls(self,response):
        base_url = 'https://www.levi.com'
        item_list = response.xpath('//a[contains(@class,"product-link")]/@href').getall()
        find_urls = [f"{base_url}{i}" for i in item_list]
        return list(set(find_urls))
    def get_total_urls(self,response):
        total_products=response.xpath('//div[contains(text(),"Items")]/text()').get()
        total_products = int(total_products.split()[0].replace(',',''))
        return total_products
    def create_new_page_url(self,response,page):
        if page==0:
            return response.url
        elif '?' in response.url:
            return f"{response.url}&page={page}"
        else:
            return f"{response.url}?page={page}"
    def parse_page(self, response):
        find_urls = self.get_find_urls(response)
        if find_urls:
            total_products=self.get_total_urls(response)
            total_pages=int(total_products/len(find_urls))+1
            print(f"{response.meta['category']} {response.meta['type']} {response.meta['country_code']} :: {total_products}:{total_pages}")
            for page in range(0,total_pages):
                new_url =  self.create_new_page_url(response,page)
                print(f"Page {page}, {new_url}")
                proxy=random.choice(self.proxies)
                yield scrapy.Request(url=new_url,
                                    callback=self.find_urls,
                                    headers=self.headers,
                                    meta={
                                        'category':response.meta['category'],
                                        'type':response.meta['type'],
                                        'page':page+1,
                                        'country_code': response.meta['country_code'],
                                        'proxy':proxy
                                        },
                                        dont_filter=True,
                                    )
    def find_urls(self,response):
        find_urls = self.get_find_urls(response)
        print(f'Page::>>> {response.meta["page"]} Total URL Found::>>{ len(find_urls)}')
        for url in find_urls:
            proxy=random.choice(self.proxies)
            yield scrapy.Request(url=url,
                                headers=self.headers,
                                callback=self.get_data,
                                meta={
                                    'category':response.meta['category'],
                                    'type':response.meta['type'],
                                    'page':response.meta['page'],
                                    'country_code': response.meta['country_code'],
                                    'proxy':proxy
                                    },
                                    dont_filter=True,
                                )
    
    def get_data(self,response):
        try:
            text= response.xpath('//script[contains(text(),"aggregateRating")]/text()').get()
            data = eval(functions_for_call.convert_string_for_eval(text))
            name=data['name']
            image_list=[i for i in data['image'] if 'laydownfront' in i]
            if not image_list:
                image_list=[i for i in data['image'] if 'modelfront_full' in i]
            if not image_list:
                image_list=[i for i in data['image']]
            image=image_list[0]
            text =response.xpath('//script[contains(text(),"window.internalTargetPageParams")]/text()').get()
            data = functions_for_call.get_values_between_string(t1='{',t2='}',text=text,find_word='return')
            new_price=data['entity.regularprice']
            old_price=data['entity.hardmarkdownprice']
            description = '\n'.join(response.xpath('//div[@class="contentContainer"]//text()').getall())
        except Exception as e:
            # import pdb; pdb.set_trace()
            self.not_processed_urls[response.meta['country_code']].append(response)  
        try:
            self.data[response.meta['country_code']].append(
                            [
                                name,new_price,old_price,description,image,response.url,
                                response.meta['category'],response.meta['type'],response.meta['page']
                            ]
            )
        except:
            pass
        
        
    def get_not_p_data(self,list_of_response):
        for response in list_of_response:
            yield scrapy.Request(url=response.url,
                                headers=self.headers,
                                callback=self.get_data,
                                meta=response.meta
                                )
    def close(self, reason):
        # Process unprocessed URLs
        for country_code, responses in self.not_processed_urls.items():
            self.get_not_p_data(responses)
        
        # Insert data into SQL for each country
        for country_code, data_entries in self.data.items():
            if data_entries:
                country_name = country_code
                currency_symbol = self.countries[country_code]['currency_symbol']
                functions_for_call.insert_dataframe_to_sql(
                    data=data_entries,
                    curr_symbol=currency_symbol,
                    brand_name=self.brand_name,
                    country=country_name,
                )