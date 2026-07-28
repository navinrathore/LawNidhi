import pdfplumber
import pprint
import sys

def explore(pdf_path):
    print(f"Opening: {pdf_path}")
    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"Total pages: {len(pdf.pages)}")
            
            for page_num in range(min(2, len(pdf.pages))):
                page = pdf.pages[page_num]
                print(f"\n--- Page {page_num + 1} Text ---")
                text = page.extract_text()
                if text:
                    print(text[:1000]) # First 1000 chars
                else:
                    print("No text found.")
                
                print(f"\n--- Page {page_num + 1} Tables ---")
                tables = page.extract_tables()
                if not tables:
                    print("No tables found.")
                for i, table in enumerate(tables):
                    print(f"Table {i}:")
                    pprint.pprint(table[:3]) # Print first 3 rows of each table
    except Exception as e:
        print(f"Error reading PDF: {e}")

if __name__ == "__main__":
    pdf_path = "/home/navin/work/AI/LawNidhi/data/cause_list_sample.pdf"
    explore(pdf_path)
