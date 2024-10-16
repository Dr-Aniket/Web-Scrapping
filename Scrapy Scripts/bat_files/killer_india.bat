@echo off
cd /d E:\Scripts\Scrappy Scripts\Scripts Directory\myenv\Scripts
call activate.bat
cd E:\Scripts\Scrappy Scripts\Scripts Directory\killer_india\killer_india
scrapy crawl killer_india_scrape
