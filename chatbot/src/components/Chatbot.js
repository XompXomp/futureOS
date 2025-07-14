import React, { useState, useEffect, useRef } from "react";
import { createConversationEntry, updateConversationEntry, initializePatientProfile } from "../utils/localdb";

export default function Chatbot() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [tags] = useState([]); // You can add logic to set tags if needed
  const messagesEndRef = useRef(null);

  // On mount, create a new conversation entry and initialize patient profile
  useEffect(() => {
    const setup = async () => {
      await initializePatientProfile();
      const entry = {
        timestamp: new Date().toISOString(),
        tags: [],
        messages: [],
      };
      const id = await createConversationEntry(entry);
      setConversationId(id);
      setMessages([]);
    };
    setup();
  }, []);

  // Scroll to bottom on new message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Real AI response from backend
  async function getAIResponse(userText) {
    try {
      const res = await fetch("http://localhost:5000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userText }),
      });
      const data = await res.json();
      if (data.response) return data.response;
      return "Sorry, I couldn't get a response from the AI.";
    } catch (e) {
      return "Error: Could not connect to AI backend.";
    }
  }

  async function handleSend(e) {
    e.preventDefault();
    if (!input.trim() || conversationId == null) return;
    const userMsg = { sender: "user", text: input };
    setMessages((prev) => [...prev, { ...userMsg, timestamp: new Date().toISOString() }]);
    setLoading(true);
    const aiText = await getAIResponse(input);
    setLoading(false);
    const aiMsg = { sender: "AI", text: aiText };
    // Update messages in memory
    setMessages((prev) => {
      const updated = [...prev, { ...aiMsg, timestamp: new Date().toISOString() }];
      // Update conversation entry in IndexedDB
      updateConversationEntry(conversationId, {
        timestamp: updated[0]?.timestamp || new Date().toISOString(),
        tags,
        messages: updated.map(({ sender, text }) => ({ sender, text })),
      });
      return updated;
    });
    setInput("");
  }

  return (
    <div style={{ maxWidth: 400, margin: "40px auto", border: "1px solid #ccc", borderRadius: 8, padding: 16, background: "#fff" }}>
      <h2 style={{ textAlign: "center" }}>careAI Chatbot</h2>
      <div style={{ height: 300, overflowY: "auto", background: "#f9f9f9", padding: 8, borderRadius: 4, marginBottom: 8 }}>
        {messages.map((msg, idx) => (
          <div key={idx} style={{ textAlign: msg.sender === "user" ? "right" : "left", margin: "8px 0" }}>
            <span style={{ display: "inline-block", padding: "8px 12px", borderRadius: 16, background: msg.sender === "user" ? "#d1e7dd" : "#e2e3e5" }}>
              <b>{msg.sender === "user" ? "You" : "AI"}:</b> {msg.text}
            </span>
          </div>
        ))}
        {loading && (
          <div style={{ textAlign: "left", margin: "8px 0" }}>
            <span style={{ display: "inline-block", padding: "8px 12px", borderRadius: 16, background: "#e2e3e5" }}>
              <b>AI:</b> ...
            </span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <form onSubmit={handleSend} style={{ display: "flex", gap: 8 }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          style={{ flex: 1, padding: 8, borderRadius: 4, border: "1px solid #ccc" }}
          disabled={loading}
        />
        <button type="submit" style={{ padding: "8px 16px", borderRadius: 4, border: "none", background: "#0d6efd", color: "#fff" }} disabled={loading}>
          Send
        </button>
      </form>
      <div style={{ fontSize: 12, color: "#888", marginTop: 8, textAlign: "center" }}>
        All messages in this session are stored as a single entry (IndexedDB). View in Chrome DevTools → Application → IndexedDB.
      </div>
    </div>
  );
} 