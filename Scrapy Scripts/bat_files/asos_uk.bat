@echo off
cd /d E:\Scripts\Scrappy Scripts\Scripts Directory\myenv\Scripts
call activate.bat
cd E:\Scripts\Scrappy Scripts\Scripts Directory\asos_uk\asos_uk
scrapy crawl asos_uk_scrape
