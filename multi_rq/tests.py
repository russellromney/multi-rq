import time
import random

def wait(i,j):
    i = random.randrange(i,j)/50
    time.sleep(i)
    return i


import requests

def count_words_at_url(url):
    resp = requests.get(url)
    return len(resp.text.split())

def sum_this(iterable):
    return sum(iterable)