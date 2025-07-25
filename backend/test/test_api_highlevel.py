import unittest
from api import app
import json
import os
from config.settings import settings
from datetime import datetime

now_str = datetime.now().strftime('%Y%m%d_%H%M%S')
LOG_FILE = os.path.join(os.path.dirname(__file__), f'test_results_log_{now_str}.txt')

def log_test_result(category, query, prev_profile, prev_memory, response):
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"\nCategory: {category}\nQuery: {query}\nPrevious Profile: {json.dumps(prev_profile, indent=2, ensure_ascii=False)}\nPrevious Memory: {json.dumps(prev_memory, indent=2, ensure_ascii=False)}\nResponse: {json.dumps(response, indent=2, ensure_ascii=False)}\n{'-'*60}\n")

class TestAPIHighLevel(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.dummy_profile = {
            "uid": "123",
            "name": "John Doe",
            "age": 35,
            "bloodType": "O+",
            "allergies": ["pollen"],
            "treatment": {
                "medicationList": ["aspirin"],
                "dailyChecklist": ["walk"],
                "appointment": "2024-07-22",
                "recommendations": ["drink water"],
                "sleepHours": 7,
                "sleepQuality": "good"
            }
        }
        self.dummy_memory = {
            "episodes": [],
            "procedural": {},
            "semantic": []
        }

    def _send_and_return(self, prompt, profile, memory):
        payload = {
            "prompt": prompt,
            "patientProfile": profile,
            "memory": memory
        }
        response = self.app.post("/api/agent", data=json.dumps(payload), content_type="application/json")
        return response.get_json()

    def test_patient_profile_prompts(self):
        category = "patient profile"
        queries = [
            # Specific updates
            "Update my age to 40.",
            "Add yoga to my daily routine.",
            "Change my appointment to 2024-08-01.",
            "Add penicillin to my allergies.",
            "Remove aspirin from my medications.",
            "Update my name to Jane Smith.",
            "Add meditation to my daily checklist.",
            "Delete my allergy to pollen.",
            "Update my sleep hours to 8.",
            "Add vitamin D to my medications.",
            # Vague or indirect updates
            "Make my profile more up to date.",
            "I want to start a new health routine.",
            "Change something in my medications.",
            "Improve my daily checklist.",
            "Update my health info."
        ]
        profile = json.loads(json.dumps(self.dummy_profile))
        memory = json.loads(json.dumps(self.dummy_memory))
        for query in queries:
            prev_profile = json.loads(json.dumps(profile))
            prev_memory = json.loads(json.dumps(memory))
            response = self._send_and_return(query, profile, memory)
            log_test_result(category, query, prev_profile, prev_memory, response)

    def test_web_search_prompts(self):
        category = "web search"
        queries = [
            "Current bitcoin value.",
            "Latest news on diabetes research.",
            "Weather in Dubai today.",
            "Nvidia stock price.",
            "COVID-19 cases in US.",
            "Population of China.",
            "Earthquake in Japan today.",
            "Manchester United last match score.",
            "Gold price today.",
            "Top news headlines.",
            "Weather forecast for New York tomorrow.",
            "Ethereum price now.",
            "Latest advancements in AI research.",
            "Current oil prices.",
            "US presidential election news."
        ]
        profile = json.loads(json.dumps(self.dummy_profile))
        memory = json.loads(json.dumps(self.dummy_memory))
        for query in queries:
            prev_profile = json.loads(json.dumps(profile))
            prev_memory = json.loads(json.dumps(memory))
            response = self._send_and_return(query, profile, memory)
            log_test_result(category, query, prev_profile, prev_memory, response)

    def test_general_conversation_prompts(self):
        category = "general conversation"
        queries = [
            "Hi",
            "Hello, how are you?",
            "Tell me a joke.",
            "Good morning!",
            "What's your name?",
            "How do you work?",
            "Thank you!",
            "Bye.",
            "Can you help me?",
            "What can you do?",
            "Who created you?",
            "How old are you?",
            "What's the meaning of life?",
            "Do you like music?",
            "What's your favorite color?"
        ]
        profile = json.loads(json.dumps(self.dummy_profile))
        memory = json.loads(json.dumps(self.dummy_memory))
        for query in queries:
            prev_profile = json.loads(json.dumps(profile))
            prev_memory = json.loads(json.dumps(memory))
            response = self._send_and_return(query, profile, memory)
            log_test_result(category, query, prev_profile, prev_memory, response)

    def test_semantic_memory_search(self):
        category = "semantic memory search"
        queries = [
            "I like roses",
            "I am a fan of Chelsea",
            "What is my favorite flower?",
            "Remind me about my preferences.",
            "What did I tell you about my sleep?",
            "Do you remember my favorite football team?",
            "Recall my favorite color.",
            "What do you know about my hobbies?",
            "Remind me what I said about tea.",
            "What are my preferences?",
            "What did I mention about my allergies?",
            "What do you remember about my routines?",
            "Recall my favorite drink.",
            "What did I say about my diet?",
            "Remind me of my favorite activities."
        ]
        profile = json.loads(json.dumps(self.dummy_profile))
        memory = json.loads(json.dumps(self.dummy_memory))
        memory["semantic"] = [
            {
                "category": "general",
                "content": "I like roses",
                "id": "acf5b003-0757-400b-ba0b-6a0e0c1917cb",
                "metadata": {},
                "patient_id": "default_patient"
            },
            {
                "category": "general",
                "content": "I am a fan of Chelsea",
                "id": "e77091cf-d931-42a4-8e76-9325d23de73d",
                "metadata": {},
                "patient_id": "default_patient"
            }
        ]
        for query in queries:
            prev_profile = json.loads(json.dumps(profile))
            prev_memory = json.loads(json.dumps(memory))
            response = self._send_and_return(query, profile, memory)
            log_test_result(category, query, prev_profile, prev_memory, response)

    def test_semantic_memory_update(self):
        category = "semantic memory update"
        queries = [
            "I like tulips",
            "I enjoy watching football, especially Chelsea",
            "I have some preferences you should remember.",
            "I prefer tea over coffee.",
            "Remember that I love hiking.",
            "I dislike loud noises.",
            "I want to try meditation.",
            "I am allergic to peanuts.",
            "I want to start a new hobby: painting.",
            "I want to remember my favorite movie is Inception.",
            "I want to keep track of my water intake.",
            "I want to remember my favorite author is Tolkien.",
            "I want to remember my favorite city is Paris.",
            "I want to remember my favorite animal is dog."
        ]
        profile = json.loads(json.dumps(self.dummy_profile))
        memory = json.loads(json.dumps(self.dummy_memory))
        for query in queries:
            prev_profile = json.loads(json.dumps(profile))
            prev_memory = json.loads(json.dumps(memory))
            response = self._send_and_return(query, profile, memory)
            log_test_result(category, query, prev_profile, prev_memory, response)

if __name__ == '__main__':
    unittest.main() 