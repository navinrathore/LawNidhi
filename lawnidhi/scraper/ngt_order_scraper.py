import os
import re
import requests
from bs4 import BeautifulSoup
import urllib3
from typing import List, Dict, Optional

# Disable insecure request warnings for NGT's SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class NGTOrderScraper:
    """
    Scrapes the NGT Case Details web page for order listing history 
    and handles downloading the dynamic PDFs.
    """
    def __init__(self, download_dir: str, session: Optional[requests.Session] = None):
        self.download_dir = download_dir
        if session:
            self.session = session
        else:
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
            })
        os.makedirs(self.download_dir, exist_ok=True)
        
    def extract_orders_from_html(self, html_content: str, diary_number: str) -> List[Dict]:
        """
        Parses the Case Details HTML to extract listing history and PDF links.
        Decodes Base64 payloads natively from `myFunctionTest` javascript hooks.
        """
        import base64
        soup = BeautifulSoup(html_content, 'html.parser')
        orders = []
        
        # Look for the Judgement/Order History table
        for tbl in soup.find_all('table'):
            headers = [th.text.strip().lower() for th in tbl.find_all('th')]
            if 'order/judgement.' in headers or 'order date' in headers or 'date of listing' in headers:
                
                # Dynamic column index resolution
                date_idx = -1
                order_idx = -1
                for i, h in enumerate(headers):
                    if 'date of listing' in h or 'order date' in h:
                        date_idx = i
                    if 'order/judgement.' in h or 'judgement' in h:
                        order_idx = i
                
                if order_idx == -1:
                    continue
                    
                rows = tbl.find_all('tr')
                for row in rows[1:]:
                    cols = row.find_all('td')
                    if len(cols) > max(date_idx, order_idx):
                        date_str = cols[date_idx].text.strip() if date_idx != -1 else "unknown_date"
                        clean_date = date_str.replace('/', '-').replace(' ', '_')
                        
                        pdf_link = None
                        all_links = cols[order_idx].find_all('a', onclick=True)
                        
                        # Prioritize: myFunctionTest (visible, working) over myFunction (hidden/legacy)
                        for a_tag in all_links:
                            # Skip hidden elements (style='display:none;')
                            style = a_tag.get('style', '')
                            if 'display:none' in style.replace(' ', ''):
                                continue
                            
                            onclick_text = a_tag['onclick']
                            match_test = re.search(r"myFunctionTest\('([^']+)'\)", onclick_text)
                            if match_test:
                                payload = match_test.group(1)
                                pdf_link = f"https://www.greentribunal.gov.in/gen_pdf_test.php?filepath={payload}"
                                break  # Found the preferred one, stop
                        
                        # Fallback: if no myFunctionTest found, try myFunction (non-hidden)
                        if not pdf_link:
                            for a_tag in all_links:
                                style = a_tag.get('style', '')
                                if 'display:none' in style.replace(' ', ''):
                                    continue
                                onclick_text = a_tag['onclick']
                                match_std = re.search(r"myFunction\('([^']+)'\)", onclick_text)
                                if match_std:
                                    payload = match_std.group(1)
                                    pdf_link = f"https://www.greentribunal.gov.in{payload}"
                                    break
                        
                        if pdf_link:
                            safe_diary = str(diary_number).replace('/', '-')
                            orders.append({
                                'diary_number': diary_number,
                                'order_date': date_str,
                                'pdf_url': pdf_link,
                                'suggested_filename': f"{safe_diary}_{clean_date}_order.pdf"
                            })
        return orders

    def download_orders_from_case_page(self, case_details_url: str, diary_number: str) -> List[str]:
        """
        Takes the intermediary Case Details HTML page URL, fetches the DOM, parses
        all Javascript Base64 encoded PDF endpoints, and downloads them locally.
        """
        print(f"Fetching Intermediary Case Details Page: {case_details_url}")
        resp = self.session.get(case_details_url, verify=False, timeout=45)
        
        if resp.status_code != 200:
            print(f"Failed to load Case Details page. HTTP Status: {resp.status_code}")
            return []
            
        orders = self.extract_orders_from_html(resp.text, diary_number)
        saved_files = []
        
        print(f"Discovered {len(orders)} encoded Order PDFs embedded in the DOM.")
        for order in orders:
            path = self.download_pdf(order['pdf_url'], order['suggested_filename'])
            if path:
                saved_files.append(path)
                
        return saved_files

    def download_pdf(self, pdf_url: str, save_filename: str) -> Optional[str]:
        """
        Downloads a dynamic PDF via GET request (No CAPTCHA required for the raw PDF API).
        Skips download if the file already exists in the target directory.
        """
        save_path = os.path.join(self.download_dir, save_filename)
        
        # Prevent duplicates
        if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
            print(f"Skipping download, file already exists: {save_path}")
            return save_path

        print(f"Downloading: {pdf_url}")
        
        try:
            response = self.session.get(pdf_url, verify=False, timeout=45)
            if response.status_code == 200 and 'application/pdf' in response.headers.get('Content-Type', ''):
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                print(f"Successfully saved to: {save_path}")
                return save_path
            else:
                print(f"Failed to download. Status: {response.status_code}, Content-Type: {response.headers.get('Content-Type')}")
                return None
        except Exception as e:
            print(f"Error downloading PDF: {e}")
            return None

if __name__ == "__main__":
    # Test just the download functionality with the user's provided link
    test_pdf_url = "https://www.greentribunal.gov.in/gen_pdf_test.php?filepath=L25ndF9kb2N1bWVudHMvbmd0L2Nhc2Vkb2MvanVkZ2VtZW50cy9ERUxISS8yMDI1LTAyLTI4LzE3NDEwODE5MDQxNjk0OTYxMjIwNjdjNmNkMzBlOWI3ZS5wZGY="
    scraper = NGTOrderScraper(download_dir="data/orders")
    
    # Fake diary number as we test
    diary_no = "0701102002572025"
    filename = f"{diary_no}_2025-02-28_order.pdf"
    
    file_path = scraper.download_pdf(test_pdf_url, filename)
    if file_path:
        print(f"Verified existence: {os.path.exists(file_path)}")
