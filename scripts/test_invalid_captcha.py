from lawnidhi.scraper.dynamic_search import DynamicSearchAPI

def test_invalid_captcha():
    api = DynamicSearchAPI()
    # Step 1: Open a connection
    api.get_captcha()
    
    print("Sending an intentionally INCORRECT CAPTCHA text ('wrong123')...")
    # Step 2: Submit a wrong CAPTCHA to deliberately trigger the NGT warning page
    html_result = api.fetch_diary_details("83", "2025", "wrong123")
    
    if html_result:
        print("HTML retrieved! Testing the extraction logic to prove it doesn't crash...")
        
        # Step 3: Run the updated extraction logic that handles missing headers
        details = api.extract_diary_number_and_links(html_result)
        diary_text = details.get('diary_number')
        
        # Step 4: Validate the bug fix (no AttributeError)
        diary_clean = diary_text.split()[0] if diary_text else 'unknown_diary_no'
        
        print(f"Extracted Diary Number: {diary_clean}")
        print(f"Found {len(details.get('order_links', []))} Order Links.")
        
        # Step 5: Test the robust download method bounds
        api.download_first_order_link(details)
    else:
        print("Failed to fetch Case No Data.")

if __name__ == "__main__":
    test_invalid_captcha()
