from lawnidhi.scraper.ngt_order_scraper import NGTOrderScraper

def test_fetch_orders():
    url = "https://www.greentribunal.gov.in/caseDetails/DELHI/0701102002572025?page=order"
    scraper = NGTOrderScraper(download_dir="data/orders")
    
    saved = scraper.download_orders_from_case_page(url, "0701102002572025")
    print(f"Resulting file paths: {saved}")

if __name__ == "__main__":
    test_fetch_orders()
