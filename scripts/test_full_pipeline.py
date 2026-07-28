import time
import os
from lawnidhi.scraper.dynamic_search import DynamicSearchAPI

def run_ipc_pipeline():
    api = DynamicSearchAPI()
    
    # 1. Pull the Captcha via the persistent requests.Session
    print("Initiating Pipeline...")
    api.get_captcha()
    print("CAPTCHA saved to data/captcha.png.")
    print("Waiting up to 30 seconds for data/captcha_ans.txt...")
    
    # 2. Asynchronous File-based Inter-Process Communication
    ans = None
    if os.path.exists("data/captcha_ans.txt"):
        os.remove("data/captcha_ans.txt")
        
    for _ in range(30):
        if os.path.exists("data/captcha_ans.txt"):
            with open("data/captcha_ans.txt", "r") as f:
                ans = f.read().strip()
            if ans:
                print(f"IPC Payload received! CAPTCHA: {ans}")
                os.remove("data/captcha_ans.txt")
                break
        time.sleep(1)
        
    if not ans:
        print("Timeout waiting for IPC solution.")
        return
        
    # 3. Resume the authorized Session Pipeline!
    # Hardcoded Diary inputs for "Original Application No. 83/2025"
    html_result = api.fetch_diary_details("83", "2025", ans, zone_type="1", case_type="1")
    
    if html_result:
        details = api.extract_diary_number_and_links(html_result)
        diary_text = details.get('diary_number')
        diary_clean = diary_text.split()[0] if diary_text else 'unknown_diary_no'
        
        print(f"HTML retrieved! Extracted Diary Number: {diary_clean}")
        
        # 4. Trigger the dynamically bridged NGTOrderScraper Base64 Decoder!
        api.download_first_order_link(details)
    else:
        print("Failed to fetch Case No Data HTML.")

if __name__ == "__main__":
    run_ipc_pipeline()
