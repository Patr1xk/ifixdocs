# main.py (enhanced with edit endpoint)
import os
import tempfile
import shutil
import subprocess
import re
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="iFixDocs Backend")

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "iFixDocs backend is running."}

class RepoURL(BaseModel):
    repo_url: str

class EditDoc(BaseModel):
    file_name: str
    updated_content: str

# Helper function for extracting code info
def extract_code_info(file_path: str):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    func_class_docs = {}
    pre_comment_buffer = []
    current_name = None

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            pre_comment_buffer.append(stripped.lstrip("# ").strip())
            continue

        func_match = re.match(r"def\s+(\w+)\(.*\):", stripped)
        class_match = re.match(r"class\s+(\w+)\(?.*?\):", stripped)

        if func_match or class_match:
            current_name = func_match.group(1) if func_match else class_match.group(1)
            inline_comment = ""
            if "#" in line:
                inline_comment = line.split("#", 1)[1].strip()

            comments = pre_comment_buffer.copy()
            if inline_comment:
                comments.append(inline_comment)
            if not comments:
                comments = ["No comments found"]

            func_class_docs[current_name] = comments
            pre_comment_buffer = []
            continue

        if current_name and "#" in line:
            comment_inside = line.split("#", 1)[1].strip()
            if comment_inside:
                func_class_docs.setdefault(current_name, []).append(comment_inside)

    all_content = "".join(lines)
    classes = [k for k in func_class_docs.keys() if k in re.findall(r"class\s+(\w+)", all_content)]
    funcs = [k for k in func_class_docs.keys() if k not in classes]

    return func_class_docs, classes, funcs

# Endpoint: generate starter docs
@app.post("/generate-docs/")
def generate_docs(data: RepoURL):
    try:
        temp_dir = tempfile.mkdtemp()
        repo_name = data.repo_url.split("/")[-1].replace(".git", "")
        repo_path = os.path.join(temp_dir, repo_name)

        subprocess.run(["git", "clone", data.repo_url, repo_path], check=True)

        docs_path = os.path.join(repo_path, "docs")
        os.makedirs(docs_path, exist_ok=True)

        docs_summary = []

        for root_dir, _, files in os.walk(repo_path):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root_dir, file)
                    func_class_docs, classes, funcs = extract_code_info(file_path)

                    class_section = "## Classes\n" + ("\n".join([f"- {c}" for c in classes]) if classes else "- None") + "\n\n"
                    func_section = "## Functions\n" + ("\n".join([f"- {f}" for f in funcs]) if funcs else "- None") + "\n\n"

                    comments_section = "## Comments per Function/Class\n"
                    for name, comments in func_class_docs.items():
                        comments_section += f"### {name}\n"
                        for c in comments:
                            comments_section += f"- {c}\n"
                        comments_section += "\n"

                    try:
                        result = subprocess.run(
                            ["git", "-C", repo_path, "log", "--pretty=format:%h - %s", "--", file],
                            capture_output=True,
                            text=True,
                            check=True
                        )
                        git_log = result.stdout.strip() or "No commits found"
                    except Exception:
                        git_log = "Git log unavailable"

                    doc_content = (
                        f"# Documentation for {file}\n\n"
                        f"{class_section}"
                        f"{func_section}"
                        f"{comments_section}"
                        f"## Git Commits\n{git_log}\n\n"
                        "_Description placeholders: add details for each function/class here._\n"
                    )

                    output_file = os.path.join(docs_path, f"{file}.md")
                    with open(output_file, "w", encoding="utf-8") as f:
                        f.write(doc_content)

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

# Endpoint: save edited docs
@app.post("/edit-doc/")
def edit_doc(data: EditDoc):
    try:
        # For prototype: just save edited content in a temp folder
        temp_dir = tempfile.mkdtemp()
        docs_path = os.path.join(temp_dir, "docs")
        os.makedirs(docs_path, exist_ok=True)

        file_path = os.path.join(docs_path, data.file_name)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(data.updated_content)

        # Return success
        return {"status": "success", "file": data.file_name, "content": data.updated_content}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
