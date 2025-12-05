import os
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import GoogleGenerativeAIEmbeddings
import google.generativeai as genai

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=API_KEY)

EMBEDDING_MODEL = "models/embedding-001"
LLM_MODEL = "gemini-pro"
VECTOR_DIR = "vector_store"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100

def load_vector_store():
    if os.path.exists(VECTOR_DIR):
        return FAISS.load_local(
            VECTOR_DIR,
            GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL),
            allow_dangerous_deserialization=True
        )
    return None

def create_vector_store(texts):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    )
    chunks = splitter.split_text(texts)

    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)
    vectordb = FAISS.from_texts(chunks, embedding=embeddings)
    vectordb.save_local(VECTOR_DIR)
    return vectordb

def rag_answer(question, vectordb):
    docs = vectordb.similarity_search(question, k=5)
    context = "\n".join([d.page_content for d in docs])

    prompt = f"""
あなたは野々市市の生活情報に詳しいAIです。
以下の文書内容に基づいて、正確に回答してください。

【文脈】
{context}

【質問】
{question}

【回答】
"""

    response = genai.GenerativeModel(LLM_MODEL).generate_content(prompt)
    return response.text

    
