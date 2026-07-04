import { useState } from "react";
import CheckView from "./components/CheckView.jsx";
import FeedView from "./components/FeedView.jsx";

export default function App() {
  const [tab, setTab] = useState("check");
  return (
    <div className="app">
      <div className="header">
        <div className="brand">
          <span className="logo">🛡️</span>
          <div>
            <h1>Antibody</h1>
            <p>your community shield against scams</p>
          </div>
        </div>
        <div className="tabs">
          <button className={`tab ${tab === "check" ? "active" : ""}`} onClick={() => setTab("check")}>
            Check a message
          </button>
          <button className={`tab ${tab === "feed" ? "active" : ""}`} onClick={() => setTab("feed")}>
            What's going around
          </button>
        </div>
      </div>

      {tab === "check" ? <CheckView /> : <FeedView />}

      <div className="footer">
        Got something suspicious? Check it here — and if it was a scam, tell us.<br />
        Every report helps protect the next person. Powered by <b>Cognee</b> memory · matched by meaning, not just keywords.
      </div>
    </div>
  );
}
