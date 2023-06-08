import requests
import pandas as pd
import json
import numpy as np
from datetime import date
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import os
# import df2img #need pip ipython, nbformat
import dataframe_image as dfi
# import ssl

# ssl._create_default_https_context = ssl._create_unverified_context
today = date.today().strftime('%Y-%m-%d')


def highlight_rows(x):
    if x['currency'] == 'EUR':
        return ['background-color: lightblue']*8
    else:
        return ['background-color: pink']*8


def save_dataframe_image(df, name):
    # df_styled = df.style.background_gradient(max_rows = -1, max_cols = -1)
    dfi.export(df, name+"2.png", max_rows=-1)
    print('Success dataframe_image')

# def save_df2img(df,name):
#     n_row = df.shape[0]
#     n_col = df.shape[1]
#     fig = df2img.plot_dataframe(
#         df,
#         title=dict(
#             font_color="darkblue",
#             #font_family="Times New Roman",
#             font_size=30,
#             text="Test Report",
#         ),
#         tbl_header=dict(
#             align="center",
#             fill_color="lightblue",
#             font_color="black",
#             font_size=16,
#             line_color="white",
#         ),
#         tbl_cells=dict(
#             align="right",
#             line_color="white",
#         ),
#         row_fill_color=("#ffffff", "#d7d8d6"),
#         fig_size=(n_col*200, 100+n_row*20),
#     )
#     df2img.save_dataframe(fig=fig, filename=name+".png")
#     print('Success df2img')


def selected_currency(df, cur_list):
    if cur_list is not None:
        if type(cur_list) != list:
            return 'Error: selected currency list is not list type'
        cur_list = [x.upper() for x in cur_list]
        df = df.loc[df["currency"].isin(cur_list), :].reset_index(drop=True)
    return df


def scrape_website(bank_abbv_name, url, selected_cur_list=None):
    bank_abbv_name = bank_abbv_name.upper()
    header = ["bank_abbv_name", "currency", "buying_rate", "selling_rate"]
    if bank_abbv_name not in ('KTB TRAVEL CARD'):  # use bs4
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
    # Find the table containing the exchange rates
    if bank_abbv_name == 'KBANK JOURNEY':
        # kbank journey card has only selling price
        exc_val = soup.find("input", {"name": "ctl01$hdnData"})['value']
        exc_val_list = json.loads(exc_val)
        exc_val_df = pd.DataFrame.from_dict(exc_val_list)
        # cleaning column values
        exc_val_df.columns = exc_val_df.columns.str.lower()
        exc_val_df["buying_rate"] = np.nan
        exc_val_df.rename(columns={"hotrates": "selling_rate"}, inplace=True)
        exc_val_df["selling_rate"] = exc_val_df["selling_rate"].apply(
            lambda x: "{:.4f}".format(float(x)))
        exc_val_df["bank_abbv_name"] = bank_abbv_name
        # select currency
        exc_val_df = selected_currency(exc_val_df, selected_cur_list)
        exc_val_df = exc_val_df[header]
    elif bank_abbv_name == 'BAY BOARDING':
        table = soup.find(
            "table", {"class": "table table-borderless"})
        tbody = table.findChildren("tbody")[0]
        exc_val_list = []
        for row in tbody:
            exc_val_list.append([bank_abbv_name, row.find_all("td")[0].text, "{:.4f}".format(
                float(row.find_all("td")[2].text)), "{:.4f}".format(float(row.find_all("td")[1].text))])
        exc_val_df = pd.DataFrame(exc_val_list, columns=header)
        exc_val_df = selected_currency(exc_val_df, selected_cur_list)
    elif bank_abbv_name == 'TTB':
        # many rounds so pic the latest round
        tbody = soup.find("tbody")
        exc_val_dict = {}
        for row in tbody:
            try:
                if row.find("h6").text == 'USD':
                    exc_val_dict[row.find("small").text] = ["{:.4f}".format(float(row.find_all(
                        "td")[3].text)), "{:.4f}".format(float(row.find_all("td")[5].text))]
                else:
                    exc_val_dict[row.find("h6").text] = ["{:.4f}".format(float(row.find_all(
                        "td")[3].text)), "{:.4f}".format(float(row.find_all("td")[5].text))]
            except:
                # print('Found some error in TTB scrapping but be able to ignore')
                pass
        exc_val_list = []
        for key in exc_val_dict:
            exc_val_list.append(
                [bank_abbv_name, key, exc_val_dict[key][0], exc_val_dict[key][1]])
        exc_val_df = pd.DataFrame(exc_val_list, columns=header)
        exc_val_df = selected_currency(exc_val_df, selected_cur_list)
        exc_val_df = exc_val_df[(exc_val_df['buying_rate'] != '') & (
            exc_val_df['selling_rate'] != '')]
        exc_val_df['currency'] = exc_val_df['currency'].str.strip()
        exc_val_df.loc[exc_val_df['currency'] ==
                       'USD DENO. $ : 50-100', 'currency'] = 'USD'
        exc_val_df.loc[exc_val_df['currency']
                       == 'JPY : 100', 'currency'] = 'JPY'
    elif bank_abbv_name == 'KTB TRAVEL':
        options = Options()
        options.add_argument("--headless")  # Run the browser in headless mode (without a GUI)

        # Set the path to ChromeDriver executable
        chrome_driver_path = os.path.expanduser("~/Downloads/chromedriver_mac64/chromedriver")
        os.environ["PATH"] += os.pathsep + chrome_driver_path
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        exc_val_df = pd.read_html(driver.find_element(
            By.XPATH, '//table').get_attribute('outerHTML'), encoding='utf-8')[0]
        exc_val_df.columns = header
        exc_val_df.loc[exc_val_df["selling_rate"]
                       == 'Unq', "selling_rate"] = np.nan
        exc_val_df["selling_rate"] = exc_val_df["selling_rate"].apply(
            lambda x: "{:.4f}".format(float(x)))
        exc_val_df.loc[exc_val_df["selling_rate"]
                       == 'nan', "selling_rate"] = ''
        exc_val_df['bank_abbv_name'] = bank_abbv_name
        exc_val_df = selected_currency(exc_val_df, selected_cur_list)
    elif bank_abbv_name == 'SUPERRICH GREEN':
        options = Options()
        options.add_argument("--headless")  # Run the browser in headless mode (without a GUI)

        # Set the path to ChromeDriver executable
        chrome_driver_path = os.path.expanduser("~/Downloads/chromedriver_mac64/chromedriver")
        os.environ["PATH"] += os.pathsep + chrome_driver_path
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        exc_val_df = pd.read_html(driver.find_element(
            By.XPATH, '//table').get_attribute('outerHTML'), encoding='utf-8')[0]
        exc_val_df.columns = exc_val_df.iloc[0]
        exc_val_df = exc_val_df.iloc[1:]
        exc_val_df.rename(columns={
                          'CURRENCY': 'currency', 'BUYING RATE': 'buying_rate', 'SELLING RATE': 'selling_rate'}, inplace=True)
        exc_val_df = exc_val_df[['currency', 'buying_rate', 'selling_rate']].drop_duplicates(
            'currency', keep='first')
        exc_val_df["selling_rate"] = exc_val_df["selling_rate"].apply(
            lambda x: "{:.4f}".format(float(x)))
        exc_val_df["buying_rate"] = exc_val_df["buying_rate"].apply(
            lambda x: "{:.4f}".format(float(x)))
        exc_val_df.loc[:, "currency"] = exc_val_df.loc[:,
                                                       "currency"].apply(lambda x: x.split('  ')[0])
        exc_val_df["bank_abbv_name"] = bank_abbv_name
        exc_val_df = selected_currency(exc_val_df, selected_cur_list)
    elif bank_abbv_name == 'BBL':
        options = Options()
        options.add_argument("--headless")  # Run the browser in headless mode (without a GUI)

        # Set the path to ChromeDriver executable
        chrome_driver_path = os.path.expanduser("~/Downloads/chromedriver_mac64/chromedriver")
        os.environ["PATH"] += os.pathsep + chrome_driver_path
        driver = webdriver.Chrome(options=options)
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
        exc_val_df["bank_abbv_name"] = bank_abbv_name
        exc_val_df = selected_currency(exc_val_df, selected_cur_list)
    elif bank_abbv_name == 'CIMB':
        options = Options()
        options.add_argument("--headless")  # Run the browser in headless mode (without a GUI)

        # Set the path to ChromeDriver executable
        chrome_driver_path = os.path.expanduser("~/Downloads/chromedriver_mac64/chromedriver")
        os.environ["PATH"] += os.pathsep + chrome_driver_path
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        exc_val_df = pd.read_html(driver.find_element(
            By.XPATH, '//table').get_attribute('outerHTML'), encoding='utf-8')[0]

        exc_val_df = exc_val_df[['Currency Code',
                                 'Buying Rates', 'Selling Rates']]
        exc_val_df.columns = ['_'.join(col)
                              for col in exc_val_df.columns.values]
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
        exc_val_df = selected_currency(exc_val_df, selected_cur_list)
    elif bank_abbv_name == "CITI":
        options = Options()
        options.add_argument("--headless")  # Run the browser in headless mode (without a GUI)

        # Set the path to ChromeDriver executable
        chrome_driver_path = os.path.expanduser("~/Downloads/chromedriver_mac64/chromedriver")
        os.environ["PATH"] += os.pathsep + chrome_driver_path
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        page_source = driver.page_source

        # Create a BeautifulSoup object to parse the HTML content
        soup1 = BeautifulSoup(page_source, "html.parser")

        # Find the div element with the specified class
        div_table = soup1.find("div", id ="horizontalTab")


        # Extract the data from the div table
        table_data = []
        for row in div_table.find_all("div", class_="cT-divTableRow"):
            # Extract the cells from each row
            cells = row.find_all("div", class_="wwctrl")
            row_data = [cell.text.strip() for cell in cells]
            table_data.append(row_data)
        header = ["bank_abbv_name", "currency", "buying_rate", "selling_rate"]
        exc = []
        for i in range(len(table_data)):
            exc.append([bank_abbv_name,table_data[i][1],table_data[i][4],table_data[i][5]])
        header = ["bank_abbv_name", "currency", "buying_rate", "selling_rate"]
        exc_val_df = pd.DataFrame(exc, columns=header)

    # Set up the Selenium webdriver
    # driver = webdriver.Chrome(options=options)
    # save_df2img(tmp_df.set_index('bank_abbv_name'),'Test_save_'+bank_abbv_name)
    # save_dataframe_image(tmp_df.set_index('bank_abbv_name'),'Test_save_'+bank_abbv_name)
    tmp_df = exc_val_df.copy()
    tmp_df.index = [today] * len(tmp_df)
    # save_df2img(tmp_df,'Test_save_'+bank_abbv_name)
    # save_dataframe_image(tmp_df,'Test_save_'+bank_abbv_name)
    return exc_val_df


kbank_c_df = scrape_website(
    "KBANK JOURNEY", "https://www.kasikornbank.com/th/personal/Debit-Card/Pages/exchange-rate.aspx")
bay_c_df = scrape_website(
    "BAY BOARDING", "https://www.krungsri.com/th/personal/card/krungsri-boarding-card")
ttb_df = scrape_website(
    "TTB", "https://www.ttbbank.com/th/rates/exchange-rates")
ktb_df = scrape_website(
    "KTB TRAVEL", "https://exchangerate.krungthai.com/#/travelCardRate")
spr_df = scrape_website(
    "SUPERRICH GREEN", "https://www.superrichthailand.com/#!/en/exchange")
bbl_df = scrape_website(
    "BBL", "https://www.bangkokbank.com/en/Personal/Other-Services/View-Rates/Foreign-Exchange-Rates")
cimb_df = scrape_website(
    "CIMB", "https://www.cimbthai.com/en/personal/help-support/rates-charges/foreign-exchange-rates.html")
citi_df = scrape_website(
    "CITI", "https://www.citibank.co.th/THGCB/COA/frx/prefxratinq/flow.action")
combined_df = pd.concat([kbank_c_df, bay_c_df, ttb_df,
                        ktb_df, spr_df, bbl_df, cimb_df,citi_df]).reset_index(drop=True)
selected_cur = ktb_df.currency.unique().tolist()
tmp = combined_df.copy()
tmp.rename(columns={'bank_abbv_name': '', 'buying_rate': 'Buying Rate',
           'selling_rate': 'Selling Rate', 'currency': 'Currency'}, inplace=True)
pivoted_df = tmp.pivot(index='Currency', columns='', values=[
                       'Buying Rate', 'Selling Rate'])
pivoted_df = pivoted_df[[('Selling Rate', 'KTB TRAVEL'), ('Selling Rate', 'TTB'), ('Selling Rate', 'KBANK JOURNEY'), ('Selling Rate', 'BAY BOARDING'), ('Selling Rate', 'SUPERRICH GREEN'), ('Selling Rate', 'BBL'), ('Selling Rate', 'CIMB'), ('Selling Rate', 'CITI')
                         , ('Buying Rate', 'KTB TRAVEL'), ('Buying Rate', 'TTB'), ('Buying Rate', 'BAY BOARDING'), ('Buying Rate', 'SUPERRICH GREEN'), ('Buying Rate', 'BBL'), ('Buying Rate', 'CIMB'), ('Buying Rate', 'CITI')]]

# without BAYBOARDING
# pivoted_df = pivoted_df[[('Selling Rate', 'KTB TRAVEL'), ('Selling Rate', 'TTB'), ('Selling Rate', 'KBANK JOURNEY'), ('Selling Rate', 'SUPERRICH GREEN'), ('Buying Rate', 'KTB TRAVEL'), ('Buying Rate', 'TTB')                        # ,('Buying Rate','KBANK JOURNEY')
#                          , ('Buying Rate', 'SUPERRICH GREEN')]]


# pivoted_df = combined_df.pivot(index='currency', columns='bank_abbv_name', values=['buying_rate', 'selling_rate'])
# pivoted_df = pivoted_df[[('buying_rate','KTB TRAVEL')
#                         ,('buying_rate','TTB')
#                         #,('buying_rate','KBANK JOURNEY')
#                         ,('buying_rate','BAY BOARDING')
#                         ,('selling_rate','KTB TRAVEL')
#                         ,('selling_rate','TTB')
#                         ,('selling_rate','KBANK JOURNEY')
#                         ,('selling_rate','BAY BOARDING')]]
pivoted_df = pivoted_df.fillna('')
output = pivoted_df[pivoted_df.index.isin(selected_cur)].copy()
# if need to highlight currency, then need to reset index
# output = output.reset_index(level=0)
output.style.apply(highlight_rows, axis=1)
save_dataframe_image(output, 'Test_pivoted')