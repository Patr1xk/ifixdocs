// App.jsx
import { useState } from "react";
import axios from "axios";

export default function App() {
  const [repoUrl, setRepoUrl] = useState("");
  const [files, setFiles] = useState([]); // List of Python files
  const [selectedFile, setSelectedFile] = useState("");
  const [docContent, setDocContent] = useState("");
  const [template, setTemplate] = useState(
    "\n## Description Template\n- Function/Class Purpose: \n- Inputs: \n- Outputs: \n- Notes: \n"
  );
  const [loading, setLoading] = useState(false);

  // Fetch starter docs from backend
  const fetchDocs = async () => {
    if (!repoUrl) return alert("Enter GitHub repo URL");
    try {
      setLoading(true);
      const res = await axios.post("http://localhost:8000/generate-docs/", {
        repo_url: repoUrl,
      });
      const docs = res.data.docs;
      const fileNames = Object.keys(docs);
      setFiles(fileNames);
      if (fileNames.length > 0) {
        setSelectedFile(fileNames[0]);
        setDocContent(docs[fileNames[0]]);
      }
    } catch (err) {
      console.error(err);
      alert("Failed to fetch docs");
    } finally {
      setLoading(false);
    }
  };

  // Handle file selection change
  const handleFileSelect = (e) => {
    const file = e.target.value;
    setSelectedFile(file);
    setDocContent(""); // reset
    axios
      .post("http://localhost:8000/generate-docs/", { repo_url: repoUrl })
      .then((res) => {
        const docs = res.data.docs;
        setDocContent(docs[file] || "");
      })
      .catch((err) => console.error(err));
  };

  // Insert template into current doc content
  const insertTemplate = () => {
    setDocContent(docContent + template);
  };

  // Save edited content to backend
  const saveDoc = async () => {
    if (!selectedFile) return alert("Select a file first");
    try {
      const res = await axios.post("http://localhost:8000/edit-doc/", {
        file_name: selectedFile,
        updated_content: docContent,
      });
      alert("Saved successfully!");
    } catch (err) {
      console.error(err);
      alert("Failed to save doc");
    }
  };

  return (
    <div style={{ padding: "20px", fontFamily: "Arial" }}>
      <h1>iFixDocs Prototype</h1>

      <div>
        <input
          type="text"
          placeholder="Paste GitHub repo URL"
          value={repoUrl}
          onChange={(e) => setRepoUrl(e.target.value)}
          style={{ width: "400px" }}
        />
        <button onClick={fetchDocs} disabled={loading} style={{ marginLeft: "10px" }}>
          {loading ? "Fetching..." : "Fetch Docs"}
        </button>
      </div>

      {files.length > 0 && (
        <div style={{ marginTop: "20px" }}>
          <label>
            Select File:{" "}
            <select value={selectedFile} onChange={handleFileSelect}>
              {files.map((f) => (
                <option key={f} value={f}>
                  {f}
                </option>
              ))}
            </select>
          </label>
        </div>
      )}

      {selectedFile && (
        <div style={{ marginTop: "20px" }}>
          <button onClick={insertTemplate}>Insert Template</button>
          <button onClick={saveDoc} style={{ marginLeft: "10px" }}>
            Save Edits
          </button>

          <textarea
            value={docContent}
            onChange={(e) => setDocContent(e.target.value)}
            rows={20}
            cols={100}
            style={{ display: "block", marginTop: "10px", fontFamily: "monospace" }}
          />
        </div>
      )}
    </div>
  );
}
