import scrapy

import sys
import os
import re
import json
import pandas as pd
from datetime import datetime
from io import StringIO

# Add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'common_lib')))

import  functions_for_call # type: ignore

class KillerIndiaScrapeSpider(scrapy.Spider):
    name = "killer_india_scrape"
    data=[]
    not_processed_urls=[]
    
    
    
    def start_requests(self):
        scraping_json = {
            'Men': {
                'Jeans': 'https://www.killerjeans.com/killer-bottom-wear/killer-jeans?page=1'
                }
        }
        for category, items in scraping_json.items():
            for type_, url in items.items():
                yield scrapy.Request(url=url,callback=self.parse_page,
                                     meta={'category':category,'type':type_,'url':url,
                                           })
        
    def get_find_urls(self,response):
        text = response.xpath("//script[(contains(text(),'ListItem')) and (contains(text(),'url'))]/text()").get()
        data=json.loads(text)['itemListElement']
        find_urls = [item['url'] for item in data]
        return find_urls
    def get_page_found(self,response):
        text=response.xpath('//input[@id="total_pages"]/@value').get()
        total_pages = int(text)
        return total_pages
    def create_new_page_url(self,response,page):
        new_url = response.url.replace(f'page=1',f'page={page+1}')
        return new_url
    def parse_page(self, response):
        find_urls = self.get_find_urls(response)
        if find_urls:
            total_pages=self.get_page_found(response)
            for page in range(0,total_pages):
                new_url =  self.create_new_page_url(response,page)
                print(f"Page {page}, {new_url}")
                yield scrapy.Request(url=new_url,
                                    callback=self.find_urls,
                                    meta={
                                        'category':response.meta['category'],
                                        'type':response.meta['type'],
                                        'page':page+1,
                                        # 'proxy':self.proxies[0]
                                        },
                                        dont_filter=True,
                                    )

    def find_urls(self,response):
        find_urls = self.get_find_urls(response)
        print('Total URL Found::>>', len(find_urls))
        for url in find_urls:
            yield scrapy.Request(url=url,
                                callback=self.get_data,
                                meta={
                                    'category':response.meta['category'],
                                    'type':response.meta['type'],
                                    'page':response.meta['page'],
                                    # 'proxy':self.proxies[0]
                                    },
                                    dont_filter=True,
                                )


    def get_data(self,response):
        try:
            data_path = '//script[contains(text(),"singleProduct.mrp")]/text()'
            text =response.xpath(data_path).get()
            pattern = re.compile(r"(var|singleProduct)\s*([\w\.]+)\s*=\s*([^;]+);")

            # Dictionary to store the variables and their values
            data = {}

            # Find all matches and add them to the dictionary
            matches = pattern.findall(text)
            for match in matches:
                var_name = f"{match[0]} {match[1]}"
                var_value = match[2].strip().strip('{}[]')
                data[var_name] = var_value
            new_price = data['singleProduct .price']
            old_price = data['singleProduct .mrp']
            name=data['singleProduct .name'].split('|')[0]
            if name[0]=="'":
                name=name[1:]
            text2=response.xpath('//script[contains(text(),"priceCurrency")]/text()').get()
            data2=eval(text2[text2.index('{'):])
            image=data2['image']
            image = re.sub(r',h-\d+,w-\d+b',',h-1080,w-812',image)
            description = data2['description']
            tables = response.xpath('//table[@class="table"]').getall()
            for table in tables:
                df=pd.read_html(StringIO(table))[0]
                description += '\n'+'\n'.join(f"{row[0]} : {row[1]}" for row in df.itertuples(index=False))
            description='\n'.join(response.xpath('//div[@class="description"]//text()').getall())+'\n'+description
        except Exception as e:
            print(f'Error::>>{e}')
            self.not_processed_urls.append(response)  
        try:
            self.data.append(
                            [
                                name,new_price,old_price,description,image,response.url,
                                response.meta['category'],response.meta['type'],response.meta['page']
                            ]
            )
            print(f"Data Collected Successfully")
        except:
            pass
        
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
                curr_symbol='₹',
                brand_name='Killer',
                country='INDIA'
                )
       