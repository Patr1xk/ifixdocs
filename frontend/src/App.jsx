// App.jsx
import { useState, useEffect } from "react";
import axios from "axios";

export default function App() {
  const [repoUrl, setRepoUrl] = useState("");
  const [files, setFiles] = useState([]); // List of Python files
  const [selectedFile, setSelectedFile] = useState("");
  const [docContent, setDocContent] = useState("");

  const [templates, setTemplates] = useState([]); // list of template names
  const [selectedTemplate, setSelectedTemplate] = useState("");
  const [templateContent, setTemplateContent] = useState("");

  const [loading, setLoading] = useState(false);

  // Fetch template list from backend when app loads
  useEffect(() => {
    axios
      .get("http://localhost:8000/templates")
      .then((res) => {
        setTemplates(res.data.templates);
      })
      .catch((err) => console.error("Failed to load templates:", err));
  }, []);

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

  // Handle template selection (fetch content from backend)
  const handleTemplateSelect = async (e) => {
    const name = e.target.value;
    setSelectedTemplate(name);
    if (!name) return;
    try {
      const res = await axios.get(`http://localhost:8000/templates/${name}`);
      setTemplateContent(res.data.content);
    } catch (err) {
      console.error("Failed to load template:", err);
    }
  };

// Insert template by asking backend
const insertTemplate = () => {
  if (!selectedTemplate) return alert("Select a template first");
  if (!templateContent) return alert("Template content not loaded yet");

  const textarea = document.querySelector("textarea");
  if (!textarea) return;

  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;

  const before = docContent.substring(0, start);
  const after = docContent.substring(end);

  // Insert template where cursor is
  const updated = before + "\n" + templateContent + "\n" + after;

  setDocContent(updated);

  // Restore cursor position after inserted template
  setTimeout(() => {
    textarea.selectionStart = textarea.selectionEnd = start + templateContent.length + 2;
    textarea.focus();
  }, 0);
};

  // Save edited content to backend
  const saveDoc = async () => {
    if (!selectedFile) return alert("Select a file first");
    try {
      await axios.post("http://localhost:8000/edit-doc/", {
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

      {/* Repo Input */}
      <div>
        <input
          type="text"
          placeholder="Paste GitHub repo URL"
          value={repoUrl}
          onChange={(e) => setRepoUrl(e.target.value)}
          style={{ width: "400px" }}
        />
        <button
          onClick={fetchDocs}
          disabled={loading}
          style={{ marginLeft: "10px" }}
        >
          {loading ? "Fetching..." : "Fetch Docs"}
        </button>
      </div>

      {/* File Selector */}
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

      {/* Template Selector */}
      {templates.length > 0 && (
        <div style={{ marginTop: "20px" }}>
          <label>
            Select Template:{" "}
            <select value={selectedTemplate} onChange={handleTemplateSelect}>
              <option value="">-- Choose a Template --</option>
              {templates.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </label>
        </div>
      )}

      {/* Editor + Actions */}
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
            style={{
              display: "block",
              marginTop: "10px",
              fontFamily: "monospace",
            }}
          />
        </div>
      )}
    </div>
  );
}
