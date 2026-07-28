from lawnidhi.scraper.dynamic_search import DynamicSearchAPI

test_html = """
<table>
    <tr>
        <th>Diary Number</th>
        <td>0701102002572025 <a href="gen_pdf_test.php?foo=bar">Order Link 1</a></td>
    </tr>
    <tr>
        <th>Filing Date</th>
        <td>2025-01-01</td>
    </tr>
</table>
"""

api = DynamicSearchAPI()
print("Extracting details from HTML...")
details = api.extract_diary_number_and_links(test_html)
print(f"Diary Number: {details['diary_number']}")
print(f"Order Links: {details['order_links']}")
api.download_first_order_link(details)
