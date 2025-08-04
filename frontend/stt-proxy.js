const WebSocket = require('ws');
const http = require('http');

// Create WebSocket server
const wss = new WebSocket.Server({ port: 8080 });

console.log('STT Proxy Server running on ws://localhost:8080');

wss.on('connection', (ws) => {
  console.log('Client connected to proxy');
  
  // Connect to STT server with authentication headers
  const sttWs = new WebSocket('ws://localhost:11004/api/asr-streaming', {
    headers: {
      'kyutai-api-key': 'public_token'
    }
  });
  
  sttWs.on('open', () => {
    console.log('Connected to STT server');
    console.log('Number of clients connected:', wss.clients.size);
  });
  
  sttWs.on('message', (data) => {
    // Forward STT responses to client
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(data);
    }
  });
  
  sttWs.on('error', (error) => {
    console.error('STT server error:', error);
    ws.close();
  });
  
  sttWs.on('close', () => {
    console.log('STT server connection closed');
    ws.close();
  });
  
  // Forward client messages to STT server
  ws.on('message', (data) => {
    if (sttWs.readyState === WebSocket.OPEN) {
      sttWs.send(data);
    }
  });
  
  ws.on('close', () => {
    console.log('Client disconnected');
    sttWs.close();
  });
  
  ws.on('error', (error) => {
    console.error('Client error:', error);
    sttWs.close();
  });
});