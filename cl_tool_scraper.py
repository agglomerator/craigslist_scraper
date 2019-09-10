"""
Craigslist scraper - 
By: Andre Kvaternik, September 2019
"""

import csv
from datetime import datetime
import sys
import time
import logging
import logging.handlers
from logging.handlers import TimedRotatingFileHandler
import requests

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from urllib.parse import urljoin  # PY3
from bs4 import BeautifulSoup
import urllib.request

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.message import EmailMessage
# _____________________________________________________________________________________________________________________
#   define some constants and variables 
# _____________________________________________________________________________________________________________________
cl_search_input_file    = r'C:\Users\Andre\Google Drive\GitHub\craigslist_scraper\cl_search_input.csv'
location                = "sfbay"
zipcode                 = "94566"
#driver                  = webdriver.Chrome()  
delay                   = 5
listing_info            = []
start_stop_str          = '_' * 150
header_prefix           = ('*' * 15)
# _______________________________________________________________________________________
# declare a bunch of variables for use in sending email via Gmail
# this is documented at https://www.interviewqs.com/blog/py_email

# Create message container - the correct MIME type is multipart/alternative.
# Credentials for sending email from Kvaternik.com

gmail_sender    = 'scraper@kvaternik.com'
gmail_passwd    = 'kmqbpfgdxmahoijr'
from_address    = 'scraper@kvaternik.com'
user_email      = 'andre+craigstlist@kvaternik.com'

msg_body_start  = """\
<html>
  <head></head>
  <body>
"""

msg_body_end = """ \
    </body>
</html>
"""

#   ___________________setup logging ____________________________________________
def logger_setup():
    global logger
    logger = logging.getLogger(__name__)
    logging.getLogger().setLevel(logging.INFO)
    log_format = '%(asctime)-15s %(message)s'
    logformatter = logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s',datefmt='%Y-%a-%b-%d %H:%M:%S')
    logging.basicConfig(
        format=log_format,
        level=logging.INFO)

    logname = r'C:\Users\Andre\OneDrive - Instor Solutions\Documents\Andre_Stuff\craigslist\craigslist_scraping.log'
    loghandler = TimedRotatingFileHandler(logname,
                                          when='midnight',
                                          interval=1,
                                          backupCount=3)
    loghandler.suffix = '%Y%m%d'
    logger.addHandler(loghandler)
    loghandler.setFormatter(logformatter)

#   ___________________ Define a function to indent log files ____________________________________________
def indent(level):
    indent = ' ' * 4 * level
    return indent

def html_indent(level):
    html_indent = "&nbsp;" * 5 * level
    return html_indent


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

#  ________________  create startup procedure__________________________________________________________________________

def startup_procedure():
    logger.info(' ' * 120)
    logger.info(start_stop_str)
    logger.info('%s Python Craigslist Scraper Script %s Started %s',header_prefix,sys.argv[0],header_prefix)
    
#  ________________  Start proeessing _________________________________________________________________________    

if __name__ == "__main__":
    logger_setup()    
    startup_procedure()
# _____________________________________________________________________________________________________________________
#    Open and read the csv file containing the input parmeters for the search
# _____________________________________________________________________________________________________________________
with open(cl_search_input_file) as csv_file:
    reader = csv.DictReader(csv_file)

    line_count = 0    
    for inputrow in reader:
        line_count += 1        
        # _____________________________________________________________________________________________________________________
        #    create search URL and call it
        # _____________________________________________________________________________________________________________________
        search_term = create_search_url(location,inputrow['category'],inputrow['searchterm'],inputrow['radius'],zipcode,inputrow['min_price'],inputrow['max_price'])         
        response = requests.get(search_term)

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
# _____________________________________________________________________________________________________________________
#    Now create an email with the results of the search
# _____________________________________________________________________________________________________________________        

hold_searchterm     = ''
msg_links           = ''
msg_html            = ''
email_body          = ''              

for x in range(len(listing_info)):
    search_results = listing_info[x].split("|")
    if hold_searchterm != search_results[0]:
        msg_links       = msg_links + '<br><b>' + search_results[0] + '</b>' 
        hold_searchterm = search_results[0]
        
    indent_string   = ("&nbsp;" * 10 * 1)
    email_body = email_body + '<br>' + indent_string  + '<a href="' + search_results[5] + '">' + search_results[1] + '</a>' + \
    + ", Location = " + search_results[2] + ", Price = " + search_results[3] + ", Post Date = " + search_results[4] 

# _____________________________________________________________________________________________________________________
#    Setup the SMTP fields and send the email
# _____________________________________________________________________________________________________________________   
msg_links       = msg_links + email_body
msg_html        = msg_body_start  +  msg_links + '\n' + msg_body_end
msg             = MIMEMultipart('alternative')
subject_text    = ' '
msg['Subject']  = 'Craigslist Scraper Results'
msg['From']     = from_address
msg['To']       = user_email
body            = MIMEText(msg_html, 'html')
msg.attach(body)

# SMTP setup for gmail
server          = smtplib.SMTP('smtp.gmail.com', 587)
server.ehlo()
server.starttls()
server.login(gmail_sender,gmail_passwd)
try:
    server.sendmail(from_address, user_email, msg.as_string())
    print("email successfully sent...")
    server.quit()
except:
    print ('error sending mail') 

logger.info('%sThere were %s input lines in the Craigslist search query file...', indent(0), line_count)
logger.info('%sThere were %s search results returned from the query...', indent(0), len(listing_info))
logger.info('_' * 120)
logger.info('%s Python Craigslist Scraping Script Completed %s',header_prefix,header_prefix)