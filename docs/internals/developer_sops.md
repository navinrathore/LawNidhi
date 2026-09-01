# Developer SOPs & Guidelines

## 1. Updating the NGT Scraper
When the target website (NGT) updates its DOM structure:
1. **Isolate the Selector:** Update the CSS selectors or XPath only within `lawnidhi.scraper/`. Do not bleed HTML parsing logic into `cli.py`.
2. **CAPTCHA Changes:** If the CAPTCHA mechanism changes, ensure the solving logic is updated before committing, as this will break the `download-case-orders` pipeline.

## 2. Handling PDF Parser Failures (`pdfplumber`)
Unstructured legal PDFs often contain malformed tables or missing borders.
- **Regex Fallbacks:** If `pdfplumber.extract_tables()` fails, implement a regex-based fallback to extract the raw text blocks.
- **Graceful Failure:** Ensure the parser logs the exact page and Diary Number where the failure occurred, rather than throwing an unhandled exception that stops a batch sync.
