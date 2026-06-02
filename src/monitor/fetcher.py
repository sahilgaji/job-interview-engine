from src.utils.http import get

def fetch(url):
    r = get(url)
    return r.text, r.url
