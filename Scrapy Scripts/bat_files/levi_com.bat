@echo off
cd /d E:\Scripts\Scrappy Scripts\Scripts Directory\myenv\Scripts
call activate.bat
cd E:\Scripts\Scrappy Scripts\Scripts Directory\levi_com\levi_com
scrapy crawl levi_com_scrape
