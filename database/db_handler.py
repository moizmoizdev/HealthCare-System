import mysql.connector
from mysql.connector import Error
from typing import List, Dict, Any
from config.chatbot_config import DB_CONFIG

class DatabaseHandler:
    def __init__(self):
        self.connection = None
        self.connect()

    def connect(self):
        try:
            self.connection = mysql.connector.connect(**DB_CONFIG)
            if self.connection.is_connected():
                print("Successfully connected to MySQL database")
        except Error as e:
            print(f"Error connecting to MySQL database: {e}")

    def disconnect(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("MySQL connection closed")

    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        try:
            cursor = self.connection.cursor(dictionary=True)
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            results = cursor.fetchall()
            cursor.close()
            return results
        except Error as e:
            print(f"Error executing query: {e}")
            return []

    def execute_many(self, query: str, params: List[tuple]) -> bool:
        try:
            cursor = self.connection.cursor()
            cursor.executemany(query, params)
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"Error executing multiple queries: {e}")
            return False

    def __del__(self):
        self.disconnect() 