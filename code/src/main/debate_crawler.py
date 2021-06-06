import lxml
import time
import json
import requests
from bs4 import BeautifulSoup


def check_popular(top=5):
    """get the popular urls and limit using 'top', default 5"""
    url = 'https://www.debate.org/opinions/?p=1&sort=popular'
    page = requests.get(url, headers={'Cache-Control': 'no-cache',
                                      "Pragma": "no-cache"})
    soup = BeautifulSoup(page.content, 'lxml')
    rows = soup.find_all('a', attrs={'class': 'a-image-contain'})
    return ['https://www.debate.org'+x['href'] for x in rows][:top]


def get_data(url):
    """load the page and parse it for title, id, category and pros and cons on that page"""
    page = requests.post(url)
    soup = BeautifulSoup(page.content, 'lxml')
    category = soup.find('div', {'id': "breadcrumb"})
    category = category.contents[5].contents[0]
    debateId = soup.find('li', {'class': "report-poll"})['id']
    title = soup.find('span', {'class': "q-title"})
    title = title.contents[0]
    yes = soup.find_all('div', attrs={'class': 'arguments args-yes'})
    no = soup.find_all('div', attrs={'class': 'arguments args-no'})
    return title, yes, no, category, debateId


def parse_opinons(html):
    """Finds all arguments; both heading and body"""
    soup = BeautifulSoup(html, 'lxml')
    data = soup.find_all('li', attrs={'class': 'hasData'})
    return data


def load_more(did):
    pros = []
    cons = []
    i = 2
    while True:
        header = {"debateId": did, "pageNumber": i,
                  "itemsPerPage": 10, "ysort": 5, "nsort": 5}
        url = "https://www.debate.org/opinions/~services/opinions.asmx/GetDebateArgumentPage"
        secpage = requests.post(url, json=header)
        pro_con = secpage.text.encode(
            'utf-8').decode('unicode-escape').split(r'{ddo.split}')
        pros += parse_opinons(str(pro_con[0]))
        cons += parse_opinons(str(pro_con[1]))
        print('loading part: ', i, pro_con[2][:-2])
        i += 1
        if r'finished' in str(pro_con[2]):
            break
        else:
            # wait 1s before loading a new page
            time.sleep(1)
    return pros, cons


if __name__ == '__main__':
    top_debates = check_popular()
    debate_list = []
    t1 = time.time()
    for url in top_debates:
        print('Working on:', url)
        title, yes, no, category, debateId = get_data(url)
        print('Found debate on :', title)
        pros, cons = load_more(debateId)
        pros += parse_opinons(str(yes[0]))
        cons += parse_opinons(str(no[0]))
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
    print('time taken :', time.time()-t1, 'seconds.\nWriting data..')
    with open('data.json', 'w') as f:
        json.dump(debate_list, f)
