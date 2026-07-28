import os
import re
import requests
from bs4 import BeautifulSoup
import urllib3
from typing import Dict, List, Optional, Any

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class DynamicSearchAPI:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0'})
        self.base_url = "https://www.greentribunal.gov.in"
        
    def get_captcha(self, save_path="data/captcha.png"):
        """Initiates a session, pulls the search form, and downloads the CAPTCHA."""
        search_url = f"{self.base_url}/judgementOrder/casenumber"
        resp = self.session.get(search_url, verify=False)
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Find CAPTCHA image
        img_tag = None
        for img in soup.find_all('img'):
            if 'captcha' in img.get('src', '').lower():
                img_tag = img
                break
                
        if not img_tag:
            raise Exception("No CAPTCHA image found on the search page.")
            
        captcha_url = img_tag['src']
        if not captcha_url.startswith('http'):
            captcha_url = f"{self.base_url}/" + captcha_url.lstrip('/')
            
        # Download CAPTCHA using the same session
        img_resp = self.session.get(captcha_url, verify=False)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(img_resp.content)
            
        return save_path

    def solve_captcha(self, image_path: str = "data/captcha.png") -> Optional[str]:
        """Attempts to solve the CAPTCHA image using improved OCR pre-processing."""
        try:
            import pytesseract
            from PIL import Image, ImageOps, ImageFilter
            
            img = Image.open(image_path).convert('RGB')
            # Pre-processing: Grayscale -> Enhanced Contrast -> Thresholding
            img = ImageOps.grayscale(img)
            # Thresholding to remove background noise (most CAPTCHAs have a light background)
            img = img.point(lambda p: p > 165 and 255) 
            img = img.filter(ImageFilter.SMOOTH_MORE)
            
            raw_text = pytesseract.image_to_string(img, config='--psm 7').strip()
            # Clean: keep only alphanumeric characters
            cleaned = re.sub(r'[^a-zA-Z0-9]', '', raw_text).lower()
            print(f"OCR Result: '{raw_text}' -> Cleaned: '{cleaned}'")
            return cleaned if cleaned else None
        except Exception as e:
            print(f"OCR Error: {e}")
            return None

    def auto_search(self, case_no: str, case_year: str, zone_type: str = "1", case_type: str = "1", max_retries: int = 3) -> Dict[str, Any]:
        """
        Fully automated pipeline with interactive fallback support.
        Returns a dict: { "success": bool, "html": str, "captcha_image_b64": str, "message": str }
        """
        import base64
        last_captcha_b64 = None

        for attempt in range(1, max_retries + 1):
            print(f"\n--- Attempt {attempt}/{max_retries} ---")
            try:
                captcha_path = self.get_captcha()
                # Store b64 for final fallback if needed
                with open(captcha_path, "rb") as image_file:
                    last_captcha_b64 = base64.b64encode(image_file.read()).decode('utf-8')
                
                captcha_text = self.solve_captcha(captcha_path)
                
                if not captcha_text:
                    print("OCR failed to extract text. Retrying...")
                    continue
                    
                html_result = self.fetch_diary_details(case_no, case_year, captcha_text, zone_type, case_type)
                
                if html_result and 'captcha is incorrect' not in html_result.lower():
                    return {"success": True, "html": html_result, "message": "Search successful"}
                else:
                    print("CAPTCHA was rejected by server. Retrying with a new one...")
            except Exception as e:
                print(f"Attempt {attempt} failed: {e}")
        
        # Automated OCR failed all retries. Return for frontend manual entry.
        return {
            "success": False, 
            "captcha_image_b64": last_captcha_b64, 
            "message": "Automated OCR failed all retries. Manual entry required."
        }

    def fetch_diary_details(self, case_no: str, case_year: str, captcha_text: str, zone_type="1", case_type="1") -> Optional[str]:
        """
        Executes the GET request on caseNoData to retrieve the resulting HTML 
        which should contain the Diary Number and other links.
        """
        params = {
            'zone_type': zone_type,
            'case_type': case_type,
            'case_no': case_no,
            'case_year': case_year,
            'order_by': '',
            'captcha_input': captcha_text
        }
        
        endpoint = f"{self.base_url}/judgementOrder/caseNoData"
        resp = self.session.get(endpoint, params=params, verify=False)
        
        # print(f"Status Code: {resp.status_code}")
        # print(f"Response: {resp.text}")

        if resp.status_code == 200:
            return resp.text

        print(f"Status Code: {resp.status_code}")
        return None
        
    def extract_diary_number_and_links(self, html_text: str) -> Dict:
        """Extracts the Diary Number and associated order links from the table."""
        soup = BeautifulSoup(html_text, 'html.parser')
        
        result: Dict[str, Any] = {
            'diary_number': None,
            'order_links': []
        }
        
        # 1. Search for the 'Diary Number' column index within the overarching table context 
        target_cell = None
        for table in soup.find_all('table'):
            headers = table.find_all('th')
            diary_idx = -1
            for i, th in enumerate(headers):
                if 'diary number' in th.text.lower() or 'diary no' in th.text.lower():
                    diary_idx = i
                    break
                    
            if diary_idx != -1:
                # Diary column found! Now scan all rows in the table for the corresponding <td>
                for tr in table.find_all('tr'):
                    tds = tr.find_all('td')
                    # Filter out header/spacer rows
                    if tds and len(tds) > diary_idx:
                        result['diary_number'] = tds[diary_idx].text.strip()
                        target_cell = tds[diary_idx]
                        break
                        
            if target_cell:
                break
        
        # 2. Extract href link associated ONLY with the found Diary Number cell/row
        if target_cell:
            a_tags = target_cell.find_all('a', href=True)
            # If the exact <td> doesn't have a link, scan its entire parent row just in case
            if not a_tags:
                parent_row = target_cell.find_parent('tr')
                if parent_row:
                    a_tags = parent_row.find_all('a', href=True)
                    
            for a_tag in a_tags:
                href = a_tag['href']
                full_link = href if href.startswith('http') else f"{self.base_url}/" + href.lstrip('/')
                if full_link not in result['order_links']:
                    result['order_links'].append(full_link)
        
        print(f"Extracted Diary Number: {result['diary_number']}")
        print(f"Extracted Order Links: {result['order_links']}")
        return result

    def download_first_order_link(self, details: Dict, download_dir: str = "data/orders") -> Optional[str]:
        """Helper to parse the details dict and download the first extracted order link."""
        from lawnidhi.scraper.ngt_order_scraper import NGTOrderScraper
        
        if not details.get('order_links'):
            print("No order links available to download.")
            return None
            
        downloader = NGTOrderScraper(download_dir=download_dir, session=self.session)
        diary_text = details.get('diary_number')
        diary_clean = diary_text.split()[0] if diary_text else 'unknown_diary_no'
        safe_diary = diary_clean.replace('/', '-')
        
        first_link = details['order_links'][0]
        filename = f"{safe_diary}_downloaded_order.pdf"
        print(f"Routing Intermediate Details Page Hook: {first_link}")
        
        saved_files = downloader.download_orders_from_case_page(first_link, safe_diary)
        return saved_files[0] if saved_files else None

    def list_available_orders(self, details: Dict, quiet: bool = False) -> List[Dict]:
        """
        Follows all order links from search results and collects individual
        downloadable order PDFs into a flat list. Does NOT download anything.
        
        Returns a list of dicts: [{order_date, pdf_url, suggested_filename, diary_number}, ...]
        Designed to be called from CLI or programmatic callers.
        """
        from lawnidhi.scraper.ngt_order_scraper import NGTOrderScraper
        
        if not details.get('order_links'):
            if not quiet:
                print("No order links available.")
            return []
        
        diary_text = details.get('diary_number')
        diary_clean = diary_text.split()[0] if diary_text else 'unknown_diary_no'
        safe_diary = diary_clean.replace('/', '-')
        
        all_orders = []
        import time
        import random
        
        for link in details['order_links']:
            if not quiet:
                print(f"Fetching orders from: {link}")
            try:
                # Add a small delay to mimic human behavior and maintain session stability
                time.sleep(random.uniform(1.5, 3.0))
                
                # Ensure Referer is set to avoid easy bot-detection/session-drops
                headers = {
                    'Referer': f"{self.base_url}/judgementOrder/casenumber",
                    'Upgrade-Insecure-Requests': '1'
                }
                
                resp = self.session.get(link, headers=headers, verify=False, timeout=45)
                
                if resp.status_code == 200:
                    if "Captcha is incorrect" in resp.text:
                        if not quiet:
                            print(f"[!] Session Expired or CAPTCHA rejected for page: {link}")
                        continue
                        
                    scraper = NGTOrderScraper(download_dir=".", session=self.session)
                    orders = scraper.extract_orders_from_html(resp.text, safe_diary)
                    all_orders.extend(orders)
                else:
                    if not quiet:
                        print(f"[!] Failed to fetch order page. Status: {resp.status_code}")
            except Exception as e:
                if not quiet:
                    print(f"Error fetching order page: {e}")
        
        return all_orders

    def download_selected_orders(self, orders: List[Dict], indices: Optional[List[int]] = None,
                                  download_dir: str = "data/orders") -> List[str]:
        """
        Downloads specific orders by 1-based index from a list returned by list_available_orders().
        If indices is None, downloads ALL orders.
        
        Args:
            orders: List of order dicts from list_available_orders()
            indices: 1-based indices to download, or None for all
            download_dir: Directory to save PDFs
            
        Returns: List of saved file paths
        """
        from lawnidhi.scraper.ngt_order_scraper import NGTOrderScraper
        
        if not orders:
            print("No orders to download.")
            return []
        
        downloader = NGTOrderScraper(download_dir=download_dir, session=self.session)
        
        if indices is None:
            to_download = orders
        else:
            to_download = []
            for idx in indices:
                if 1 <= idx <= len(orders):
                    to_download.append(orders[idx - 1])
                else:
                    print(f"Warning: Order #{idx} is out of range (1-{len(orders)}), skipping.")
        
        saved = []
        for order in to_download:
            path = downloader.download_pdf(order['pdf_url'], order['suggested_filename'])
            if path:
                saved.append(path)
        
        return saved

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) >= 3:
        case_no = sys.argv[1]
        case_year = sys.argv[2]
    else:
        case_input = input("Enter case number (e.g. 83/2025): ").strip()
        if '/' in case_input:
            case_no, case_year = case_input.split('/', 1)
        else:
            case_no = case_input
            case_year = input("Enter case year: ").strip()
    
    print(f"Searching for Case No: {case_no}, Year: {case_year}")
    api = DynamicSearchAPI()
    
    try:
        # Fully automated: OCR + retry
        result = api.auto_search(case_no, case_year)
        
        # If automated failed, handle CLI manual fallback
        if not result["success"] and result.get("captcha_image_b64"):
            print("\n[!] Automated OCR failed after all retries.")
            print(f"CAPTCHA has been saved to data/captcha.png for manual inspection.")
            captcha_ans = input("Please enter the CAPTCHA text: ").strip()
            
            # Manual attempt
            html_result = api.fetch_diary_details(case_no, case_year, captcha_ans)
            if html_result and 'captcha is incorrect' not in html_result.lower():
                result = {"success": True, "html": html_result}
            else:
                print("Manual verification failed. CAPTCHA was incorrect.")
                sys.exit(1)

        if result["success"]:
            html_result = result["html"]
            details = api.extract_diary_number_and_links(html_result)
            diary_text = details.get('diary_number')
            diary_clean = diary_text.split()[0] if diary_text else 'unknown_diary_no'
            
            print(f"\n[✓] Search Successful! Diary Number: {diary_clean}")
            print(f"Found {len(details.get('order_links', []))} Order Links.")
            
            # Show orders
            orders = api.list_available_orders(details, quiet=True)
            for i, order in enumerate(orders, 1):
                print(f"  {i}. {order['suggested_filename']} ({order['order_date']})")
                
            # Automatically download the first order PDF
            if orders:
                print(f"\nDownloading first order: {orders[0]['suggested_filename']}...")
                api.download_first_order_link(details)
                print("[✓] Download complete.")
        else:
            print(f"Failed to fetch Case No Data: {result.get('message')}")
    except Exception as e:
        print(f"Error: {e}")
