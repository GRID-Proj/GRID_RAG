import os
import shutil
import time
import gc
import stat
import json
from typing import List, Optional

from chromadb.config import Settings as ChromaSettings
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_chroma import Chroma
from langchain.schema.output_parser import StrOutputParser
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema.runnable import RunnablePassthrough
from langchain.prompts import PromptTemplate
from langchain.schema import Document
from langchain_community.vectorstores.utils import filter_complex_metadata

VECTOR_DB_PATH = os.path.join("vectorstores", "default")
UPLOADED_FILES_LOG = os.path.join(VECTOR_DB_PATH, "files.txt")


class ChatPDF:
    def __init__(self, chunk_size: int = 750, chunk_overlap: int = 100):
        # Model and embeddings
        self.model = ChatOllama(model="deepseek-r1:1.5b")
        self.embedding = OllamaEmbeddings(model="nomic-embed-text")
        
        # Text splitting
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        # Prompt template
        self.prompt = PromptTemplate.from_template("""
<s>[INST] You are an expert assistant specialized in structural and geotechnical tunnel engineering. 
Use ONLY the information retrieved from the provided documents (PDFs, JSONs) to answer. 
Do NOT invent tests, simulations, or geological information that is not in the documents. 
Do not use lists or line breaks. Provide a detailed and complete answer based on the provided documents.
If the answer is not in the context, say: "The answer is not in the provided documents."

Question: {question}
Context: {context}

[/INST]</s>
""")
        
        # Vector store
        self.db_path = VECTOR_DB_PATH
        self.vector_store: Optional[Chroma] = None
        self.retriever: Optional[any] = None
        self.chain: Optional[any] = None
        
        # Load existing vector store if available
        self._load_vector_store()

    # --- Chroma settings ---
    def _chroma_settings(self) -> ChromaSettings:
        return ChromaSettings(
            persist_directory=self.db_path,
            allow_reset=True,
            anonymized_telemetry=False
        )

    # --- Load vector store ---
    def _load_vector_store(self):
        db_file = os.path.join(self.db_path, "chroma.sqlite3")
        if os.path.exists(db_file):
            self.vector_store = Chroma(
                persist_directory=self.db_path,
                embedding_function=self.embedding,
                client_settings=self._chroma_settings()
            )
            self.retriever = self.vector_store.as_retriever(
                search_type="similarity_score_threshold",
                search_kwargs={"k": 8, "score_threshold": 0.3}
            )
            self.chain = (
                {"context": self.retriever, "question": RunnablePassthrough()}
                | self.prompt
                | self.model
                | StrOutputParser()
            )

    # --- PDF ingestion ---
    def ingest(self, pdf_file_path: str):
        os.makedirs(self.db_path, exist_ok=True)
        docs = PyPDFLoader(file_path=pdf_file_path).load()
        chunks = self.text_splitter.split_documents(docs)
        chunks = filter_complex_metadata(chunks)

        file_name = os.path.basename(pdf_file_path)
        for chunk in chunks:
            chunk.metadata['source_file'] = file_name

        if not chunks:
            raise ValueError(f"No content extracted from PDF: {file_name}")

        if not self.vector_store:
            self.vector_store = Chroma.from_documents(
                documents=chunks,
                embedding=self.embedding,
                persist_directory=self.db_path,
                client_settings=self._chroma_settings()
            )
        else:
            self.vector_store.add_documents(chunks)

        self._log_uploaded_file(file_name)
        self._load_vector_store()

    # --- JSON ingestion ---
    def ingest_json(self, json_path: str):
        def extract_documents(data) -> List[Document]:
            docs = []
            if isinstance(data, dict):
                if "defectList" in data:
                    for entry in data["defectList"]:
                        text = "\n".join(f"{k}: {v}" for k, v in entry.items())
                        docs.append(Document(page_content=text, metadata={"source": os.path.basename(json_path)}))
                elif "category" in data:
                    for cat in data.get("category", []):
                        for entry in cat.get("elements", []):
                            text = "\n".join(f"{k}: {v}" for k, v in entry.items())
                            docs.append(Document(page_content=text, metadata={"source": os.path.basename(json_path)}))
            return docs

        with open(json_path, 'r', encoding='utf-8-sig') as f:
            json_data = json.load(f)

        docs = extract_documents(json_data)
        if not docs:
            raise ValueError("JSON does not contain 'defectList' or 'elements' entries.")

        if not self.vector_store:
            self.vector_store = Chroma.from_documents(
                documents=docs,
                embedding=self.embedding,
                persist_directory=self.db_path,
                client_settings=self._chroma_settings()
            )
        else:
            self.vector_store.add_documents(docs)

        self._log_uploaded_file(os.path.basename(json_path))
        self._load_vector_store()

    # --- Uploaded files log ---
    def _log_uploaded_file(self, file_name: str):
        os.makedirs(self.db_path, exist_ok=True)
        with open(UPLOADED_FILES_LOG, 'a+') as f:
            f.seek(0)
            files = f.read().splitlines()
            if file_name not in files:
                f.write(file_name + '\n')

    def list_uploaded_files(self) -> List[str]:
        if not os.path.exists(UPLOADED_FILES_LOG):
            return []
        with open(UPLOADED_FILES_LOG, 'r') as f:
            return f.read().splitlines()

    # --- Delete all data ---
    def delete_all_data(self):
        self.clear()
        time.sleep(0.5)
        gc.collect()
        if os.path.exists(self.db_path):
            try:
                shutil.rmtree(self.db_path, onerror=self._handle_remove_readonly)
            except Exception as e:
                print(f"Error deleting DB folder: {e}")

    def _handle_remove_readonly(self, func, path, exc):
        os.chmod(path, stat.S_IWRITE)
        func(path)

    def clear(self):
        self.vector_store = None
        self.retriever = None
        self.chain = None

    # --- Ask method ---
    def ask(self, query: str) -> str:
        if not self.chain:
            return "Please, add a PDF or JSON document first."

        # Get model response
        response = self.chain.invoke(query)

        # --- Post-process (Cleaning Only) ---
        import re

        # Remove line breaks and multiple spaces
        # NOTE: Keep the .strip() to clean up leading/trailing whitespace
        response = re.sub(r'\s+', ' ', response.strip())

        # Remove bullet-like characters (if the model ignores the "no lists" rule)
        response = re.sub(r'[-•–]', '', response)

        # Since we trust the LLM's full answer now, we return the cleaned response.
        return response.strip()

