# Database query tools 

# backend/tools/database_tools.py (continued)
from langchain.agents import Tool
from modules.database_operations import DatabaseOperations
from config.settings import settings
from utils.logging_config import logger

def create_database_tools():
    """Create database operation tools for the agent."""
    
    db_ops = DatabaseOperations("data/database.db")
    
    def query_database_tool(query: str) -> str:
        """Query the database with natural language or SQL."""
        try:
            # First, try to convert natural language to SQL
            sql_query = db_ops.natural_language_to_sql(query)
            
            if sql_query is None:
                # If conversion fails, treat as direct SQL query
                sql_query = query
            
            # Execute the query
            result = db_ops.execute_query(sql_query)
            
            if result is None:
                return "Error: Could not execute database query"
            
            if not result:
                return "No results found for your query"
            
            # Format results
            formatted_result = "Query Results:\n"
            for i, row in enumerate(result[:10]):  # Limit to first 10 results
                formatted_result += f"Row {i+1}: {dict(row)}\n"
            
            if len(result) > 10:
                formatted_result += f"... and {len(result) - 10} more rows"
            
            return formatted_result
        except Exception as e:
            return f"Error querying database: {str(e)}"

    def get_database_schema_tool(table_name: str = "") -> str:
        """Get database schema information."""
        try:
            if table_name:
                # Get specific table schema
                schema = db_ops.get_table_schema(table_name)
                if schema:
                    return f"Schema for table '{table_name}':\n{schema}"
                else:
                    return f"Table '{table_name}' not found"
            else:
                # Get all tables
                tables = db_ops.get_all_tables()
                if tables:
                    return f"Available tables: {', '.join(tables)}"
                else:
                    return "No tables found in database"
        except Exception as e:
            return f"Error getting database schema: {str(e)}"

    return [
        Tool(
            name="query_database",
            func=query_database_tool,
            description="Query the database using natural language or SQL. Input: your question or SQL query"
        ),
        Tool(
            name="get_database_schema",
            func=get_database_schema_tool,
            description="Get database schema information. Input: table_name (optional, leave empty to get all tables)"
        )
    ]