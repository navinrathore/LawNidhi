from lawnidhi.scraper.ngt_order_scraper import NGTOrderScraper

test_html = """
<table class="table-bordered customtable" width="100%">
    <thead>
    <tr>
        <th>S.No.</th>
        <th>Date of Listing</th>
        <th>Date of Upload</th>
        <th>Coram</th>
        <th>Order/Judgement.</th>
    </tr>	
    </thead>
    <tbody>
        <tr>
            <td>1</td>
            <td>28-02-2025</td>
            <td></td>
            <td>Mr. Justice Prakash Shrivastava <br/> Dr. A. Senthil Vel<br/></td>
            <td>
            <script>/casedoc/judgements/DELHI/2025-02-28/1741081904169496122067c6cd30e9b7e.pdf</script>
            <a  href="javascript:void(0);" onclick = "myFunctionTest('L25ndF9kb2N1bWVudHMvbmd0L2Nhc2Vkb2MvanVkZ2VtZW50cy9ERUxISS8yMDI1LTAyLTI4LzE3NDEwODE5MDQxNjk0OTYxMjIwNjdjNmNkMzBlOWI3ZS5wZGY=');" class="linktext"><img title="View PDF" src="https://www.greentribunal.gov.in/sites/all/themes/ngt/images/pdficon.png"></a>
            </td>
        </tr>
    </tbody>
</table>    
"""

scraper = NGTOrderScraper(download_dir="data/orders")
print("Extracting dynamic pdf urls from onClick base64 wrappers...")
orders = scraper.extract_orders_from_html(test_html, "test_diary")

for order in orders:
    print(f"Parsed Date: {order['order_date']}")
    print(f"Decoded Base64 PDF URL: {order['pdf_url']}")
    
