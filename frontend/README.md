# FutureOS AI Assistant Frontend

A modern, responsive web interface for the FutureOS AI healthcare assistant.

## Features

- 🤖 **AI Chat Interface**: Clean, modern chat UI with real-time responses
- 📱 **Responsive Design**: Works on desktop, tablet, and mobile devices
- 💬 **Interactive Suggestions**: Quick action buttons for common queries
- ⚡ **Real-time Communication**: Instant messaging with the AI backend
- 🎨 **Modern UI**: Beautiful gradient design with smooth animations

## Quick Start

### 1. Install Dependencies

```bash
cd frontend
pip install -r requirements.txt
```

### 2. Start the API Server

```bash
python api.py
```

The API server will start on `http://localhost:5000`

### 3. Open the Frontend

Simply open `index.html` in your web browser, or serve it using a local server:

```bash
# Using Python's built-in server
python -m http.server 8000

# Then open http://localhost:8000 in your browser
```

## API Endpoints

- `POST /api/chat` - Send a message to the AI assistant
- `GET /api/health` - Check API health status

## Usage

1. **Type your message** in the input field at the bottom
2. **Press Enter** or click the send button
3. **Use suggestion buttons** for quick common queries
4. **Wait for the AI response** - you'll see a loading animation

## Example Queries

- "What is my name?"
- "Show my medical information"
- "What medications am I taking?"
- "Update my profile"
- "What are my allergies?"

## Troubleshooting

### API Connection Issues

If you see "Unable to connect to the server" error:

1. Make sure the API server is running (`python api.py`)
2. Check that the server is on `localhost:5000`
3. Ensure no firewall is blocking the connection

### Backend Dependencies

The frontend API requires the backend to be properly set up with all dependencies. Make sure you have:

1. All backend requirements installed
2. Proper environment variables set
3. Backend modules accessible

## File Structure

```
frontend/
├── api.py              # Flask API server
├── index.html          # Main frontend interface
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Development

The frontend is built with:
- **HTML5** - Structure
- **CSS3** - Styling with modern gradients and animations
- **JavaScript** - Interactive functionality
- **Flask** - API server

## Browser Support

- Chrome (recommended)
- Firefox
- Safari
- Edge

## License

This project is part of the FutureOS healthcare system. 