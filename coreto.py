###############################################################################
# Script to get alerts from Coreto
# By: Viviana Márquez
###############################################################################
import os
from twilio.rest import Client

import bs4 as bs
import unidecode
import urllib.request

import time
import random
import pandas as pd
from datetime import datetime


###############################################################################
# Scrape Coin Market Cap for Coreto's Price
###############################################################################
# Random pause to avoid being detected
pause = random.randrange(111)
if pause%10==0:
    exit()
    
time.sleep(pause)

link = "https://coinmarketcap.com/currencies/coreto/"

request = urllib.request.Request(link, headers={'User-Agent': 'Mozilla/5.0'})

webpage = urllib.request.urlopen(request)
source = webpage.read()
webpage.close()

current_time = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
soup = bs.BeautifulSoup(source, 'html.parser')

price = unidecode.unidecode(soup.find(class_="price").text).split()[1]
pct = unidecode.unidecode(soup.find(class_="price").text).split()[2]


###############################################################################
# Save results to a dataframe
###############################################################################
try:
    df = pd.read_csv("coreto_price.csv")
    temp = pd.DataFrame([(current_time, price, pct, True)], columns = ["time", "price", "pct", "flag"])
    df = pd.concat([df, temp], ignore_index=True)
    df.to_csv("coreto_price.csv", index=False)
except:
    df = pd.DataFrame([(current_time, price, pct, True)], columns = ["time", "price", "pct", "flag"])
    df.to_csv("coreto_price.csv", index=False)


###############################################################################
# Send text message using Twilio
###############################################################################
# Find difference between the last sent price and current price
latest_prices = df[df.flag].iloc[-2:].price.apply(lambda val: float(val[1:])).values
diff = abs(latest_prices[0]-latest_prices[1])

# Excecute code if difference is higher than USD$0.005 
flag = diff>0.02

def send_msg(text, number, sender):
    message = client.messages.create(body=text, from_=sender, to=number)

if flag:
    # Read Twilio credentials and authenticate
    keys = pd.read_csv("twilio.csv", header=None)
    keys = dict(zip(keys[0],keys[1]))

    client = Client(keys['account_sid'], keys['auth_token'])
    
    # Read target phone numbers
    phones = pd.read_csv("phones.csv", header=None)
    phones[1] = phones[1].apply(lambda val: f"+{str(val)}")
    phones = dict(zip(phones[0],phones[1]))
    
    # Compose text message
    msg = f"Lapi 🐰❤️ Coreto's price is {price}. Price changed ${diff} from last text message. Scraped @ {current_time}"
    
    for person in phones:
        number = phones[person]
        send_msg(msg, number, keys['sender'])
        
else:
    temp.flag = ~temp.flag
    df = pd.concat([df.iloc[:-1], temp], ignore_index=True)
    df.to_csv("coreto_price.csv", index=False)


print(f"Done @ {datetime.now().strftime('%m/%d/%Y, %H:%M:%S')}")
