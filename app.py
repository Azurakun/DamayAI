# app.py
from flask import Flask, render_template, request, jsonify
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
import os

# --- Configuration ---
# Ensure the GOOGLE_API_KEY is set as an environment variable
if 'GOOGLE_API_KEY' not in os.environ:
    raise ValueError("Error: GOOGLE_API_KEY environment variable not set.")

FAISS_INDEX_PATH = "faiss_index"

# --- Flask App Initialization ---
app = Flask(__name__)

# --- Load Models and Index ---
# This is done once when the server starts
print("Loading FAISS index and models...")
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
vector_index = FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.7)
print("✅ Models and index loaded.")


def get_conversational_chain():
    """Creates and returns a conversational QA chain."""
    prompt_template = """
    You are a helpful assistant for the SMKN 2 Indramayu school website.
    Your task is to answer the user's question based only on the provided context.
    If the information is not in the context, politely say that you don't have that information from the website.
    Do not make up answers. Be concise and friendly.
    
    Context:
    {context}
    
    Question:
    {question}
    
    Answer:
    """
    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "question"]
    )
    chain = load_qa_chain(llm, chain_type="stuff", prompt=prompt)
    return chain

# --- API Routes ---
@app.route("/")
def index():
    """Renders the main chat page."""
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    """Handles the chat POST request."""
    try:
        user_question = request.json.get("message")
        if not user_question:
            return jsonify({"error": "No message provided"}), 400

        # 1. Find relevant documents from our vector store
        docs = vector_index.similarity_search(user_question, k=4)
        
        # 2. Get the response from the Gemini model
        chain = get_conversational_chain()
        response = chain({"input_documents": docs, "question": user_question}, return_only_outputs=True)
        
        return jsonify({"reply": response["output_text"]})

    except Exception as e:
        print(f"Error in /chat endpoint: {e}")
        return jsonify({"error": "An internal error occurred."}), 500

# --- Run the App ---
if __name__ == "__main__":
    app.run(debug=True)