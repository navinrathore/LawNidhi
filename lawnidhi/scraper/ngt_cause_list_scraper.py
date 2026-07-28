import os
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, date
from typing import List, Dict, Optional
from lawnidhi.parsers.ngt.cause_list_parser import NGTCauseListParser
from lawnidhi.db.ingest import ingest_schedule
from lawnidhi.db import cause_list_repo
import urllib3

# Suppress SSL warnings for government sites with self-signed certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class NGTCauseListScraper:
    """Scraper for NGT Chairperson Bench cause lists."""
    
    BASE_URL = "https://www.greentribunal.gov.in/principal-chairperson-bench"
    DOWNLOAD_DIR = "data/cause_lists"

    def __init__(self):
        os.makedirs(self.DOWNLOAD_DIR, exist_ok=True)
        self.parser = NGTCauseListParser()

    def _parse_link_text(self, text: str) -> Optional[Dict]:
        """
        Extracts date, type, and court from link text.
        Example: "Click here to see 25th March 2026 Cause List of Court-1..."
        """
        # Clean text
        text = text.replace('\n', ' ').strip()
        
        # Regex for date: "25th March 2026"
        date_match = re.search(r'(\d+)(st|nd|rd|th)?\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})', text, re.IGNORECASE)
        if not date_match:
            return None
            
        day = date_match.group(1)
        month = date_match.group(3)
        year = date_match.group(4)
        date_str = f"{day} {month} {year}"
        
        try:
            list_date = datetime.strptime(date_str, "%d %B %Y").date()
        except ValueError:
            return None
            
        # Determine Type
        list_type = "Final"
        if "ADVANCE" in text.upper():
            list_type = "Advance"
        elif "SUPPLEMENTARY" in text.upper():
            list_type = "Supplementary"
        elif "TENTATIVE" in text.upper():
            list_type = "Tentative"
            
        # Determine Court
        court_no = "1" # Default to Court 1
        court_match = re.search(r'Court\s*No?\.?\s*(\d+)', text, re.IGNORECASE)
        if court_match:
            court_no = court_match.group(1)
            
        return {
            'date': list_date,
            'type': list_type,
            'court_no': court_no,
            'description': text
        }

    def fetch_list_links(self) -> List[Dict]:
        """Scrapes the chairperson bench page for cause list links."""
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(self.BASE_URL, headers=headers, verify=False)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        links = []
        
        # Look for links containing "Click here to see"
        for a in soup.find_all('a', href=True):
            text = a.get_text()
            if "CLICK HERE TO SEE" in text.upper():
                meta = self._parse_link_text(text)
                if meta:
                    meta['url'] = a['href']
                    if not meta['url'].startswith('http'):
                        meta['url'] = "https://www.greentribunal.gov.in" + meta['url']
                    links.append(meta)
                    
        return links

    def download_file(self, url: str, filename: str) -> str:
        """Downloads a PDF file and returns the local path."""
        path = os.path.join(self.DOWNLOAD_DIR, filename)
        
        # We always download as content might have changed (e.g. Advance -> Final update)
        # But if the filename is unique to date/type, we could skip.
        # NGT often reuses URLs for the same slot.
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, stream=True, verify=False)
        response.raise_for_status()
        
        with open(path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        return path

    def sync(self, start_date: date = None):
        """
        Main sync loop: Scans links, downloads new ones, parses and ingests.
        By default, starts from today.
        """
        if not start_date:
            start_date = date.today()
            
        print(f"Syncing cause lists from {start_date} onwards...")
        links = self.fetch_list_links()
        
        found_count = 0
        skipped_count = 0
        processed_count = 0
        
        for link in links:
            if link['date'] < start_date:
                continue
                
            found_count += 1
            # DEBUG: Print details of all found lists
            print(f"  [DEBUG] Found: {link['date']} | {link['type']} | Court {link['court_no']}")
            
            # Construct local filename: YYYY-MM-DD_Type_Court.pdf
            filename = f"{link['date'].isoformat()}_{link['type']}_C{link['court_no']}.pdf"
            
            # Check if already processed (identical source URL and path exists)
            # Actually, user wants Advance to be updated with Final.
            # Our ingest_schedule handles duplicate logic and deletion of old Advance lists.
            
            existing = cause_list_repo.get_cause_list_record(link['date'], link['type'], link['court_no'])
            if existing and existing['source_url'] == link['url'] and os.path.exists(existing['file_path']):
                 # Skip if source URL is identical and file exists
                 skipped_count += 1
                 continue

            print(f"Downloading: {link['date']} ({link['type']}) - Court {link['court_no']}")
            try:
                local_path = self.download_file(link['url'], filename)
                
                # Parse and Ingest
                schedule = self.parser.parse(local_path)
                # Ensure the parser caught the correct date/type from PDF
                # If not, override with what we saw on the website
                schedule.date = link['date']
                schedule.list_type = link['type']
                schedule.court_no = link['court_no']
                
                ingest_schedule(schedule)
                
                # Update tracking record
                cause_list_repo.add_cause_list_record(
                    link['date'], link['type'], link['court_no'], 
                    local_path, link['url']
                )
                processed_count += 1
                
            except Exception as e:
                print(f"Error processing {filename}: {e}")
                
        print("-" * 40)
        print(f"Sync complete:")
        print(f"  Total found      : {found_count}")
        print(f"  Already processed: {skipped_count}")
        print(f"  Newly downloaded : {processed_count}")
        print("-" * 40)
        return processed_count

if __name__ == "__main__":
    scraper = NGTCauseListScraper()
    scraper.sync()
