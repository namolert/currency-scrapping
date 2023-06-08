import requests
import pandas as pd
import json
import numpy as np
from datetime import date
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
# import df2img #need pip ipython, nbformat
import dataframe_image as dfi
# import ssl

url = "https://ereport.uob.co.th/UOBWebFrontService/Exchange/FxRateEnNew.jsp?flags=LastFx"
bank_abbv_name = "UOB"
response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")
header = ["bank_abbv_name", "currency", "buying_rate", "selling_rate"]

table = soup.find('table', attrs={'border': '1', 'width': '100%', 'cellspacing': '0',
                                  'cellpadding': '2', 'bordercolor': '#B9DCFF'}).findAll('tr')
exc_val_list = []
for row in table:
    try:
        currency = row.find_all('td')[0].text.replace("\xa0", "").strip()
        exc_val_list.append([bank_abbv_name, currency                                     # sight buying
                             # ,"{:.4f}".format(float(row.find_all("td")[2].text))
                             # TT buying
                             # SELL
                            , "{:.4f}".format(float(row.find_all("td")[3].text)), "{:.4f}".format(float(row.find_all("td")[4].text))])
    except:
        pass
exc_val_df = pd.DataFrame(exc_val_list, columns=header)
exc_val_df['currency'] = exc_val_df['currency'].str.replace(
    'JPY (:100)', 'JPY')
div100 = float(
    exc_val_df.loc[exc_val_df['currency'] == 'JPY']['buying_rate'].values[0])/100
print(div100)
exc_val_df.loc[exc_val_df['currency'] ==
               'JPY', ['buying_rate']] = div100
# exc_val_df.loc[[2], 'buying_rate'] = div100

# print(float(exc_val_df.loc[exc_val_df['currency']
#       == 'JPY']['buying_rate'].values[0])/100)
print(exc_val_df)
