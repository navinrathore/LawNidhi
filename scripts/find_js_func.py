import time
import os
from bs4 import BeautifulSoup
from lawnidhi.scraper.dynamic_search import DynamicSearchAPI

api = DynamicSearchAPI()
api.get_captcha()
print("CAPTCHA saved. Waiting for data/captcha_ans.txt...")

ans = None
for _ in range(30):
    if os.path.exists("data/captcha_ans.txt"):
        with open("data/captcha_ans.txt", "r") as f:
            ans = f.read().strip()
        if ans:
            os.remove("data/captcha_ans.txt")
            break
    time.sleep(1)

html_result = api.fetch_diary_details("83", "2025", ans, "1", "1")
first_link = "https://www.greentribunal.gov.in/caseDetails/DELHI/0701102002572025?page=order"
print(f"Fetching {first_link}...")
resp = api.session.get(first_link, verify=False)

soup = BeautifulSoup(resp.text, 'html.parser')
for s in soup.find_all('script'):
    if s.string and ('myFunction' in s.string):
        print("FOUND FUNCTION DEFINITION:")
        print(s.string)
