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
    
    drt_select()
    
def drt_select():
    partyname = '/html/body/div[1]/div/form/div[1]/div[4]/a'
    drt_xpath = '//select[@id="schemaname"]'
    drt_chennai_xpath = '//*[@id="schemaname"]/option[3]'
    driver.find_element(By.XPATH,partyname).click()
    driver.find_element(By.XPATH,drt_xpath).click()
    driver.find_element(By.XPATH,drt_chennai_xpath).click()
    
    drt_party = 'sha'
    driver.find_element(By.ID,'name').send_keys(drt_party)
    
    bypass_captcha()
    
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
    
    scrape_main()
    
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
    convert_to_df(headers,table_rows)
    
def convert_to_df(columns,rows):
    df = pd.DataFrame(rows, columns=columns)
    print(df.head())
    
    
    
        
if __name__=="__main__":
    drt_login()       
















