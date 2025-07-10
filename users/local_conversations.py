# THE METHODS THE AI WOULD NEED TO CALL EVENTUALLY


import sqlite3
from datetime import datetime
from typing import List, Optional
import json

DB_PATH = 'instance/local_conversations.db'

# Ensure the database and table exist
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    conversation TEXT NOT NULL,  -- JSON string
    timestamp TEXT NOT NULL,
    tags TEXT,
    source TEXT CHECK(source IN ('audio', 'text', 'ambient')) NOT NULL
)
''')
conn.commit()
conn.close()

def add_conversation(user_id: int, conversation: List[dict], tags: List[str], source: str):
    """
    Add a conversation for a user, keeping only the last 10.
    conversation: List of message dicts, e.g.
    [
        {"sender": "user", "text": "Hi", "timestamp": "2024-06-01T12:00:00Z"},
        {"sender": "ai", "text": "Hello!", "timestamp": "2024-06-01T12:00:01Z"}
    ]
    """
    timestamp = datetime.utcnow().isoformat()
    tags_str = ','.join(tags)
    conversation_json = json.dumps(conversation)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO conversations (user_id, conversation, timestamp, tags, source)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, conversation_json, timestamp, tags_str, source))
    # Delete older conversations if more than 10 exist for this user
    c.execute('''
        DELETE FROM conversations WHERE id IN (
            SELECT id FROM conversations WHERE user_id = ? ORDER BY timestamp DESC LIMIT -1 OFFSET 10
        )
    ''', (user_id,))
    conn.commit()
    conn.close()

def get_last_conversations(user_id: int, limit: int = 10):
    """
    Get the last N conversations for a user, most recent first.
    Returns a list of dicts with deserialized conversation JSON and conversation ID.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT id, conversation, timestamp, tags, source FROM conversations
        WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?
    ''', (user_id, limit))
    results = c.fetchall()
    conn.close()
    return [
        {
            'id': row[0],
            'conversation': json.loads(row[1]),
            'timestamp': row[2],
            'tags': row[3].split(',') if row[3] else [],
            'source': row[4]
        } for row in results
    ]

def search_conversations_by_tag(user_id: int, tag: str):
    """
    Search for conversations by tag for a user. Returns deserialized conversation JSON and conversation ID.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT id, conversation, timestamp, tags, source FROM conversations
        WHERE user_id = ? AND (',' || tags || ',') LIKE ? ORDER BY timestamp DESC
    ''', (user_id, f'%,{tag},%'))
    results = c.fetchall()
    conn.close()
    return [
        {
            'id': row[0],
            'conversation': json.loads(row[1]),
            'timestamp': row[2],
            'tags': row[3].split(',') if row[3] else [],
            'source': row[4]
        } for row in results
    ]

def get_conversation_by_id(conversation_id: int):
    """
    Retrieve a conversation by its unique ID.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, conversation, timestamp, tags, source FROM conversations WHERE id = ?', (conversation_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            'id': row[0],
            'conversation': json.loads(row[1]),
            'timestamp': row[2],
            'tags': row[3].split(',') if row[3] else [],
            'source': row[4]
        }
    return None

def append_to_conversation(conversation_id: int, new_messages: list):
    """
    Append new messages to an existing conversation by its ID.
    new_messages: list of message dicts to add.
    Returns True if successful, False if conversation not found.
    """
    import json
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT conversation FROM conversations WHERE id = ?', (conversation_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return False  # Conversation not found
    conversation = json.loads(row[0])
    conversation.extend(new_messages)
    c.execute('UPDATE conversations SET conversation = ? WHERE id = ?', (json.dumps(conversation), conversation_id))
    conn.commit()
    conn.close()
    return True 