# -*- coding: utf-8 -*-
"""
Created on Sat Oct 30 16:14:01 2021

@author: Siddhant
"""
import pandas as pd

import cv2
from selenium import webdriver
#from selenium.webdriver.support.ui import WebDriverWait
#from selenium.webdriver.support import expected_conditions as EC
#from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
#from selenium.common.exceptions import NoSuchElementException

    
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

driver = None


def drt_login():
    global driver
    Link = "https://drt.gov.in/front/page1_advocate.php"
    driver = webdriver.Chrome()
    #wait = WebDriverWait(driver, 600)
    driver.get(Link)
    driver.maximize_window()
    
    
    
def drt_select():
    partyname = '/html/body/div[1]/div/form/div[1]/div[4]/a'
    drt_xpath = '//select[@id="schemaname"]'
    drt_chennai_xpath = '//*[@id="schemaname"]/option[3]'
    driver.find_element(By.XPATH,partyname).click()
    driver.find_element(By.XPATH,drt_xpath).click()
    driver.find_element(By.XPATH,drt_chennai_xpath).click()
    
    drt_party = 'sha'
    driver.find_element(By.ID,'name').send_keys(drt_party)
    
    
    
def bypass_captcha():
    with open('.//captcha.png', 'wb') as file:
        file.write(driver.find_element_by_xpath('//*[@id="captchatext"]/img').screenshot_as_png) 
    img = cv2.imread("captcha.png")
    gry = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    (h, w) = gry.shape[:2]
    gry = cv2.resize(gry, (w*2, h*2))
    cls = cv2.morphologyEx(gry, cv2.MORPH_CLOSE, None)
    thr = cv2.threshold(cls, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    txt = pytesseract.image_to_string(thr).strip()
    driver.find_element_by_xpath('//*[@id="captchatext"]/input').send_keys(txt)
    driver.find_element_by_id('submit1').click()
    
    
    
def scrape_main():
   # with open("source.text","w") as file:
    #    file.write(driver.page_source)
    th_list = driver.find_elements_by_tag_name('th')
    headers = [x.text for x in th_list[1:]]
    td_list = driver.find_elements_by_tag_name('td')
    data = [x.text for x in td_list]
    table_rows = []
    r = []
    count = 0
    for i in range(len(data)):
        count += 1
        r.append(data[i])
        if count == len(headers):
            table_rows.append(r)
            r = []
            count = 0
            
    #print(table_rows)
    return headers,table_rows
    
def convert_to_df(columns,rows):
    df = pd.DataFrame(rows, columns=columns)
    return df
    
def scrape_detail_url(df, detail_url):
    urls = []
    for i in range(1,len(df.index)+1):
        detail_xpath = "/html/body/div[1]/div/form/div[5]/div/div[2]/table/tbody/tr[{}]/td[9]/a".format(i)
        attr = driver.find_element_by_xpath(detail_xpath).get_attribute('href')
        url = detail_url + attr.split("'",2)[1]
        urls.append(url)
    df = df.drop('View More', 1)
    df["Link for More Details"] = urls
    return df
    
def scrape_details(df):
    datalist = []
    browser = webdriver.Chrome()
    #wait = WebDriverWait(driver, 600)
    for url in df["Link for More Details"].tolist():
        browser.get(url)
        browser.maximize_window()
        text = browser.find_elements_by_tag_name('tr')
        data = [x.text for x in text]
        datalist.append(data)
    df_data = pd.DataFrame(datalist)
    return df_data
        
        
        
if __name__=="__main__":
    drt_login()     
    
    drt_select()
    
    bypass_captcha()
    
    columns, rows = scrape_main()
    
    
    df = convert_to_df(columns, rows)
    
    detail_url = "https://drt.gov.in/drtlive/Misdetailreport.php?no="
    
    df = scrape_detail_url(df,detail_url)
    
    df_data = scrape_details(df)
    
    
















