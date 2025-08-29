# main.py
import os
import tempfile
import shutil
import subprocess
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="iFixDocs Backend")

# Allowed origins (your frontend URLs)
origins = [
    "http://localhost:5173",  # Vite dev server (React)
    "http://127.0.0.1:5173",  # Sometimes browser resolves this way
    # "https://yourfrontenddomain.com",  # Add production domain later
]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,        # who can talk to backend
    allow_credentials=True,
    allow_methods=["*"],          # allow all HTTP methods (GET, POST, PUT, DELETE)
    allow_headers=["*"],          # allow all headers
)

#Fastapi must return json format de, cannot plain string
@app.get("/")
def root():
    return {"message": "Hello! iFixDocs backend is running."}

class RepoURL(BaseModel):
    repo_url: str

@app.post("/generate-docs/")
def generate_docs(data: RepoURL):
    try:
        # temp dir for cloning
        temp_dir = tempfile.mkdtemp()
        repo_name = data.repo_url.split("/")[-1].replace(".git", "")
        repo_path = os.path.join(temp_dir, repo_name)

        # clone repo
        subprocess.run(["git", "clone", data.repo_url, repo_path], check=True)

        # path for docs
        docs_path = os.path.join(repo_path, "docs")
        os.makedirs(docs_path, exist_ok=True)

        # generate a starter README for each Python file
        docs_summary = []
        for root, _, files in os.walk(repo_path):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    with open(file_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()

                    # get first few lines (docstring or comments)
                    doc_content = ""
                    for line in lines[:20]:
                        if line.strip().startswith("#") or line.strip().startswith('"""'):
                            doc_content += line.strip() + "\n"

                    if not doc_content:
                        doc_content = f"Documentation placeholder for {file}"

                    output_file = os.path.join(docs_path, f"{file}.md")
                    with open(output_file, "w", encoding="utf-8") as f:
                        f.write(f"# Documentation for {file}\n\n{doc_content}")

                    docs_summary.append(file)
        
        docs_content = {}
        for file in docs_summary:
            md_path = os.path.join(docs_path, f"{file}.md")
            with open(md_path, "r", encoding="utf-8") as f:
                docs_content[file] = f.read()

        return {"status": "success", "docs": docs_content}        

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


