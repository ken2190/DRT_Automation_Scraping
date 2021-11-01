#!/usr/bin/env python
# coding: utf-8

# In[3]:


#importing Necessary Modules
import pandas as pd
from sqlalchemy import create_engine
import sys
import cv2
from selenium import webdriver
from selenium.webdriver.common.by import By 
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

driver = None

#Opening the Website
def drt_login():
    global driver
    Link = "https://drt.gov.in/front/page1_advocate.php"
    driver = webdriver.Chrome()
    #wait = WebDriverWait(driver, 600)
    driver.get(Link)
    driver.maximize_window()
    
    
#Selecting values of DRT/ DRAT name and Party name to get data    
def drt_select():
    partyname = '/html/body/div[1]/div/form/div[1]/div[4]/a'
    drt_xpath = '//select[@id="schemaname"]'
    drt_chennai_xpath = '//*[@id="schemaname"]/option[3]'
    driver.find_element(By.XPATH,partyname).click()
    driver.find_element(By.XPATH,drt_xpath).click()
    driver.find_element(By.XPATH,drt_chennai_xpath).click()
    
    drt_party = 'sha'
    driver.find_element(By.ID,'name').send_keys(drt_party)
    
    
#Entering captcha value received by pytesseract    
def bypass_captcha():
    #Downloading Captcha image
    with open('.//captcha.png', 'wb') as file:
        file.write(driver.find_element_by_xpath('//*[@id="captchatext"]/img').screenshot_as_png) 
        
    #Image noise cleaning for obtaining better results
    #This is not very accurate in obtaining captchas yet
    img = cv2.imread("captcha.png")
    gry = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    (h, w) = gry.shape[:2]
    gry = cv2.resize(gry, (w*2, h*2))
    cls = cv2.morphologyEx(gry, cv2.MORPH_CLOSE, None)
    thr = cv2.threshold(cls, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    txt = pytesseract.image_to_string(thr).strip()
    driver.find_element_by_xpath('//*[@id="captchatext"]/input').send_keys(txt)
    driver.find_element_by_id('submit1').click()
    
    
#Scraping the Main report page   
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
    return headers,table_rows

#Converting first page to Dataframe and storing in "df" pandas dataframe object
def convert_to_df(columns,rows):
    df = pd.DataFrame(rows, columns=columns)
    return df

#Scraping URLs from the "More Details" Hyperlink
#Updating the original table with links for the Case details to be accessed anytime
def scrape_detail_url(df, detail_url):
    urls = []
    for i in range(1,len(df.index)+1):
        detail_xpath = "/html/body/div[1]/div/form/div[5]/div/div[2]/table/tbody/tr[{}]/td[9]/a".format(i)
        attr = driver.find_element_by_xpath(detail_xpath).get_attribute('href')
        url = detail_url + attr.split("'",2)[1]
        urls.append(url)
    df = df.drop('View More', 1)
    df["Link for More Details"] = urls
    driver.close()
        
        
    return df

#Scraping first table in all links for Case details
#cleaning the list to look more presentable
def scrape_table1_details(df):
    datalist = []

    browser = webdriver.Chrome()
    #wait = WebDriverWait(driver, 600)
    for url in df["Link for More Details"].tolist():
        browser.get(url)
        #browser.maximize_window()
        
        tables = browser.find_elements_by_tag_name('table')
        #table1
        tablerows = tables[0].find_elements_by_tag_name('tr')
        t = []
        for tr in tablerows:
            if tr.find_elements_by_tag_name('th') != []:
                continue
                #t.append(tr.find_element_by_tag_name('th').text)
            if tr.find_elements_by_tag_name('td') != []:
                td_data = []
                if len(tr.find_elements_by_tag_name('td')) == 1:
                    continue
                for td in tr.find_elements_by_tag_name('td'):
                    td_data.append(td.text)
                t.append(td_data)
        
        datalist.extend(t)
    browser.close()
    table1_data = []
    columns = ['Diary no/Year','Case Type/Case No/Year','DRT Detail','Date of Filing.','Case Status.','In the Court of','Court No.',
               'Next Listing Date','Next Listing Purpose']
    for i in range(len(columns)):
        temp = [columns[i]]
        for j in range(len(datalist)):
            if datalist[j][0] == columns[i]:
                temp.append(datalist[j][1])
        table1_data.append(temp)
        
    
    table1_df = pd.DataFrame(table1_data).T
    table1_df = table1_df.rename(columns=table1_df.iloc[0]).drop(table1_df.index[0])       
    return table1_df

#Scraping second table in all links for Petitioner details
#cleaning the list to look more presentable
def scrape_table2_details(df):
    datalist = []
    diary = []
    browser = webdriver.Chrome()
    #wait = WebDriverWait(driver, 600)
    for url in df["Link for More Details"].tolist():
        browser.get(url)
        #browser.maximize_window()
        diary.append(browser.find_element_by_xpath('/html/body/div/form/font/table[1]/tbody/tr[2]/td[2]').text)
        tables = browser.find_elements_by_tag_name('table')
        #table2
        tablerows = tables[1].find_elements_by_tag_name('tr')
        data = [x.text for x in tablerows]
        datalist.append(data)
    browser.close()
    table2_data = []
    columns = ['PETITIONER/APPLICANT DETAIL','RESPONDENTS/DEFENDENT DETAILS']
    temp = []
    for data in datalist:
        temp = [data[1],data[3]]      
        table2_data.append(temp)
    
    table2_df = pd.DataFrame(table2_data)
    table2_df.columns = columns
    table2_df.insert(loc = 0, column = 'Diary no/Year', value = diary)
    return table2_df

#Scraping third table in all links for Case Proceedings details
#cleaning the list to look more presentable
def scrape_table3_details(df):
    datalist = []
    diary = []
    browser = webdriver.Chrome()
    #wait = WebDriverWait(driver, 600)
    for url in df["Link for More Details"].tolist():
        browser.get(url)
        #browser.maximize_window()
        diary.append(browser.find_element_by_xpath('/html/body/div/form/font/table[1]/tbody/tr[2]/td[2]').text)
        tables = browser.find_elements_by_tag_name('table')
        #table3
        tablerows = tables[2].find_elements_by_tag_name('tr')
        data = [x.text for x in tablerows]
        if len(data) > 3:
            datalist.append(data[2:-1])
        else:
            datalist.append(["None None None"])        
    browser.close()
    table3_data = []
    for i in range(len(diary)):
        for data in datalist[i]:
            table3_data.append(str(diary[i] + " " + data).split(" ",3))
    columns = ['Diary no/Year','Court Name','Causelist Date','Purpose']
    
    
    table3_df = pd.DataFrame(table3_data)
    table3_df.columns = columns
    
    return table3_df


#Pushing the dataframes to database.
#If the database already exists, updating the database with the newer values


def postgres_storing(df,table1_df, table2_df, table3_df):
    db = create_engine('postgresql://postgres:db@localhost:5432/Legistify')
    con = db.connect()
    df.to_sql("Report",con,if_exists='replace')
    table1_df.to_sql("Case Status",con,if_exists='replace')
    table2_df.to_sql("Petitioner Details",con,if_exists='replace')
    table3_df.to_sql("Case Proceedings Details",con,if_exists='replace')
        
           
if __name__=="__main__":
    drt_login()     
    
    drt_select()
    
    try:
        bypass_captcha()
    except:
        print("Invalid Captcha. Please try again")
        sys.exit()
    
    columns, rows = scrape_main()
    
    
    df = convert_to_df(columns, rows)
    
    detail_url = "https://drt.gov.in/drtlive/Misdetailreport.php?no="
    
    df = scrape_detail_url(df,detail_url)
    
    table1_df = scrape_table1_details(df)
    
    table2_df = scrape_table2_details(df)
    
    table3_df = scrape_table3_details(df)
    
    postgres_storing(df,table1_df, table2_df, table3_df)
    


# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:




