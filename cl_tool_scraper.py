"""
Craigslist scraper - 
By: Andre Kvaternik, September 2019
"""

import csv
from datetime import datetime
import sys
import time
import logging
import requests

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from urllib.parse import urljoin  # PY3
from bs4 import BeautifulSoup
import urllib.request

# _____________________________________________________________________________________________________________________
#   define some constants and variables 
# _____________________________________________________________________________________________________________________
cl_search_input_file = r'C:\Users\Andre\Google Drive\GitHub\craigslist_scraper\cl_search_input.csv'
location        = "sfbay"
zipcode         = "94566"
driver          = webdriver.Chrome()  
delay           = 5
listing_info    = []
# _____________________________________________________________________________________________________________________
#   define function to call when ready to create search URL
# _____________________________________________________________________________________________________________________
def create_search_url(location,category,searchterm,radius,zipcode,min_price,max_price):
  
    search_url = \
    "https://" + location + \
    ".craigslist.org/search/" + category + \
    "?sort=pricedsc" + \
    "&query=" + searchterm + \
    "&search_distance=" + radius + \
    "&postal=" + zipcode + \
    "&min_price=" + min_price + \
    "&max_price=" + max_price
    return (search_url)

# _____________________________________________________________________________________________________________________
#    Open and read the csv file containing the input parmeters for the search
# _____________________________________________________________________________________________________________________
with open(cl_search_input_file) as csv_file:
    reader = csv.DictReader(csv_file)
    for inputrow in reader:
        line_count = 0
        # _____________________________________________________________________________________________________________________
        #    create search URL and call it
        # _____________________________________________________________________________________________________________________
        search_term = create_search_url(location,inputrow['category'],inputrow['searchterm'],inputrow['radius'],zipcode,inputrow['min_price'],inputrow['max_price'])         
        response = requests.get(search_term)
        
        try:
            wait = WebDriverWait(driver,delay)
            wait.until(EC.presence_of_element_located((By.ID, "searchform")))
            print("Page is ready")
        except TimeoutException:
            print("Loading took too much time")
        # _____________________________________________________________________________________________________________________
        #    Now parse the resulting output and put the results into an array for unloading later
        # _____________________________________________________________________________________________________________________
        soup = BeautifulSoup(response.content,'html.parser')
        rows = soup.find('ul', {'class': 'rows'})

        for row in rows.find_all('li', {'class': 'result-row'},recursive=False):

            id = row.attrs['data-pid']
            time = row.find('time')
            price = row.find('span', {'class': 'result-price'})
            
            where = row.find('span', {'class': 'result-hood'})
            if where:
                where = where.text.strip()[1:-1]
            else:
                where = " "    
                
            link = row.find('a', {'class': 'hdrlnk'})
            name = link.text
            url = link.attrs['href']
            
            post_time = row.find('time', {'class' : 'result-date'})["datetime"]
            if not post_time:
                post_time = ""
                
            listing_info.append(
            inputrow['searchterm'] + "|" + 
            name + "|" + 
            where + "|" + 
            price.text + "|" + 
            str(post_time) + "|" + 
            url 
            )
            
print ("There are %s entries in the returned array" %(len(listing_info)))
 
for x in range(len(listing_info)):
    print("array = %s" %(listing_info[x]))

driver.close