# DOI.py
import requests
import pdfplumber
import re

def extract_doi_from_pdf(pdf_path):
    doi_pattern = r'\b(10\.\d{4,}/[^\s]+)\b'
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                doi_matches = re.findall(doi_pattern, text)
                if doi_matches:
                    doi = doi_matches[0].strip().rstrip('.')
                    return doi
    raise ValueError("No DOI found in the PDF.")

def get_paper_details(doi):
    url = f"https://api.crossref.org/works/{doi}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            message = data.get('message', {})
            
            # Year
            date_info = message.get('published-print') or message.get('published-online') or message.get('published')
            publication_year = None
            if date_info and 'date-parts' in date_info:
                try:
                    publication_year = date_info['date-parts'][0][0]
                except (IndexError, TypeError):
                    pass

            # Author
            authors_list = message.get('author', [])
            last_author_name = "Unknown"
            if authors_list:
                last_author = authors_list[-1]
                last_author_name = last_author.get('family') or last_author.get('name') or "Unknown"

            citation_count = message.get('is-referenced-by-count', 0)
            return last_author_name, publication_year, citation_count, message.get('reference', [])
        
        elif response.status_code == 404:
            raise ValueError(f"DOI not found: {doi}")
        else:
            raise ValueError(f"HTTP Error {response.status_code}")
    except Exception as e:
        raise RuntimeError(f"Error fetching {doi}: {e}")

def get_referenced_dois(references):
    if not references: return []
    return [item['DOI'] for item in references if item and 'DOI' in item]

def get_citing_papers(doi):
    """
    Finds papers that cite the given DOI.
    Returns a list of dictionaries.
    """
    url = f"https://api.crossref.org/works?filter=references:{doi}&select=DOI,title,is-referenced-by-count,author,published-print,published-online&rows=50"
    
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            items = data.get('message', {}).get('items', [])
            
            results = []
            for item in items:
                # Extract Year
                date_info = item.get('published-print') or item.get('published-online')
                year = None
                if date_info and 'date-parts' in date_info:
                    try:
                        year = date_info['date-parts'][0][0]
                    except:
                        pass
                
                # Extract Author
                authors = item.get('author', [])
                author_name = "Unknown"
                if authors:
                    author_name = authors[0].get('family', 'Unknown')

                results.append({
                    'doi': item.get('DOI'),
                    'title': item.get('title', ['No Title'])[0],
                    'citations': item.get('is-referenced-by-count', 0),
                    'year': year,
                    'author': author_name,
                    'source': 'Citing Paper' # Default source
                })
            return results
        else:
            return []
    except Exception as e:
        print(f"Error fetching citing papers: {e}")
        return []