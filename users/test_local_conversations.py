from local_conversations import add_conversation, get_last_conversations
from datetime import datetime

user_id = 42

def now():
    return datetime.utcnow().isoformat()

conversations = [
    {
        "messages": [
            {"sender": "user", "text": "Hi!", "timestamp": now()},
            {"sender": "ai", "text": "Hello! How can I help you today?", "timestamp": now()},
            {"sender": "user", "text": "What's the weather?", "timestamp": now()},
            {"sender": "ai", "text": "It's sunny and 25°C.", "timestamp": now()}
        ],
        "tags": ["greeting", "weather"],
        "source": "text"
    },
    {
        "messages": [
            {"sender": "user", "text": "Play some music.", "timestamp": now()},
            {"sender": "ai", "text": "Playing your favorite playlist.", "timestamp": now()},
            {"sender": "user", "text": "Next song.", "timestamp": now()},
            {"sender": "ai", "text": "Skipping to the next track.", "timestamp": now()}
        ],
        "tags": ["music", "audio"],
        "source": "audio"
    },
    {
        "messages": [
            {"sender": "user", "text": "Remind me to call mom.", "timestamp": now()},
            {"sender": "ai", "text": "Reminder set for today at 6pm.", "timestamp": now()},
            {"sender": "user", "text": "Thanks!", "timestamp": now()},
            {"sender": "ai", "text": "You're welcome!", "timestamp": now()}
        ],
        "tags": ["reminder", "family"],
        "source": "text"
    }
]

for i, conv in enumerate(conversations, 1):
    print(f"Adding conversation {i}...")
    add_conversation(user_id, conv["messages"], conv["tags"], conv["source"])
    print(f"Conversation {i} added.")

print("\nList of last conversations:")
convs = get_last_conversations(user_id)
for c in convs:
    print(f"ID: {c['id']}, Tags: {c['tags']}, Source: {c['source']}")
    for msg in c['conversation']:
        print(f"  {msg['sender']}: {msg['text']}") 