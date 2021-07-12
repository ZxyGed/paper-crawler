import os
import time
import json
import requests
from pyquery import PyQuery as pq
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from papercrawler import PaperCrawler

options = webdriver.ChromeOptions()
options.add_argument('enable-webgl')
# 如果想要监测浏览器运行，注释掉这一项
# options.add_argument('headless')
options.add_experimental_option(
    "excludeSwitches", ['enable-automation', 'enable-logging'])
options.add_experimental_option('useAutomationExtension', False)
options.add_experimental_option("prefs",
                                {"profile.password_manager_enabled": False, "credentials_enable_service": False})

browser = webdriver.Chrome(options=options)
browser.maximize_window()
crawler = PaperCrawler('tensor', 'NIPS', 2019, 'E:/test', browser)
# print(crawler.base)
# crawler.fetchPaper(
#     'Modeling Shared responses in Neuroimaging Studies through MultiView ICA')
# paperList=['a','b','c']
# crawler.savePaperList('E:/test', 'test.json', paperList)
# crawler.crawl()
print(crawler.checkTotalPaperList())
