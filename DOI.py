import requests
import pdfplumber
import re

def extract_doi_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                # Extract DOI
                doi_matches = re.findall(r'\b(10\.\d{4}/[^\s|]+)\b', text)
                doi = doi_matches[0] if doi_matches else None
                if doi:
                    return doi
    raise ValueError("No DOI found in the PDF.")

def get_paper_details(doi):
    url = f"https://api.crossref.org/works/{doi}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            message = data.get('message', {})
            
            #Publication Year
            publication_year = message.get('published-print', {}).get('date-parts', [["-"]])[0][0]

            #Author
            authors = message.get('author', [])
            corresponding_author = authors[-1]['family'] if authors else "-"
            
            #Citation Count
            citation_count = message.get('is-referenced-by-count', 0)

            return corresponding_author, publication_year, citation_count, message.get('reference', [])
        else:
            raise ValueError(f"Error fetching data from CrossRef: HTTP Status Code {response.status_code}")
    
    except Exception as e:
        raise RuntimeError(f"An exception occurred: {e}")

def get_referenced_dois(references):
    referenced_dois = []
    for item in references:
        if 'DOI' in item:
            referenced_dois.append(item['DOI'])
    return referenced_dois