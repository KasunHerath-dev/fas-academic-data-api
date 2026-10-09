import requests
from bs4 import BeautifulSoup
import sys

USER_AGENT = "Mozilla/5.0"
url = "https://fas.wyb.ac.lk/revised-academic-time-table-level-1-semester-i-academic-year-2024-2025/"
html = requests.get(url, headers={"User-Agent": USER_AGENT}).text
soup = BeautifulSoup(html, "lxml")
for a in soup.find_all("a", href=True):
    if ".pdf" in a["href"].lower():
        print("Found PDF:", a["href"])
