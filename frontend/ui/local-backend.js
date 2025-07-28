const express = require('express');
const cors = require('cors');
const app = express();
const PORT = 8002;

app.use(cors());
app.use(express.json());

// In-memory store for demonstration (replace with IPC or polling for real IndexedDB data)
let memory = { id: 'memory', episodes: [], procedural: {}, semantic: [] };
let links = { id: 'links', links: [] };
let general = { id: 'general', general: {} };
let conversation = { cid: 'conv-001', tags: [], conversation: [] };
let updates = [
  {
    datetime: "2023-04-02T13:00:00",
    text: "Panadol added to medications"
  }
];

app.post('/api/llama-bridge', (req, res) => {
  const body = req.body;
  // Handle data requests
  if (body.request_type) {
    if (body.request_type === 'updates') {
      return res.json({ updates });
    }
    if (body.request_type === 'memory_links') {
      return res.json({ memory, links });
    }
    if (body.request_type === 'convo_general_insights') {
      return res.json({ conversation, general });
    }
    return res.status(400).json({ error: 'Unknown request_type' });
  }
  // Handle data updates
  if (body.tag && body.data) {
    if (body.tag === 'recommendations_and_treatment_insights') {
      // Update recommendations/treatment insights (define logic)
      updates = { ...updates, ...body.data };
      return res.json({ status: 'ok' });
    }
    if (body.tag === 'links_and_function_call') {
      links = { ...links, ...body.data };
      return res.json({ status: 'ok' });
    }
    if (body.tag === 'updated_general_insights') {
      general = { ...general, ...body.data };
      return res.json({ status: 'ok' });
    }
    return res.status(400).json({ error: 'Unknown tag' });
  }
  return res.status(400).json({ error: 'Invalid request' });
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Local backend listening at http://0.0.0.0:${PORT}`);
}); 