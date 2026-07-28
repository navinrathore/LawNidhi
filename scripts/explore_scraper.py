import requests
from bs4 import BeautifulSoup
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def explore_url(url):
    print(f"Fetching: {url}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    
    try:
        response = requests.get(url, headers=headers, verify=False, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        if 'captcha' in response.text.lower():
            print("WARNING: CAPTCHA detected in the HTML!")
            
        pdf_links = [a['href'] for a in soup.find_all('a', href=True) if 'gen_pdf' in a['href'] or 'pdf' in a['href'].lower()]
        print(f"Found {len(pdf_links)} PDF-related links (unique):")
        for link in set(pdf_links):
            print(f"- {link}")
            
        tables = soup.find_all('table')
        print(f"\nFound {len(tables)} tables on page.")
        
        for i, table in enumerate(tables):
            headers = [th.text.strip() for th in table.find_all('th')]
            print(f"Table {i} headers: {headers}")
            if headers:
                # Print first row
                rows = table.find_all('tr')
                if len(rows) > 1:
                    cols = [td.text.strip() for td in rows[1].find_all('td')]
                    print(f"  First Row: {cols}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    url = "https://www.greentribunal.gov.in/caseDetails/DELHI/0701102002572025?page=order"
    explore_url(url)
