# create_index.py
import requests
from bs4 import BeautifulSoup
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
import os

# --- Configuration ---
# You must set your GOOGLE_API_KEY as an environment variable
# For example, in your terminal: export GOOGLE_API_KEY="YOUR_API_KEY"
if 'GOOGLE_API_KEY' not in os.environ:
    print("Error: GOOGLE_API_KEY environment variable not set.")
    exit()

URL = "https://smkn2indramayu.sch.id/"
FAISS_INDEX_PATH = "faiss_index"

def scrape_website(url):
    """Scrapes the text content from a given URL."""
    print(f"Scraping {url}...")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Remove script and style elements
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

def main():
    """Main function to create and save the vector index."""
    # 1. Scrape the website content
    raw_text = scrape_website(URL)
    if not raw_text:
        print("Could not retrieve website content. Exiting.")
        return

    # 2. Split the text into manageable chunks
    print("Splitting text into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100
    )
    texts = text_splitter.split_text(raw_text)
    print(f"Created {len(texts)} text chunks.")

    # 3. Create embeddings and the FAISS vector store
    print("Creating embeddings and FAISS index...")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    
    # This process can take a moment as it calls the API for each chunk
    vectorstore = FAISS.from_texts(texts, embeddings)
    
    # 4. Save the FAISS index locally
    vectorstore.save_local(FAISS_INDEX_PATH)
    print(f"✅ Index saved successfully to '{FAISS_INDEX_PATH}' folder!")

if __name__ == "__main__":
    main()