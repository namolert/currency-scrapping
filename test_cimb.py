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

url = "https://www.cimbthai.com/en/personal/help-support/rates-charges/foreign-exchange-rates.html"
bank_abbv_name = "CIMB"
# response = requests.get(url)
# soup = BeautifulSoup(response.text, "html.parser")

options = Options()
options.headless = True
driver = webdriver.Chrome(
    '~/Downloads/chromedriver_mac64/chromedriver', options=options)
driver.get(url)
exc_val_df = pd.read_html(driver.find_element(
    By.XPATH, '//table').get_attribute('outerHTML'), encoding='utf-8')[0]

exc_val_df = exc_val_df[['Currency Code', 'Buying Rates', 'Selling Rates']]
exc_val_df.columns = ['_'.join(col) for col in exc_val_df.columns.values]
exc_val_df.rename(columns={
    'Currency Code_Currency Code': 'currency',
    'Buying Rates_Unnamed: 2_level_1': 'buying_rate',
    'Selling Rates_Telegraphic Transfer': 'selling_rate'},
    inplace=True)
exc_val_df = exc_val_df[['currency', 'buying_rate', 'selling_rate']].drop_duplicates(
    'currency', keep='first')
exc_val_df = exc_val_df[(exc_val_df['buying_rate'] != '-') & (
    exc_val_df['selling_rate'] != '-')]
exc_val_df.loc[exc_val_df['currency'] ==
               'USD50-100', 'currency'] = 'USD'

exc_val_df["selling_rate"] = exc_val_df["selling_rate"].apply(
    lambda x: "{:.4f}".format(float(x)))
exc_val_df["buying_rate"] = exc_val_df["buying_rate"].apply(
    lambda x: "{:.4f}".format(float(x)))
exc_val_df["bank_abbv_name"] = bank_abbv_name

print(exc_val_df)
