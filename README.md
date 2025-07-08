# AI Agent System

A modular AI agent system with file operations, database queries, JSON manipulation, text processing, and RAG capabilities.

## Features

- **File Operations**: Read, write, and append to text files
- **Database Queries**: Natural language to SQL conversion and database operations
- **JSON Management**: Update patient profiles while maintaining structure
- **Text Processing**: Summarization and question answering
- **RAG System**: Document-based question answering
- **Web Interface**: Simple Flask-based chat interface

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```
4. Run the backend:
   ```bash
   cd backend
   python main.py
   ```
5. Run the frontend (optional):
   ```bash
   cd frontend
   python app.py
   ```

## Usage

The agent can handle various tasks:

- "What's in my patient profile?"
- "Update my age to 25"
- "Query all patients from the database"
- "Summarize this text: [your text]"
- "What does the medical documentation say about hypertension?"

## Project Structure

```
MyApp/
├── backend/          # Core agent logic
│   ├── modules/      # Business logic modules
│   ├── tools/        # LangChain tool wrappers
│   ├── config/       # Configuration
│   ├── utils/        # Utilities
│   └── data/         # Data storage
└── frontend/         # Web interface
    ├── templates/    # HTML templates
    └── static/       # CSS/JS assets
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request