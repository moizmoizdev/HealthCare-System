from typing import Dict, Any, Optional, Tuple
from database.db_handler import DatabaseHandler
from ai.deepseek_handler import DeepSeekHandler
from config.chatbot_config import ROLE_PERMISSIONS, schema, SYSTEM_PROMPTS
import json
import copy
import datetime
import re
import time
# Custom JSON encoder to handle dates and other special types
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        elif isinstance(obj, bytes):
            return obj.decode('utf-8', errors='replace')
        return super().default(obj)

class HealthcareChatbot:
    def __init__(self, user_role: str):
        # Validate the user role
        if user_role not in ROLE_PERMISSIONS:
            raise ValueError(f"Invalid user role: {user_role}. Must be one of: {', '.join(ROLE_PERMISSIONS.keys())}")
            
        self.user_role = user_role
        self.db_handler = DatabaseHandler()
        self.deepseek_handler = DeepSeekHandler()
        self.permissions = ROLE_PERMISSIONS[user_role]
        self.last_sql_query = None
        self.last_results = None

    def process_query(self, user_question: str, show_sql: bool = False, show_results: bool = False, 
                     patient_id: str = None, staff_id: str = None, doctor_id: str = None) -> str:
        """Process user query and return appropriate response with proper security controls"""
        
        try:
            # Validate and sanitize IDs to prevent injection
            safe_user_question = user_question
            
            # Only add IDs if they are valid (numeric) and relevant to the user role
            if patient_id is not None:
                if not self._is_valid_id(patient_id):
                    return "Invalid patient ID format. IDs should be numeric."
                if self.user_role == 'patient' or self.user_role == 'staff' or self.user_role == 'doctor':
                    safe_user_question = f"{safe_user_question}\nPatient ID: {patient_id}"
            
            if staff_id is not None:
                if not self._is_valid_id(staff_id):
                    return "Invalid staff ID format. IDs should be numeric."
                if self.user_role == 'staff':
                    safe_user_question = f"{safe_user_question}\nStaff ID: {staff_id}"
            
            if doctor_id is not None:
                if not self._is_valid_id(doctor_id):
                    return "Invalid doctor ID format. IDs should be numeric."
                if self.user_role == 'doctor' or self.user_role == 'staff':
                    safe_user_question = f"{safe_user_question}\nDoctor ID: {doctor_id}"
            
            # Generate SQL query using DeepSeek with the user's assigned role (not overridable)
            sql_query = self.deepseek_handler.generate_sql_query(
                safe_user_question,
                schema,
                self.user_role
            )
            
            # Apply additional security check to ensure query complies with role permissions
            if not self.is_query_allowed(sql_query):
                return f"This query is not allowed for your role ({self.user_role}). Please try a different question."
                
            self.last_sql_query = sql_query
            
            # Start building the response
            parts = []
            
            # Add SQL query if requested
            if show_sql:
                parts.append(f"Generated SQL Query:\n{sql_query}\n")
            
            # Execute query and get results
            query_results = self.db_handler.execute_query(sql_query)
            self.last_results = query_results
            
            # Add raw results if requested
            if show_results and query_results:
                try:
                    # Format the results nicely with custom encoder for dates
                    if len(query_results) > 10:
                        # If many results, show first 10 with count
                        results_str = json.dumps(query_results[:10], indent=2, cls=CustomJSONEncoder)
                        parts.append(f"Raw Query Results (showing 10 of {len(query_results)} rows):\n{results_str}\n")
                    else:
                        # Show all results
                        results_str = json.dumps(query_results, indent=2, cls=CustomJSONEncoder)
                        parts.append(f"Raw Query Results ({len(query_results)} rows):\n{results_str}\n")
                except Exception as e:
                    parts.append(f"Raw Query Results ({len(query_results)} rows):\nCould not serialize results: {str(e)}\n")
                    # Fallback to simple string representation
                    parts.append(f"Results summary: {str(query_results)[:500]}...\n")
            elif show_results:
                parts.append("Raw Query Results: No data returned\n")
            
            # Generate response based on results
            if query_results:
                # If we have results, explain them
                ai_response = self.deepseek_handler.explain_results(query_results, safe_user_question)
            else:
                # If no results found, provide general information
                ai_response = self.deepseek_handler.get_general_response(safe_user_question)
            
            # Add AI explanation
            parts.append(f"Response:\n{ai_response}")
            
            # Join all parts
            return "\n".join(parts)
                
        except Exception as e:
            error_message = f"I apologize, but I encountered an error processing your request: {str(e)}. Please try rephrasing your question or contact support if the issue persists."
            
            # Include query in error message if available
            if show_sql and self.last_sql_query:
                error_message = f"Generated SQL Query:\n{self.last_sql_query}\n\n{error_message}"
                
            return error_message

    def _is_valid_id(self, id_str: str) -> bool:
        """Validate that an ID is numeric and safe"""
        return id_str is not None and re.match(r'^\d+$', id_str) is not None

    def get_last_sql_query(self) -> str:
        """Return the last SQL query generated"""
        return self.last_sql_query
        
    def get_last_results(self) -> list:
        """Return the last results retrieved"""
        return self.last_results

    def is_query_allowed(self, query: str) -> bool:
        """Check if the query is allowed based on user role"""
        if not query:
            return False
            
        # Convert to lowercase for case-insensitive comparison
        query_lower = query.lower()
        
        # Check for restricted operations
        for operation in ['delete', 'drop', 'truncate', 'alter', 'grant', 'revoke']:
            if operation in query_lower:
                return False
        
        # Ensure only allowed operations are used
        allowed_operations = [op.lower() for op in self.permissions['allowed_operations']]
        for op in ['select', 'insert', 'update', 'delete']:
            if op in query_lower and op not in allowed_operations:
                return False
        
        # Check for allowed tables
        allowed = False
        for table in self.permissions['allowed_tables']:
            # Match whole word only to prevent substring matching
            if re.search(r'\b' + table.lower() + r'\b', query_lower):
                allowed = True
                break
        
        # Check for restricted fields
        for field in self.permissions['restricted_fields']:
            if re.search(r'\b' + field.lower() + r'\b', query_lower):
                return False
                
        return allowed

    def get_patient_medical_advice(self, patient_id: str, show_records: bool = False, show_sql: bool = False) -> str:
        """Get a patient's medical records and provide personalized medical advice"""
        if not self._is_valid_id(patient_id):
            return "Invalid patient ID. Please provide a valid numeric ID."
            
        # Check if the user has appropriate permissions (doctor or staff)
        if self.user_role not in ['doctor', 'staff'] and not patient_id.isdigit():
            return "You don't have permission to access other patients' medical records."
            
        try:
            # Start building the response
            parts = []
            
            # Get patient basic information
            patient_query = f"""
            SELECT p.name, p.gender, p.age, p.birthdate, p.contact_info, 
                  pt.weight, pt.height
            FROM person p
            JOIN patient pt ON p.person_id = pt.patient_id
            WHERE p.person_id = {patient_id};
            """
            
            if show_sql:
                parts.append("SQL Query for Patient Information:")
                parts.append(patient_query)
                parts.append("")
                
            patient_info = self.db_handler.execute_query(patient_query)
            
            if not patient_info:
                return f"No patient found with ID {patient_id}."
                
            # Get patient medical records
            records_query = f"""
            SELECT mr.record_id, mr.diagnosis, mr.bloodpressure, mr.date,
                  d.name as department_name, t.name as treatment_name
            FROM medical_records mr
            JOIN department d ON mr.department_id = d.department_id
            JOIN treatement t ON mr.treatement_id = t.treatement_id
            WHERE mr.patient_id = {patient_id}
            ORDER BY mr.date DESC;
            """
            
            if show_sql:
                parts.append("SQL Query for Medical Records:")
                parts.append(records_query)
                parts.append("")
                
            medical_records = self.db_handler.execute_query(records_query)
            
            if not medical_records:
                return f"No medical records found for patient {patient_info[0].get('name', 'Unknown')}."
                
            # Get doctor's information related to the patient
            doctor_query = f"""
            SELECT DISTINCT p.name as doctor_name, d.specialization
            FROM appointments a
            JOIN doctor d ON a.doctor_id = d.doctor_id
            JOIN person p ON d.doctor_id = p.person_id
            WHERE a.patient_id = {patient_id};
            """
            
            if show_sql:
                parts.append("SQL Query for Doctor Information:")
                parts.append(doctor_query)
                parts.append("")
                
            doctors = self.db_handler.execute_query(doctor_query)
            print("got all queries from db: "+str(time.time()))
            # Show patient info and records if requested
            if show_records:
                parts.append("Patient Information:")
                parts.append(json.dumps(patient_info[0], indent=2, cls=CustomJSONEncoder))
                parts.append("\nMedical Records:")
                parts.append(json.dumps(medical_records, indent=2, cls=CustomJSONEncoder))
                if doctors:
                    parts.append("\nTreating Doctors:")
                    parts.append(json.dumps(doctors, indent=2, cls=CustomJSONEncoder))
                parts.append("")
            
            # Generate medical advice based on the records
            advice = self.deepseek_handler.get_medical_advice(medical_records, patient_info[0])
            parts.append("Medical Advice:")
            parts.append(advice)
            
            return "\n".join(parts)
            
        except Exception as e:
            error_message = f"Error retrieving medical records: {str(e)}"
            print(error_message)
            return error_message

    def __del__(self):
        if hasattr(self, 'db_handler'):
            self.db_handler.disconnect()