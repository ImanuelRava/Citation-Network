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
    """Fetches author, year, citation count, references, and title for a DOI."""
    url = f"https://api.crossref.org/works/{doi}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        
        msg = resp.json()['message']

        # Year
        date_info = msg.get('published-print') or msg.get('published-online') or msg.get('published', {})
        year = date_info.get('date-parts', [[None]])[0][0]

        # Author
        authors = msg.get('author', [])
        author = "Unknown"
        if authors:
            last_author = authors[-1]
            author = last_author.get('family') or last_author.get('name') or "Unknown"

        # Title
        title_list = msg.get('title', [])
        title = title_list[0] if title_list else "No Title"

        return author, year, msg.get('is-referenced-by-count', 0), msg.get('reference', []), title

    except requests.exceptions.HTTPError:
        raise ValueError(f"DOI not found: {doi}")
    except Exception as e:
        raise RuntimeError(f"Error fetching {doi}: {e}")

def get_referenced_dois(references):
    """Extracts DOIs from a list of reference objects."""
    if not references: return []
    return [ref['DOI'] for ref in references if ref and 'DOI' in ref]

def get_forward_citations(doi):
    """
    Queries an external academic graph API to find papers citing the given DOI.
    Also retrieves the list of works each paper references to enable cross-reference checking.
    """
    base_url = "https://api.openalex.org"
    
    # Step 1: Find the work ID for the DOI
    search_url = f"{base_url}/works/doi:{doi}"
    
    try:
        # 1. Find the work ID
        resp = requests.get(search_url, timeout=10)
        if resp.status_code != 200:
            return []
        
        work_data = resp.json()
        work_id = work_data.get('id')
        
        if not work_id:
            return []

        # Step 2: Get papers that cite this work
        # We select 'referenced_works' to know what these papers cite
        citations_url = f"{base_url}/works?filter=cites:{work_id}&per_page=100&select=id,doi,display_name,publication_year,cited_by_count,authorships,referenced_works"
        
        resp = requests.get(citations_url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            items = data.get('results', [])
            
            results = []
            for item in items:
                # Author extraction
                authors = item.get('authorships', [])
                author_name = "Unknown"
                if authors:
                    author_name = authors[0].get('author', {}).get('display_name', 'Unknown')

                results.append({
                    'id': item.get('id'), # OpenAlex ID (e.g., https://openalex.org/W1234)
                    'doi': item.get('doi'),
                    'title': item.get('display_name', 'No Title'),
                    'citations': item.get('cited_by_count', 0),
                    'year': item.get('publication_year'),
                    'author': author_name,
                    'referenced_ids': item.get('referenced_works', []) # List of IDs this paper cites
                })
            return results
        else:
            return []
            
    except Exception as e:
        print(f"API Error: {e}")
        return []