# create_index.py
import requests
from bs4 import BeautifulSoup
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import DirectoryLoader, UnstructuredURLLoader
import os
from urllib.parse import urljoin, urlparse
import time
import re

# --- Configuration ---
if 'GOOGLE_API_KEY' not in os.environ:
    print("Error: GOOGLE_API_KEY environment variable not set.")
    exit()

BASE_URL = "https://smkn2indramayu.sch.id/"
FAISS_INDEX_PATH = "faiss_index"
LOCAL_FILES_PATH = "documents"

def get_sitemap_urls(base_url):
    """
    Tries to find and parse a sitemap.xml file.
    """
    sitemap_url = urljoin(base_url, "sitemap.xml")
    urls = []
    try:
        response = requests.get(sitemap_url, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "xml")
            locs = soup.find_all("loc")
            urls = [loc.text for loc in locs]
            print(f"Found {len(urls)} URLs in sitemap.xml")
    except requests.RequestException as e:
        print(f"Could not fetch or parse sitemap: {e}")
    return urls

def crawl_and_scrape(base_url):
    """
    Recursively crawls pages from the base URL and scrapes their text content.
    It now starts with sitemap URLs and then crawls found links.
    """
    sitemap_urls = get_sitemap_urls(base_url)
    to_visit = set(sitemap_urls)
    to_visit.add(base_url)
    visited = set()
    all_text = ""
    
    # Use UnstructuredURLLoader for potentially better text extraction
    # and handling of different file types linked from the URLs.
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    
    while to_visit:
        url = to_visit.pop()
        if url in visited or not url.startswith(BASE_URL):
            continue
            
        print(f"Scraping {url}...")
        visited.add(url)
        
        try:
            # Add a small delay to be polite to the server
            time.sleep(1) 
            
            response = requests.get(url, timeout=15, headers=headers)
            response.raise_for_status()

            # Simple content type check
            content_type = response.headers.get('content-type', '')
            if 'text/html' in content_type:
                soup = BeautifulSoup(response.content, "html.parser")

                # Remove script, style, nav, footer for cleaner text
                for element in soup(["script", "style", "nav", "footer", "header"]):
                    element.decompose()

                text = soup.get_text()
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                page_text = "\n".join(chunk for chunk in chunks if chunk)
                all_text += "\n\n" + page_text

                # Find all links and add new ones to the to_visit set
                for link in soup.find_all('a', href=True):
                    absolute_link = urljoin(url, link['href'])
                    parsed_link = urlparse(absolute_link)
                    clean_link = parsed_link._replace(fragment="").geturl()
                    
                    # Add to to_visit if it's a new link within the same domain
                    if clean_link not in visited and clean_link not in to_visit:
                         if clean_link.startswith(BASE_URL):
                            to_visit.add(clean_link)
            else:
                 print(f"Skipping non-HTML content at {url}")


        except requests.RequestException as e:
            print(f"Error scraping {url}: {e}")
            
    return all_text


def load_local_documents(path):
    """Loads documents from a local directory."""
    print(f"Loading documents from {path}...")
    loader = DirectoryLoader(path, glob="**/*", show_progress=True)
    documents = loader.load()
    print(f"Loaded {len(documents)} documents.")
    return documents

def main():
    """Main function to create and save the vector index."""
    # 1. Crawl the website and get all text content
    print("Starting website crawl...")
    website_text = crawl_and_scrape(BASE_URL)
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    scraped_texts = text_splitter.split_text(website_text)
    print(f"Created {len(scraped_texts)} text chunks from the entire website.")

    # 2. Load local documents
    if not os.path.exists(LOCAL_FILES_PATH):
        os.makedirs(LOCAL_FILES_PATH)
        print(f"Created '{LOCAL_FILES_PATH}' directory. Add your documents there and run again.")
    
    local_docs = load_local_documents(LOCAL_FILES_PATH)
    
    # 3. Combine and split all documents
    all_content = scraped_texts + [doc.page_content for doc in local_docs]
    if not all_content:
        print("No content to index. Exiting.")
        return

    print("Splitting all combined text into chunks...")
    final_docs = text_splitter.create_documents(all_content)
    print(f"Total documents to index: {len(final_docs)}")

    # 4. Create embeddings and the FAISS vector store
    print("Creating embeddings and FAISS index...")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vectorstore = FAISS.from_documents(final_docs, embeddings)

    # 5. Save the FAISS index locally
    vectorstore.save_local(FAISS_INDEX_PATH)
    print(f"✅ Index saved successfully to '{FAISS_INDEX_PATH}' folder!")

if __name__ == "__main__":
    main()