# create_index.py
import requests
from bs4 import BeautifulSoup
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import DirectoryLoader
import os
from urllib.parse import urljoin, urlparse

# --- Configuration ---
if 'GOOGLE_API_KEY' not in os.environ:
    print("Error: GOOGLE_API_KEY environment variable not set.")
    exit()

BASE_URL = "https://smkn2indramayu.sch.id/"
FAISS_INDEX_PATH = "faiss_index"
LOCAL_FILES_PATH = "documents"

def crawl_and_scrape(url, visited=set()):
    """
    Recursively crawls pages from the base URL and scrapes their text content.
    """
    # 1. Check if the URL should be visited
    if url in visited or not url.startswith(BASE_URL):
        return "", visited
    
    print(f"Scraping {url}...")
    visited.add(url)

    try:
        # 2. Fetch and parse the page content
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()

        # 3. Extract text from the current page
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        page_text = "\n".join(chunk for chunk in chunks if chunk)
        
        all_text = page_text

        # 4. Find all links and recursively crawl them
        for link in soup.find_all('a', href=True):
            absolute_link = urljoin(url, link['href'])
            # Ensure the link is clean (remove fragments) and within the same domain
            parsed_link = urlparse(absolute_link)
            clean_link = parsed_link._replace(fragment="").geturl()

            # Recursively call the function for new, valid links
            new_text, visited = crawl_and_scrape(clean_link, visited)
            all_text += "\n" + new_text
            
        return all_text, visited

    except requests.RequestException as e:
        print(f"Error scraping {url}: {e}")
        return "", visited

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
    website_text, _ = crawl_and_scrape(BASE_URL)
    
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