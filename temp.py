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

url = "https://www.bangkokbank.com/en/Personal/Other-Services/View-Rates/Foreign-Exchange-Rates"
bank_abbv_name = "BBL"
# response = requests.get(url)
# soup = BeautifulSoup(response.text, "html.parser")

options = Options()
options.headless = True
driver = webdriver.Chrome(
    '~/Downloads/chromedriver_mac64/chromedriver', options=options)
driver.get(url)
exc_val_df = pd.read_html(driver.find_element(
    By.XPATH, '//table').get_attribute('outerHTML'), encoding='utf-8')[0]

exc_val_df.rename(columns={
    'Currency': 'currency', 'Bank Notes Buying Rates': 'buying_rate', 'Bank Notes Selling Rates': 'selling_rate'}, inplace=True)
exc_val_df = exc_val_df[['currency', 'buying_rate', 'selling_rate']].drop_duplicates(
    'currency', keep='first')
exc_val_df = exc_val_df[(exc_val_df['buying_rate'] != '-') & (
    exc_val_df['selling_rate'] != '-')]

exc_val_df["selling_rate"] = exc_val_df["selling_rate"].apply(
    lambda x: "{:.4f}".format(float(x)))
exc_val_df["buying_rate"] = exc_val_df["buying_rate"].apply(
    lambda x: "{:.4f}".format(float(x)))
# exc_val_df.loc[:, "currency"] = exc_val_df.loc[:,
#                                                "currency"].apply(lambda x: x.split('  ')[0])
exc_val_df["bank_abbv_name"] = bank_abbv_name
print(exc_val_df)
