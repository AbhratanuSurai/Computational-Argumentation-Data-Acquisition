import re
import os
import lxml
import time
import json
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium import common as cex
from selenium.webdriver.firefox.options import Options




def check_popular(top=5):
    """get the popular urls and limit using 'top', default 5"""
    url = 'https://www.debate.org/opinions/?p=1&sort=popular'
    page = requests.get(url, headers={'Cache-Control': 'no-cache',
                                      "Pragma": "no-cache"})
    soup = BeautifulSoup(page.content, 'lxml')
    rows = soup.find_all('a', attrs={'class': 'a-image-contain'})
    return ['https://www.debate.org'+x['href'] for x in rows][:top]


def parse_opinons(html):
    """Finds all arguments; both heading and body"""
    soup = BeautifulSoup(html, 'lxml')
    data = soup.find_all('li', attrs={'class': 'hasData'})
    return data

def get_entirepage(url):
    opts = Options()
    opts.add_argument("--headless")
    # check if windows or linux
    if os.name == 'nt':
        driver = webdriver.Firefox(options=opts) 
    else:
        driver = webdriver.Firefox(options=opts,executable_path="./geckodriver") 
    # load page 
    driver.get(url)
    print('loading more arguments...')
    # close "Privacy Policy and our Terms of Use" overly to avoid obstacle later
    try:
        driver.find_element_by_class_name('cookies-request-close').click()
    except :
        # its not there!
        pass
    # look for "Load More Arguments" button as long as available
    while True:
        try:
            button = driver.find_element_by_xpath("//a[contains(.,'Load More Arguments')]")
            if button is not None:
                onclick_text = button.get_attribute('onclick')
                if onclick_text and re.search('loadMoreArguments', onclick_text):
                    print ("found more!")
                    button.click()
                    # wait 1s, just to be nice
                    time.sleep(1)
        except :
            # all arguments loaded 
            print('no more.')
            break
    page = driver.page_source
    driver.quit()
    return page

def parse_items(html):
    """Extracts informations like category, tilte, debate id, 
    and separtes pro and con section(keeping in html form)"""
    soup = BeautifulSoup(html, 'lxml')
    category = soup.find('div', {'id': "breadcrumb"})
    category = category.contents[5].contents[0]
    debateId = soup.find('li', {'class': "report-poll"})['id']
    title = soup.find('span', {'class': "q-title"})
    title = title.contents[0]
    pro = soup.find('div', attrs={'class': 'arguments args-yes'})
    con = soup.find('div', attrs={'class': 'arguments args-no'})
    return title, pro,con ,category,debateId


if __name__ == '__main__':
    top_debates = check_popular()
    debate_list = []
    t1 = time.time()
    for url in top_debates:
        print('Working on:', url)
        title, yes, no, category, debateId = parse_items(get_entirepage(url))
        print('Found debate on :', title)
        pros = parse_opinons(str(yes))
        cons = parse_opinons(str(no))
        pro_args = [{'title': pro.contents[0].text,
                     'body': pro.contents[2].text} for pro in pros]
        con_args = [{'title': con.contents[0].text,
                     'body': con.contents[2].text} for con in cons]
        debate_topic = {"topic": title,
                        "category": category,
                        "pro_arguments": pro_args,
                        "con_arguments": con_args
                        }
        debate_list.append(debate_topic)
        print('pro arguments:', len(pro_args))
        print('con arguments:', len(con_args))
    print('time taken :',time.time()-t1,'seconds.\nWriting data..')
    with open('data.json', 'w') as f:
        json.dump(debate_list, f)