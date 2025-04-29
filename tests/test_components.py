import sys
import os
from typing import Dict, List, Any
import time

# Add parent directory to sys.path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_handler import DatabaseHandler
from ai.deepseek_handler import DeepSeekHandler
from chatbot.chatbot import HealthcareChatbot
from config.chatbot_config import ROLE_PERMISSIONS, schema

def test_database_connection():
    """Test database connection and basic operations"""
    print("\n=== Testing Database Connection ===")
    db = DatabaseHandler()
    
    # Test connection
    print("Connecting to database...")
    if db.connection and db.connection.is_connected():
        print("✅ Connection successful")
    else:
        print("❌ Connection failed")
        return
    
    # Test simple query
    print("\nExecuting simple query...")
    results = db.execute_query("SELECT VERSION()")
    if results:
        print(f"✅ Query successful: {results}")
    else:
        print("❌ Query failed")
    
    # Test database schema
    print("\nGetting table information...")
    results = db.execute_query("SHOW TABLES")
    if results:
        print("✅ Tables found:")
        for table in results:
            table_name = list(table.values())[0]
            print(f"  - {table_name}")
            # Show columns for each table
            columns = db.execute_query(f"DESCRIBE {table_name}")
            for col in columns[:3]:  # Show just first 3 columns to avoid too much output
                print(f"    * {col['Field']} ({col['Type']})")
            if len(columns) > 3:
                print(f"    * ... and {len(columns)-3} more columns")
    else:
        print("❌ No tables found")
    
    db.disconnect()
    print("\nDatabase connection closed")

def test_deepseek_handler():
    """Test DeepSeek AI handler"""
    print("\n=== Testing DeepSeek Handler ===")
    
    # Initialize handler
    print("Initializing DeepSeek handler...")
    try:
        ai_handler = DeepSeekHandler()
        print("✅ DeepSeek handler initialized")
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return
    
    # Test SQL generation
    print("\nTesting SQL query generation...")
    test_question = "What appointments are available next week?"
    try:
        sql_query = ai_handler.generate_sql_query(
            test_question, 
            schema,
            'patient'
        )
        print(f"✅ SQL query generated: \n{sql_query}")
        
        # Try to validate the SQL query syntax
        print("\nValidating SQL query syntax...")
        try:
            db = DatabaseHandler()
            if db.connection and db.connection.is_connected():
                # We won't actually execute the query but will check its syntax
                cursor = db.connection.cursor()
                cursor.execute(f"EXPLAIN {sql_query}")
                cursor.close()
                print("✅ SQL query syntax is valid")
            db.disconnect()
        except Exception as e:
            print(f"❌ SQL validation failed: {str(e)}")
            
    except Exception as e:
        print(f"❌ SQL generation failed: {e}")
    
    # Test general response
    print("\nTesting general response...")
    try:
        response = ai_handler.get_general_response("What is hypertension?")
        print(f"✅ General response received: \n{response[:100]}...")
    except Exception as e:
        print(f"❌ General response failed: {e}")

def test_chatbot_with_roles():
    """Test chatbot with different roles"""
    print("\n=== Testing Chatbot with Different Roles ===")
    
    roles = ['patient', 'staff', 'doctor']
    questions = [
        "Show me available appointments",
        "List all departments",
        "How many doctors are in cardiology?"
    ]
    
    for role in roles:
        print(f"\n--- Testing as {role.upper()} ---")
        try:
            chatbot = HealthcareChatbot(role)
            print(f"✅ Chatbot initialized for {role}")
            
            # Test permissions
            permissions = ROLE_PERMISSIONS[role]
            print(f"Allowed tables: {', '.join(permissions['allowed_tables'])}")
            print(f"Allowed operations: {', '.join(permissions['allowed_operations'])}")
            
            # Test queries
            for question in questions:
                print(f"\nQuestion: {question}")
                start_time = time.time()
                response = chatbot.process_query(question, show_sql=True, show_results=True)
                elapsed = time.time() - start_time
                print(f"Response time: {elapsed:.2f}s")
                print(f"{response}")
                
                time.sleep(1)  # Small delay to avoid overwhelming API
                
        except Exception as e:
            print(f"❌ Test failed for {role}: {e}")

def run_all_tests():
    """Run all component tests"""
    test_database_connection()
    test_deepseek_handler()
    test_chatbot_with_roles()

if __name__ == "__main__":
    # Check for command-line arguments to run specific tests
    if len(sys.argv) > 1:
        if sys.argv[1] == 'db':
            test_database_connection()
        elif sys.argv[1] == 'ai':
            test_deepseek_handler()
        elif sys.argv[1] == 'chatbot':
            test_chatbot_with_roles()
        else:
            print(f"Unknown test: {sys.argv[1]}")
            print("Available tests: db, ai, chatbot")
    else:
        run_all_tests() 