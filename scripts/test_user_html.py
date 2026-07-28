from lawnidhi.scraper.dynamic_search import DynamicSearchAPI

test_html = """
<div class="table-responsive">
    <table class="table-bordered customtable" width="100%">
        <thead>
            <tr>
                <th>Sr. No.</th>
                <th>Zonal Bench</th>
                <th>Diary Number</th>
                <th>Case Number/Location Code</th>
                <th>Party Name</th>
                <th style="width:10px;">Order Date</th>
                <th>Case Status</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>1</td>
                <!--judgementOrderDetails-->
                <td><a href="https://www.greentribunal.gov.in/caseDetails/DELHI/0701102002572025?page=order" class="linkurl">NEW DELHI (PRINCIPAL BENCH)</a></td>
                <td><a href="https://www.greentribunal.gov.in/caseDetails/DELHI/0701102002572025?page=order" class="linkurl">070110200257/2025</a></td>
                <td><a href="https://www.greentribunal.gov.in/caseDetails/DELHI/0701102002572025?page=order" class="linkurl">Original Application No. 83/2025 / DELHI</a></td>
                <td><a href="https://www.greentribunal.gov.in/caseDetails/DELHI/0701102002572025?page=order" class="linkurl">SHAKUNTLA... </a></td>
                <td><a href="https://www.greentribunal.gov.in/caseDetails/DELHI/0701102002572025?page=order" class="linkurl">28-02-2025</a></td>
                <td><a href="https://www.greentribunal.gov.in/caseDetails/DELHI/0701102002572025?page=order" class="linkurl"><font style="color:green;font-size:13px;font-weight:bold;">DISPOSED</font></a></td>
            </tr>
        </tbody>
    </table>
</div>
"""

api = DynamicSearchAPI()
print("Extracting details from User HTML...")
details = api.extract_diary_number_and_links(test_html)
