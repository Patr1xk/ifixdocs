# main.py
import os
import tempfile
import shutil
import subprocess
import re
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="iFixDocs Backend")

# Allowed origins (your frontend URLs)
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      
    allow_credentials=True,
    allow_methods=["*"],        
    allow_headers=["*"],        
)

@app.get("/")
def root():
    return {"message": "Hello! iFixDocs backend is running."}

class RepoURL(BaseModel):
    repo_url: str

@app.post("/generate-docs/")
def generate_docs(data: RepoURL):
    try:
        # Temporary dir for cloning
        temp_dir = tempfile.mkdtemp()
        repo_name = data.repo_url.split("/")[-1].replace(".git", "")
        repo_path = os.path.join(temp_dir, repo_name)

        # Clone repo
        subprocess.run(["git", "clone", data.repo_url, repo_path], check=True)

        # Path for docs
        docs_path = os.path.join(repo_path, "docs")
        os.makedirs(docs_path, exist_ok=True)

        docs_summary = []

        for root_dir, _, files in os.walk(repo_path):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root_dir, file)
                    with open(file_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        content = "".join(lines)

                    # Extract classes
                    classes = re.findall(r"class\s+(\w+)\(?.*?\):", content)
                    if classes:
                        class_section = "## Classes\n" + "\n".join([f"- {c}" for c in classes]) + "\n\n"
                    else:
                        class_section = "## Classes\n- None\n\n"

                    # Extract functions
                    funcs = re.findall(r"def\s+(\w+)\(.*\):", content)
                    if funcs:
                        func_section = "## Functions\n" + "\n".join([f"- {fn}" for fn in funcs]) + "\n\n"
                    else:
                        func_section = "## Functions\n- None\n\n"

                    # Combine into doc content
                    doc_content = f"# Documentation for {file}\n\n" + class_section + func_section
                    doc_content += "_Description placeholders: add details for each function/class here._\n"

                    # Save to docs folder
                    output_file = os.path.join(docs_path, f"{file}.md")
                    with open(output_file, "w", encoding="utf-8") as f:
                        f.write(doc_content)

                    docs_summary.append(file)

        # Return content in JSON for frontend preview
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
