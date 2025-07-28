const express = require('express');
const cors = require('cors');
const app = express();
const PORT = 8002;

app.use(cors());
app.use(express.json());

// Sample data for demonstration
let updates = [
  { datetime: '03_07_25_10_30', text: 'Panadol removed from medications' },
  { datetime: '03_07_25_11_45', text: 'Ibuprofen added to medications' }
];

let memory = [
  { datetime: '01_07_25_09_00', text: "Patient said they can't sleep" },
  { datetime: '02_07_25_22_15', text: 'Wakes up multiple times' }
];

let links = {
  Sleep: {
    'disturbed sleep': 0.6,
    'tired in morning': 0.3
  }
};

let conversation = [
  {
    cid: 1,
    user: "I haven't been sleeping well",
    AI: "Tell me more about that",
    Tag: "Sleep",
    Datetime: "2024-06-01T08:00:00"
  }
];

let general = {
  EmotionalCues: ["anxious", "tired"],
  Tone: "reflective",
  Engagement: "high",
  Hesitation: "minimal",
  NuancedFindings: ["User shows progress in managing stress"]
};

// GET /updates
app.get('/updates', (req, res) => {
  res.json(updates);
});

// GET /memory-links
app.get('/memory-links', (req, res) => {
  res.json({ memory, links });
});

// GET /conversations-insights
app.get('/conversations-insights', (req, res) => {
  res.json({ conversations: conversation, previous_insights: general });
});

// POST /recommendations-treatment
app.post('/recommendations-treatment', (req, res) => {
  // In a real app, update patient profile here
  console.log('Received recommendations/treatment:', req.body);
  res.json({ status: 'ok' });
});

// POST /links-function-call
app.post('/links-function-call', (req, res) => {
  // In a real app, update links here
  console.log('Received links/function call:', req.body);
  res.json({ status: 'ok' });
});

// POST /general-insights
app.post('/general-insights', (req, res) => {
  // In a real app, update general insights here
  console.log('Received general insights:', req.body);
  res.json({ status: 'ok' });
});

// Healthcare LLM Update Endpoints
app.post('/api/healthcare-updates', (req, res) => {
  const { type, data } = req.body;
  console.log(`Received healthcare update - type: ${type}, data:`, data);
  
  switch (type) {
    case 'recommendations':
      // Update patient profile recommendations
      console.log('Updating patient profile recommendations:', data);
      // In a real implementation, this would update the frontend's IndexedDB
      // For now, we'll just log it
      break;
      
    case 'links':
      // Update links
      console.log('Updating links:', data);
      links = { ...links, ...data };
      break;
      
    case 'general':
      // Update general insights
      console.log('Updating general insights:', data);
      general = { ...general, ...data };
      break;
      
    default:
      console.log('Unknown update type:', type);
  }
  
  res.json({ status: 'ok', message: `Updated ${type}` });
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Local backend listening at http://0.0.0.0:${PORT}`);
}); 