# Agent Tests

This directory contains individual test scripts for each agent in the system. These tests verify that each agent works correctly without memory functionality.

## Test Files

- `test_patient_agent.py` - Tests patient profile management functionality
- `test_web_agent.py` - Tests web search capabilities
- `test_text_agent.py` - Tests text processing and analysis tools
- `test_file_agent.py` - Tests file reading and writing operations
- `test_json_agent.py` - Tests JSON file operations
- `test_all_agents.py` - Master script to run all tests

## Running Tests

### Run Individual Tests

To test a specific agent:

```bash
# From the backend_langgraph directory
python tests/test_patient_agent.py
python tests/test_web_agent.py
python tests/test_text_agent.py
python tests/test_file_agent.py
python tests/test_json_agent.py
```

### Run All Tests

To run all agent tests at once:

```bash
# From the backend_langgraph directory
python tests/test_all_agents.py
```

## Test Structure

Each test script:

1. **Initializes the agent** with core tools (no memory tools)
2. **Creates test cases** specific to that agent's functionality
3. **Runs each test case** and displays the response
4. **Handles errors** gracefully with detailed error reporting

## Test Cases

### Patient Agent
- Reading patient profiles
- Updating patient information
- Querying medical conditions
- Managing allergies and medications

### Web Agent
- Searching for current information
- Finding news and facts
- Looking up historical data
- Getting weather information

### Text Agent
- Greeting responses
- Agent listing
- Text summarization
- Keyword extraction

### File Agent
- Reading files from data/docs
- Writing files to data/docs
- Listing available files
- File content management

### JSON Agent
- Reading JSON files
- Writing JSON data
- Listing JSON files
- JSON structure management

## Expected Behavior

Each agent should:
- Respond conversationally to user input
- Use appropriate tools when needed
- Provide meaningful responses
- Handle errors gracefully
- Not rely on memory functionality

## Troubleshooting

If tests fail:

1. **Check dependencies** - Ensure all required packages are installed
2. **Verify file paths** - Make sure data/docs directory exists
3. **Check LLM configuration** - Verify settings.py has correct LLM settings
4. **Review error messages** - Look for specific error details in output

## Notes

- These tests focus on core functionality without memory
- Each agent is tested in isolation
- Tests use the same LLM configuration as the main system
- Error handling is comprehensive to help with debugging 