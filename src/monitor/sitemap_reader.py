from bs4 import BeautifulSoup
from src.utils.http import get

def read_sitemap(url):
    r = get(url)
    soup = BeautifulSoup(r.text, "xml")
    return [x.text.strip() for x in soup.find_all("loc")]
