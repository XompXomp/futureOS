import asyncio
from typing import Dict, Any
from agents.patient_agent import PatientAgent
from agents.file_agent import FileAgent
from agents.web_agent import WebAgent
from agents.text_agent import TextAgent
from agents.json_agent import JsonAgent
from utils.logging_config import logger
from tools.memory_tools import create_memory_tools
from config.settings import settings
from langchain_community.chat_models import ChatOllama
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama

class OrchestratorAgent:
    def __init__(self, orchestrator_id: str = "orchestrator"):
        """Initialize the orchestrator with LLM-driven routing and specialized agents."""
        # Initialize specialized agents
        self.patient_agent = PatientAgent()
        self.file_agent = FileAgent()
        self.web_agent = WebAgent()
        self.text_agent = TextAgent()
        self.json_agent = JsonAgent()
        
        # Initialize memory system for this orchestrator
        self.orchestrator_id = orchestrator_id
        self.memory_tools = create_memory_tools(orchestrator_id)
        
        # LLM selection based on settings
        if settings.USE_OLLAMA:
            self.llm = ChatOllama(
                model=settings.OLLAMA_MODEL,
                base_url=settings.OLLAMA_BASE_URL,
                temperature=0.3
            )
        else:
            self.llm = ChatGroq(
                model=settings.LLM_MODEL,
                temperature=0.3
            )
        
        # Build agent/tool registry for prompt and routing
        self.agent_registry = {
            "patient_agent": {
                "instance": self.patient_agent,
                "description": "Handles patient profile queries, updates, and medical information (semantic/episodic/procedural memory)"
            },
            "file_agent": {
                "instance": self.file_agent,
                "description": "Handles file operations like reading, writing, and managing documents"
            },
            "web_agent": {
                "instance": self.web_agent,
                "description": "Handles web searches and online information gathering"
            },
            "text_agent": {
                "instance": self.text_agent,
                "description": "Handles text processing, summarization, and analysis"
            },
            "json_agent": {
                "instance": self.json_agent,
                "description": "Handles JSON file operations (read, write, list JSON files)"
            }
        }

    def _build_routing_prompt(self, user_input: str) -> str:
        """Build a descriptive system prompt for the LLM, listing all agents/tools."""
        prompt = (
            "You are the Orchestrator Agent for a multi-agent AI system. "
            "Your job is to decide which specialized agent should handle the user's request.\n\n"
            "Available agents and their capabilities:\n"
        )
        for name, info in self.agent_registry.items():
            prompt += f"- {name}: {info['description']}\n"
        prompt += (
            "\nRouting Rules:\n"
            "1. patient_agent: Use for questions about patient info, medical data, personal details\n"
            "2. web_agent: Use for current events, news, weather, online searches, factual questions\n"
            "3. text_agent: Use for text analysis, summarization, general conversation, greetings\n"
            "4. file_agent: Use for file operations, reading/writing documents\n"
            "5. json_agent: Use for JSON file operations, data management\n"
            "\nIMPORTANT: Always try to route to a specific agent. Only use fallback if the request is completely ambiguous.\n"
            "For greetings like 'Hello', 'Hi', etc. - route to text_agent\n"
            "For general questions - route to web_agent\n"
            "For patient-related queries - route to patient_agent\n"
            "\nOutput your decision as JSON:\n"
            "{\"agent\": \"agent_name\", \"parameters\": {\"query\": \"user's request\"}}\n"
            "\nExamples:\n"
            "- User: 'Hello' → {\"agent\": \"text_agent\", \"parameters\": {\"input\": \"Hello\"}}\n"
            "- User: 'What's the weather?' → {\"agent\": \"web_agent\", \"parameters\": {\"query\": \"weather today\"}}\n"
            "- User: 'What's my name?' → {\"agent\": \"patient_agent\", \"parameters\": {\"query\": \"patient name\"}}\n"
            "\nUser input: {user_input}\n"
        )
        return prompt

    def _parse_llm_output(self, llm_output: str) -> Dict[str, Any]:
        """Parse the LLM output to extract the agent/tool call."""
        import json
        llm_output = llm_output.strip()
        # Try JSON
        try:
            parsed = json.loads(llm_output)
            if isinstance(parsed, dict) and "agent" in parsed:
                return parsed
        except Exception:
            pass
        # Try simple string
        for agent in self.agent_registry:
            if agent in llm_output:
                return {"agent": agent, "parameters": {}}
        # Fallback
        return {"agent": "fallback", "parameters": {"echo": llm_output}}

    def handle(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """LLM-based routing handler for orchestrator tasks."""
        try:
            user_input = state.get('user_input', '')
            system_prompt = self._build_routing_prompt(user_input)
            messages = state.get('messages', [])
            # Compose LLM input
            llm_input = [
                {"role": "system", "content": system_prompt},
                *[{"role": "user", "content": user_input}]
            ]
            # Call LLM
            response = self.llm.invoke(llm_input)
            llm_output = response.content if hasattr(response, 'content') else str(response)
            logger.info(f"Orchestrator LLM output: {llm_output}")
            # Parse LLM output
            parsed = self._parse_llm_output(str(llm_output))
            agent_name = parsed.get("agent")
            parameters = parsed.get("parameters", {})
            # Route to the chosen agent
            if agent_name in self.agent_registry:
                logger.info(f"Routing to {agent_name}")
                # Merge parameters into state if any
                routed_state = state.copy()
                routed_state.update(parameters)
                result = self.agent_registry[agent_name]["instance"].handle(routed_state)
                return result
            else:
                # Fallback: echo user input or return a clarifying message
                logger.warning(f"LLM output ambiguous or unrecognized. Fallback triggered.")
                state["final_response"] = f"I'm not sure which agent should handle your request. Echo: {user_input}"
                return state
        except Exception as e:
            logger.error(f"Error in orchestrator agent: {str(e)}")
            state["error_message"] = f"Error in orchestrator agent: {str(e)}"
            state["has_error"] = True
            return state 