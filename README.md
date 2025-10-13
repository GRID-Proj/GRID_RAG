# ChatPDF Application: Step-by-Step Installation Guide

ChatPDF is a **locally hosted** application that enables users to interactively query the contents of PDF documents. It leverages **Retrieval-Augmented Generation (RAG)** technology to generate context-aware answers using only the information found in the uploaded PDFs. ChatPDF provides a simple, user-friendly web interface for document ingestion and question answering, powered entirely by local resources—**no internet-based APIs are required after setup**.

---

## 🔧 Technologies Used

- **Streamlit** – For building the graphical web interface  
- **LangChain** – Manages interaction between LLMs, embeddings, and retrieval  
- **ChromaDB** – Local vector database for storing and retrieving document chunks  
- **Ollama** – Hosts Large Language Models (LLMs) like Mistral locally

---

## 1. System Requirements

- **Operating System**: Windows 10/11, macOS, or Linux  
- **Python**: Version 3.10 or higher  
- **Memory (RAM)**: Minimum 4 GB  
- **Storage**: At least 5 GB available disk space  
- **Internet**: Only required for setup (to install packages and download the model)

> 💡 **How to open Command Prompt / Terminal:**
> - **Windows**: Press `Windows + R`, type `cmd`, and press Enter  
> - **macOS**: Use Spotlight (`Cmd + Space`) and search for "Terminal"  
> - **Linux**: Open the Terminal from your application menu or press `Ctrl + Alt + T`

---

## 2. Project Folder Structure

```
ChatPDF_Project/
├── main.py           # Application backend
├── app.py            # Streamlit frontend
├── requirements.txt  # Python dependencies
└── vectorstores/     # Auto-generated when app runs
```

---

## 3. Installation Procedure

### 3.1. Install Python 3.10+

1. Download from: [python.org/downloads](https://www.python.org/downloads/)
2. During installation, **check the box** for "Add Python to PATH"
3. Verify installation:
   ```bash
   python --version
   ```
   It should return `Python 3.10` or higher.

---

### 3.2. Set Up a Virtual Environment (Recommended)

In your project folder:

```bash
# Create a virtual environment
python -m venv venv

# Activate the environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

> 💡 You should see `(venv)` appear before your prompt, meaning the virtual environment is active.

---

### 3.3. Install Project Dependencies

Create a file named `requirements.txt` with the following content:

```text
streamlit
streamlit-chat
langchain
langchain-community
langchain-ollama
langchain-chroma
chromadb
pypdf
jq
```

Then install:

```bash
pip install -r requirements.txt
```

---

### 3.4. Install Ollama and Run the Mistral Model

1. Download and install from [ollama.com/download](https://ollama.com/download)  
2. Then run:
   ```bash
   ollama run deepseek-r1:1.5b
   ollama run nomic-embed-text
   ```
   This will download (~1.4 GB) and start the Mistral model locally.

---

### 3.5. Add the Application Code

Ensure your folder has these two files with the following content:

- `main.py` – [Full backend logic]
- `app.py` – [Streamlit frontend interface]

> 📁 Make sure these are in the same directory as your `requirements.txt`.

---

## 4. Running the Application

From the project directory (and with the virtual environment activated):

```bash
streamlit run app.py
```

Your browser will open automatically or show a local link (e.g., http://localhost:8501).

---

## 5. Using the Application

1. Click **Upload PDFs** to ingest your documents  
2. Type a question and click **Send**  
3. View document-aware answers in the chat  
4. Use **🗑️ Delete All Data** to reset and clear vector memory

---
## 🔄 What's New in v2.1.0

- ✅ **General JSON Support**: Ingest both `defectList[]` (e.g., MRT damage logs) and `category[].elements[]` (e.g., masonry catalog).
- ✅ **Prompt Improvements**: Short, clear, paragraph-only answers. Avoids repetition, bullets, and numbering.
- ✅ **Flexible Retrieval**: Loosened similarity threshold for better JSON matching.
- ✅ **Cleaner UI Flow**: Auto-detection of PDF vs. JSON during upload; graceful error handling.
- ✅ **Automatic Truncation**: Ensures concise 3-sentence answers even if the model overruns.
---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
