const express = require('express');
const cors = require('cors');
const app = express();
const PORT = 8002;

// Import shared data directly
const {
  sharedPatientProfile,
  sharedMemory,
  sharedLinks,
  sharedGeneral,
  sharedUpdates,
  sharedConversation
} = require('./shared-data.js');

app.use(cors());
app.use(express.json());

// Use shared data directly - no more HTTP requests needed!
let patientProfile = { ...sharedPatientProfile };
let memory = { ...sharedMemory };
let links = { ...sharedLinks };
let general = { ...sharedGeneral };
let updates = { ...sharedUpdates };
let conversation = { ...sharedConversation };

// GET /updates - returns current data (not template data)
app.get('/updates', (req, res) => {
  res.json(updates.updates);
});

// GET /memory-links - returns current data (not template data)
app.get('/memory-links', (req, res) => {
  res.json({
    memory: memory.memory,
    links: links.links
  });
});

// GET /conversations-insights - returns current data (not template data)
app.get('/conversations-insights', (req, res) => {
  res.json({
    conversations: conversation.conversation,
    previous_insights: general.general
  });
});

// POST /recommendations-treatment
app.post('/recommendations-treatment', (req, res) => {
  console.log('Received recommendations/treatment:', req.body);
  
  // Update the local data directly
  if (req.body && req.body.treatment) {
    patientProfile.treatment = req.body.treatment;
  }
  
  res.json({ status: 'ok', message: 'Updated locally' });
});

// POST /links-function-call
app.post('/links-function-call', (req, res) => {
  console.log('Received links/function call:', req.body);
  
  // Update the local data directly
  if (req.body && req.body.links) {
    links.links = { ...links.links, ...req.body.links };
  }
  
  res.json({ status: 'ok', message: 'Updated locally' });
});

// POST /general-insights
app.post('/general-insights', (req, res) => {
  console.log('Received general insights:', req.body);
  
  // Update the local data directly
  if (req.body && req.body.general) {
    general.general = { ...general.general, ...req.body.general };
  }
  
  res.json({ status: 'ok', message: 'Updated locally' });
});

// Healthcare LLM Update Endpoints
app.post('/api/healthcare-updates', (req, res) => {
  const { type, data } = req.body;
  console.log(`Received healthcare update - type: ${type}, data:`, data);
  
  try {
    switch (type) {
      case 'recommendations':
        // Update recommendations directly
        if (patientProfile.treatment && patientProfile.treatment.length > 0) {
          patientProfile.treatment[0].recommendations = Array.isArray(data) ? data : [data];
          console.log('Updated patient profile recommendations:', patientProfile.treatment[0].recommendations);
        }
        sendUpdateToFrontend('patientProfile', patientProfile);
        break;
        
      case 'links':
        // Update links directly
        console.log('[DEBUG] Received links data:', data);
        console.log('[DEBUG] Current links.links before update:', links.links);
        
        // Check if this is a combined update with both links and Function
        if (data.links && data.Function) {
          console.log('[DEBUG] Detected combined links and function update');
          links.links = { ...links.links, ...data.links };
          console.log('[DEBUG] Updated links.links:', links.links);
          // Send both updates to frontend
          sendMultipleUpdatesToFrontend([
            { type: 'links', data: links.links },
            { type: 'function', data: data.Function }
          ]);
        } else {
          // Regular links update
          links.links = { ...links.links, ...data };
          console.log('[DEBUG] Updated links.links:', links.links);
          sendUpdateToFrontend('links', links.links);
        }
        break;
        
      case 'general':
        // Update general directly
        general.general = { ...general.general, ...data };
        
        // Handle trend_analysis specifically if it exists in the data
        if (data && data.trend_analysis) {
          general.general.trend_analysis = data.trend_analysis;
          console.log('Updated trend analysis:', data.trend_analysis);
        }
        
        console.log('Updated general:', general.general);
        sendUpdateToFrontend('general', general.general);
        break;
        
      case 'trend_analysis':
        // Handle trend_analysis as a separate update type
        general.general.trend_analysis = data;
        console.log('Updated trend analysis:', data);
        sendUpdateToFrontend('general', general.general);
        break;
        
      case 'function':
        // Handle function calls (e.g., ProactiveAdd)
        console.log('Received function call:', data);
        sendUpdateToFrontend('function', data);
        break;
        
      case 'links_and_function':
        // Handle case where both links and function come together
        console.log('[DEBUG] Received combined links and function update:', data);
        if (data.links) {
          // Update links first
          links.links = { ...links.links, ...data.links };
          console.log('[DEBUG] Updated links.links:', links.links);
        }
        if (data.Function) {
          // Send both updates to frontend
          sendMultipleUpdatesToFrontend([
            { type: 'links', data: links.links },
            { type: 'function', data: data.Function }
          ]);
        } else {
          sendUpdateToFrontend('links', links.links);
        }
        break;
        
      default:
        console.log('Unknown update type:', type);
    }
    
    res.json({ status: 'ok', message: `Updated ${type}` });
  } catch (error) {
    console.error('Error processing healthcare update:', error);
    res.status(500).json({ error: 'Failed to process update' });
  }
});

// Function to send updates to frontend
function sendUpdateToFrontend(type, data) {
  console.log(`[DEBUG] Sending ${type} update to frontend:`, data);
  
  // Store the latest update for the frontend to fetch
  global.latestUpdate = {
    type: type,
    data: data,
    timestamp: Date.now()
  };
  console.log(`[DEBUG] Stored latestUpdate:`, global.latestUpdate);
}

// Function to send multiple updates to frontend (for when both links and function come together)
function sendMultipleUpdatesToFrontend(updates) {
  console.log(`[DEBUG] Sending multiple updates to frontend:`, updates);
  
  // Store multiple updates for the frontend to fetch
  global.latestUpdates = updates.map(update => ({
    type: update.type,
    data: update.data,
    timestamp: Date.now()
  }));
  console.log(`[DEBUG] Stored latestUpdates:`, global.latestUpdates);
}

// Endpoint for frontend to get latest updates
app.get('/api/latest-update', (req, res) => {
  console.log('[DEBUG] Frontend requested latest update, global.latestUpdate:', global.latestUpdate, 'global.latestUpdates:', global.latestUpdates);
  
  // Check for multiple updates first
  if (global.latestUpdates && global.latestUpdates.length > 0) {
    const update = global.latestUpdates.shift();
    console.log('[DEBUG] Sending update from latestUpdates to frontend:', update);
    res.json(update);
    // Clear the array if it's empty
    if (global.latestUpdates.length === 0) {
      global.latestUpdates = null;
    }
  } else if (global.latestUpdate) {
    console.log('[DEBUG] Sending update to frontend:', global.latestUpdate);
    res.json(global.latestUpdate);
    // Clear the update after sending
    global.latestUpdate = null;
  } else {
    console.log('[DEBUG] No updates available, sending no-updates status');
    res.json({ status: 'no-updates' });
  }
});

// Endpoint to get current patient profile
app.get('/api/patient-profile', (req, res) => {
  res.json(patientProfile);
});

// Endpoint to sync data from React app
app.post('/api/sync-from-frontend', (req, res) => {
  const { patientProfile: newProfile, memory: newMemory, links: newLinks, general: newGeneral, updates: newUpdates } = req.body;
  
  if (newProfile) {
    patientProfile = newProfile;
    console.log('Synced patient profile from frontend:', patientProfile);
  }
  if (newMemory) {
    memory = newMemory;
    console.log('Synced memory from frontend');
  }
  if (newLinks) {
    links = newLinks;
    console.log('Synced links from frontend');
  }
  if (newGeneral) {
    general = newGeneral;
    console.log('Synced general from frontend');
  }
  if (newUpdates) {
    updates = newUpdates;
    console.log('Synced updates from frontend');
  }
  
  res.json({ status: 'ok', message: 'Data synced from frontend' });
});

// Endpoint to update patient profile directly
app.post('/api/patient-profile', (req, res) => {
  const newProfile = req.body;
  console.log('Updating patient profile:', newProfile);
  
  if (newProfile && typeof newProfile === 'object') {
    patientProfile = { ...patientProfile, ...newProfile };
    
    // Ensure treatment array structure is maintained
    if (newProfile.treatment && Array.isArray(newProfile.treatment)) {
      patientProfile.treatment = newProfile.treatment;
    }
    
    console.log('Updated patient profile:', patientProfile);
    sendUpdateToFrontend('patientProfile', patientProfile);
    res.json({ status: 'ok', message: 'Patient profile updated' });
  } else {
    res.status(400).json({ error: 'Invalid patient profile data' });
  }
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Local backend listening at http://0.0.0.0:${PORT}`);
  console.log('Local backend now uses shared data directly - no HTTP requests needed!');
  console.log('Data is synchronized with the React app via shared-data.js');
}); 