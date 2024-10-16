@echo off
cd /d E:\Scripts\Scrappy Scripts\Scripts Directory\myenv\Scripts
call activate.bat
cd E:\Scripts\Scrappy Scripts\Scripts Directory\torrid_usa\torrid_usa
scrapy crawl torrid_usa_scrape
