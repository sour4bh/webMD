#%%
import requests
import json
import bs4
from tqdm import tqdm
import time
from pprint import pprint as pp
#%%
drugs = {}
alpha = list('abcdefghijklmnopqrstuvwxyz')
alpha = [i+j for i in alpha for j in alpha]

def update_list(soup, by):
    ul = soup.find('ul', 'drug-list')
    if ul is None:
        print('not found')
        return None
    for li in ul.find_all('li'):
        try:
            d = drugs[by]
        except KeyError:
            drugs[by] = []
        finally:
            drugs[by].append((li.a.text, li.a['href']))

istheredurgs = lambda soup : soup.find('ul', 'drug-list').find('li') is not None
#%%
for by in tqdm(alpha):
    # print(by, end='\t')
    r = requests.get(f'https://www.webmd.com/drugs/2/alpha/{by[0]}/{by}')
    if r.status_code == 200:
        soup = bs4.BeautifulSoup(r.content, 'lxml')
        if istheredurgs(soup):
            update_list(soup, by)
            tqdm.write(by)
    else:
        print(by, r.status_code)
#%%
with open('alpha.json', 'w') as f:
    json.dump(drugs, f)
#%%
with open('alpha.json', 'r') as f:
    drugs = json.load(f)
    count = 0
    for i in drugs:
        count += len(drugs[i])
    print(count)
# %%
