import requests
from bs4 import BeautifulSoup
import urllib3
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_captcha_and_url():
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0'})
    
    search_url = "https://www.greentribunal.gov.in/judgementOrder/casenumber"
    resp = session.get(search_url, verify=False)
    
    if resp.status_code != 200:
        print(f"Failed to load search page: {resp.status_code}")
        return
        
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    token = soup.find('input', {'name': 'csrf_token'})
    print(f"CSRF Token found: {'Yes (' + token.get('value', '') + ')' if token else 'No'}")
    
    img_tag = None
    for img in soup.find_all('img'):
        if 'captcha' in img.get('src', '').lower() or 'captcha' in img.get('id', '').lower() or 'captcha' in img.get('alt', '').lower():
            img_tag = img
            break
            
    if not img_tag:
        print("No CAPTCHA image found on page!")
        return
        
    captcha_url = img_tag['src']
    if not captcha_url.startswith('http'):
        captcha_url = "https://www.greentribunal.gov.in/" + captcha_url.lstrip('/')
        
    print(f"CAPTCHA Image URL: {captcha_url}")
    
    img_resp = session.get(captcha_url, verify=False)
    with open("scripts/captcha.png", "wb") as f:
        f.write(img_resp.content)
    print("Saved CAPTCHA to scripts/captcha.png")

if __name__ == "__main__":
    get_captcha_and_url()
