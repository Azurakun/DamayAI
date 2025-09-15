# app.py
from flask import Flask, render_template, request, jsonify
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
import os
import re
from dotenv import load_dotenv

# --- Konfigurasi ---
load_dotenv() # Memuat variabel dari file .env

FAISS_INDEX_PATH = "faiss_index"

# --- Inisialisasi Aplikasi Flask ---
app = Flask(__name__)

# --- Muat Model dan Indeks ---
print("Memuat indeks FAISS dan model...")
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
vector_index = FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.8)
print("✅ Model dan indeks berhasil dimuat.")


def get_conversational_chain():
    """Membuat dan mengembalikan conversational QA chain."""
    # --- PROMPT DIMODIFIKASI UNTUK MENYERTAKAN RIWAYAT OBROLAN ---
    prompt_template = """
    Anda adalah "Damay", asisten AI yang ramah untuk SMKN 2 Indramayu.
    Gunakan gaya percakapan yang alami dalam Bahasa Indonesia.

    Jawab pertanyaan pengguna berdasarkan konteks yang relevan dari dokumen sekolah dan riwayat percakapan sebelumnya.
    Jika informasi tidak ditemukan, katakan dengan sopan. Jangan mengarang jawaban.
    
    Riwayat Percakapan Sebelumnya:
    {chat_history}

    Konteks Dokumen:
    {context}

    Pertanyaan Pengguna:
    {question}

    Jawaban Ramah Damay:
    """
    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["chat_history", "context", "question"]
    )
    chain = load_qa_chain(llm, chain_type="stuff", prompt=prompt)
    return chain

# --- Rute API ---
@app.route("/")
def index():
    """Merender halaman utama chat."""
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    """Menangani permintaan POST dari chat."""
    try:
        data = request.json
        user_question = data.get("message")
        chat_history = data.get("history", []) # Terima riwayat obrolan dari frontend

        if not user_question:
            return jsonify({"error": "Pesan tidak ditemukan"}), 400

        # Format riwayat obrolan untuk ditampilkan di prompt
        formatted_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in chat_history])

        # 1. Temukan dokumen yang relevan
        docs = vector_index.similarity_search(user_question, k=5)

        # 2. Dapatkan respons dari model Gemini
        chain = get_conversational_chain()
        response = chain(
            {"input_documents": docs, "chat_history": formatted_history, "question": user_question},
            return_only_outputs=True
        )

        output_text = response["output_text"]

        # 3. Pisahkan jawaban dan rekomendasi
        answer = output_text
        recommended_questions = []
        
        match = re.search(r'Pertanyaan Rekomendasi:|Rekomendasi Pertanyaan:', output_text, re.IGNORECASE)
        if match:
            split_keyword = match.group(0)
            parts = output_text.split(split_keyword)
            answer = parts[0].strip()
            raw_questions = parts[1].strip()
            recommended_questions = re.findall(r'[\s*-]?\s*(.*?)\??$', raw_questions, re.MULTILINE)
            recommended_questions = [q.strip() for q in recommended_questions if q.strip()]

        return jsonify({
            "reply": answer,
            "recommended_questions": recommended_questions
        })

    except Exception as e:
        print(f"Error pada endpoint /chat: {e}")
        return jsonify({"error": "Terjadi kesalahan internal."}), 500

# --- Jalankan Aplikasi ---
if __name__ == "__main__":
    app.run(debug=True)