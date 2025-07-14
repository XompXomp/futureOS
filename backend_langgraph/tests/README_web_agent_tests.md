# Web Agent Tests

This directory contains comprehensive tests for the web search agent functionality.

## Test Files

### `test_web_agent.py`
The main test file for the web search agent. It includes:

- **Basic Web Agent Functionality**: Tests various search queries and responses
- **Web Search Tools**: Tests the underlying search tools directly
- **Memory Management**: Tests the agent's memory storage and retrieval capabilities

### `run_web_agent_test.py`
A simple test runner script that can be executed directly to run all web agent tests.

## Running the Tests

### Option 1: Using the Test Runner
```bash
cd backend_langgraph
python run_web_agent_test.py
```

### Option 2: Running Individual Tests
```bash
cd backend_langgraph
python tests/test_web_agent.py
```

### Option 3: Running Specific Test Functions
```python
from tests.test_web_agent import test_web_agent, test_web_agent_tools

# Run only basic functionality tests
test_web_agent()

# Run only tool tests
test_web_agent_tools()
```

## Test Coverage

The web agent tests cover the following areas:

### 1. Basic Web Search Functionality
- Weather queries
- News searches
- Technical information searches
- Current events queries
- Error handling for empty queries

### 2. Query Extraction
- LLM-based query refinement
- Semantic understanding of user intent
- Query optimization for search engines

### 3. Memory Management
- Semantic memory storage
- Episodic memory tracking
- Procedural memory for search patterns
- Memory retrieval and recall

### 4. Tool Integration
- Google PSE search integration
- Semantic search capabilities
- Document search functionality

## Test Structure

Each test follows this pattern:

1. **Setup**: Initialize the web agent
2. **Execute**: Run a search query through the agent
3. **Inspect**: Show memory contents and response
4. **Verify**: Check for errors and validate responses

## Expected Output

The tests will show:

- Search queries and responses
- Memory contents after each operation
- Error messages if any issues occur
- Tool execution results
- Memory storage and retrieval patterns

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure all dependencies are installed
   ```bash
   pip install -r requirements.txt
   ```

2. **LLM Connection Issues**: Check your Ollama or Groq configuration in `config/settings.py`

3. **Search API Errors**: Verify Google PSE API keys are set correctly

4. **Memory Errors**: Check if the memory store is properly initialized

### Debug Mode

To run tests with more verbose output, you can modify the logging level in `utils/logging_config.py`:

```python
logging.basicConfig(level=logging.DEBUG)
```

## Test Customization

You can customize the tests by:

1. **Adding New Test Cases**: Add new test functions to `test_web_agent.py`
2. **Modifying Search Queries**: Change the test queries in the state dictionaries
3. **Testing Different Scenarios**: Add edge cases and error conditions
4. **Memory Inspection**: Modify the `show_memory_contents` function to inspect specific memory types

## Integration with Other Tests

The web agent tests are designed to work alongside other agent tests:

- `test_patient_agent.py`: Tests patient-specific functionality
- `test_json_agent.py`: Tests JSON processing capabilities

You can run all tests together or individually depending on your needs.

## Performance Notes

- Tests may take some time due to LLM calls and web searches
- Memory inspection adds overhead but provides valuable debugging information
- Consider running tests in isolation for faster feedback during development

## Contributing

When adding new tests:

1. Follow the existing pattern in `test_web_agent.py`
2. Include memory inspection for debugging
3. Add comprehensive error handling
4. Document any new test scenarios
5. Update this README if adding new test categories 