#%%
import time
import re
import os
import bs4 
import json
import requests
from pandas import read_html
from requests.exceptions import ConnectionError
from tqdm import tqdm
from pprint import pprint
#%%
txt = lambda elem: elem.text.replace('\n', '').strip()
url = lambda link : f'https://www.webmd.com{link}'
#%%
def extract_text(soup, content_box=True):
    content = {}
    stack = []
    level = 1
    pointer = content
    prev_elem = None
    content_soup = soup
    if content_box:
        content_soup = soup.find_all('div', 'inner-content')
    for inner_content in content_soup:
        for elem in inner_content.recursiveChildGenerator():
            tag = str(elem.name)
            pointer = content
            if re.match('h[2-6]', tag):
                diff = int(tag[-1]) - level
                if diff:
                    if diff < 0:
                        for i in range(abs(diff)):
                            stack.pop()
                        stack.pop()
                        stack.append(txt(elem))
                        prev_elem = elem
                    if diff > 0:
                        for i in range(abs(diff)):
                            stack.append(txt(elem))
                            prev_elem = elem
                    level += diff
                else:
                    stack.pop()
                    stack.append(txt(elem))
                for point in stack:
                    try:
                        pointer = pointer[point]
                    except KeyError:
                        pointer[point] = {'text' : []}
                        pointer = pointer[point]

            elif len(stack) and str(type(elem)) == '<class \'bs4.element.Tag\'>' and str(elem.name) == 'p':
                for point in stack:
                    pointer = pointer[point]
                pointer['text'].append(txt(elem))
                prev_elem = elem

            elif len(stack) and str(type(elem)) == '<class \'bs4.element.Tag\'>' and str(elem.name) == 'ul':
                for point in stack:
                    pointer = pointer[point]
                lis = []
                for li in elem.find_all('li'):
                    lis.append(li.get_text().replace('\n', ' '))
                if prev_elem.name == 'p':
                    try:
                        pointer['text'].pop()
                    except IndexError:
                        pass
                    pointer['text'].append({txt(prev_elem) : lis})
                elif prev_elem.name[0] == 'h':
                    pointer['text'].append(lis)
                prev_elem = elem
    return content

def extract_metadata(soup):
    content = soup.find('div', 'drug-names')
    re_keys = lambda ps : re.findall('[A-Z]+ [A-Z\W]+:', ps.text)[0]
    keys = list(map(re_keys, content.find_all('p')))
    vals = []
    for i, sub in enumerate(content.find_all('p')):
        vals.append(sub.text.replace(keys[i], '').strip().split(','))
        keys[i] = keys[i].replace(':', '').strip()
    return dict(zip(keys, vals))

def extract_reviews(soup):
    def get_rating(soup):
        rating = {}
        for rated in soup.find_all('div', 'catRatings'):
            rating[rated.p.text] = re.findall('[0-9]', rated.find('span').text)[0]
        return rating
    def get_comments(soup):
        posts = []
        comments = soup.find_all('div', 'userPost')
        # print('c', len(comments))
        if not len(comments):
            return 0, []
        for i, comment in enumerate(comments): 
            post = {
                'user'              : txt(comment.find('p', 'reviewerInfo')),
                'condition'         : txt(comment.find('div', 'conditionInfo')),
                'comment_date'      : txt(comment.find('div', 'date')),
                'content'           : txt(comment.find('p', 'comment', id=f'comFull{i+1}')),
                'rating'            : get_rating(comment)
                }
            posts.append(post)
            return len(posts), posts
    
    reviews = {'reviews' : []}
    a = soup.find('a', 'drug-review')
    if int(re.findall('([0-9]+)', a.text)[0]):
        link = url(a['href'])
        page = 0
        while True:
            page_link = link + f'&pageIndex={page}&sortby=3'
            r = requests.get(page_link)
            soup = bs4.BeautifulSoup(r.content, 'lxml')
            # if not page: 
                # reviews['overall_ratings'] = get_rating(soup.find('div', id='overallRating'))
            count, comments = get_comments(soup)
            if not count:
                return len(reviews['reviews']), reviews
            for comment in comments:
                reviews['reviews'].append(comment)
            # print('p', page)
            page += 1
    return 0, {}
#%%
with open('alpha.json', 'r') as f:
    drugs = json.load(f)

with open('only_in_webmd.csv', 'r') as f:
    only_in_webmd = [d[:-1] for d in f.readlines()]

i, last, goto = 0, None, None
# with open('pickles.txt', 'r') as f:
#     pickles = f.read()
#     if len(pickles) > 1:
#         goto = pickles
#         print('starting at', goto)
#     else:
#         print('found nothing pickled')

t1 = time.time()
while True:
    try:    
        for drug, link in tqdm([i for key in drugs for i in drugs[key]]):
            drug = drug.replace('/', ' ')
            last = drug; i += 1
            if goto is not None:
                if goto != last:
                    continue
                else:
                    goto = None
            
            if drug not in only_in_webmd:
                tqdm.write(f'skipping {drug}')
                continue

            tqdm.write(f'scraping {drug}') # stdout log?
            # tqdm.write(drug)
            try:
                os.mkdir(f'data/{drug}')
            except FileExistsError:
                pass
            
            r = requests.get(url(link))
            soup = bs4.BeautifulSoup(r.content, 'lxml')
            try:
                with open(f'data/{drug}/{drug}.json', 'w') as f:
                    #  metadata
                    content = extract_metadata(soup )
                    # overview text
                    content.update(extract_text(soup))
                    json.dump(content, f, indent=5)
                
                with open(f'data/{drug}/{drug}_reviews.json', 'w') as f:
                    content = extract_reviews(soup)
                    tqdm.write(f'reviews {content[0]}')
                    json.dump(content[1], f, indent=4)
            except AttributeError as ae:
                tqdm.write(str(ae))
                with open('failed.csv', 'w') as f:
                    f.write(drug + '\n')
                continue
            with open('pickles.txt', 'w', encoding='utf-8') as f:
                f.write(last)
            # # time.sleep(2) # god mode off
    except (TimeoutError, ConnectionError):
            print('BOT KILL, CONNECTION SEVERED')
            goto = last
            print('waiting a minute...')
            time.sleep(60)
            continue
    except KeyboardInterrupt:
        break
    break
print('total time taken', round((time.time() - t1) / 60, 2))
#%%