# create_index.py
import requests
from bs4 import BeautifulSoup
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import DirectoryLoader
import os

# --- Configuration ---
if 'GOOGLE_API_KEY' not in os.environ:
    print("Error: GOOGLE_API_KEY environment variable not set.")
    exit()

URL = "https://smkn2indramayu.sch.id/"
FAISS_INDEX_PATH = "faiss_index"
LOCAL_FILES_PATH = "documents" # Create a folder named 'documents' and place your files there

def scrape_website(url):
    """Scrapes the text content from a given URL."""
    print(f"Scraping {url}...")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()

        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = "\n".join(chunk for chunk in chunks if chunk)
        print("Scraping finished successfully.")
        return text
    except requests.RequestException as e:
        print(f"Error scraping website: {e}")
        return None

def load_local_documents(path):
    """Loads documents from a local directory."""
    print(f"Loading documents from {path}...")
    # This loader will automatically handle .pdf, .docx, .txt, and many other file types.
    loader = DirectoryLoader(path, glob="**/*", show_progress=True)
    documents = loader.load()
    print(f"Loaded {len(documents)} documents.")
    return documents

def main():
    """Main function to create and save the vector index."""
    # 1. Scrape the website content
    raw_text = scrape_website(URL)
    scraped_texts = []
    if raw_text:
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        scraped_texts = text_splitter.split_text(raw_text)
    print(f"Created {len(scraped_texts)} text chunks from website.")

    # 2. Load local documents
    if not os.path.exists(LOCAL_FILES_PATH):
        os.makedirs(LOCAL_FILES_PATH)
        print(f"Created '{LOCAL_FILES_PATH}' directory. Please add your documents there and run this script again.")
        return

    local_docs = load_local_documents(LOCAL_FILES_PATH)
    
    # 3. Combine and split all documents
    all_texts = scraped_texts + [doc.page_content for doc in local_docs]
    if not all_texts:
        print("No content to index. Exiting.")
        return

    print("Splitting all combined text into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    final_texts = text_splitter.create_documents(all_texts)
    print(f"Total documents to index: {len(final_texts)}")

    # 4. Create embeddings and the FAISS vector store
    print("Creating embeddings and FAISS index...")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vectorstore = FAISS.from_documents(final_texts, embeddings)

    # 5. Save the FAISS index locally
    vectorstore.save_local(FAISS_INDEX_PATH)
    print(f"✅ Index saved successfully to '{FAISS_INDEX_PATH}' folder!")

if __name__ == "__main__":
    main()