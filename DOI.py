# DOI.py
import requests
import pdfplumber
import re

def extract_doi_from_pdf(pdf_path):
    """Extracts the first found DOI from a PDF file."""
    pattern = r'\b(10\.\d{4,}/[^\s]+)\b'
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                match = re.search(pattern, text)
                if match:
                    return match.group(0).strip().rstrip('.')
    raise ValueError("No DOI found in the PDF.")

def get_paper_details(doi):
    """Fetches author, year, citation count, and references for a DOI."""
    url = f"https://api.crossref.org/works/{doi}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status() # Raises error for 404, 500, etc.
        
        msg = resp.json()['message']

        # Year: check print, then online, then generic
        date_info = msg.get('published-print') or msg.get('published-online') or msg.get('published', {})
        year = date_info.get('date-parts', [[None]])[0][0]

        # Author: get last author's family name
        authors = msg.get('author', [])
        author = "Unknown"
        if authors:
            last_author = authors[-1]
            author = last_author.get('family') or last_author.get('name') or "Unknown"

        return author, year, msg.get('is-referenced-by-count', 0), msg.get('reference', [])

    except requests.exceptions.HTTPError:
        raise ValueError(f"DOI not found: {doi}")
    except Exception as e:
        raise RuntimeError(f"Error fetching {doi}: {e}")

def get_referenced_dois(references):
    """Extracts DOIs from a list of reference objects."""
    if not references: return []
    return [ref['DOI'] for ref in references if ref and 'DOI' in ref]