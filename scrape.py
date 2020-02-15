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
url = lambda link : f'https://www.drugs.com{link}'
