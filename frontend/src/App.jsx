import { useEffect, useState } from "react";

function App() {
  const [msg, setMsg] = useState("");

  useEffect(() => {
    fetch("http://127.0.0.1:8000/")   // calling FastAPI
      .then(res => res.json())
      .then(data => {
        console.log(data);
        setMsg(data.message);   // grab "message" field
      })
      .catch(err => console.error("Error fetching:", err));
  }, []);

  return (
    <div>
      <h1>Frontend Connected ✅</h1>
      <p>Backend says: {msg}</p>
    </div>
  );
}

export default App;
