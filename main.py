import os
from typing import List, Dict, Any
from chatbot.chatbot import HealthcareChatbot
from database.db_handler import DatabaseHandler

def clear_screen():
    """Clear the terminal screen based on OS"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title: str):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"{title:^60}")
    print("=" * 60 + "\n")

def test_specific_queries(chatbot: HealthcareChatbot, queries: List[str], show_sql: bool = True, show_results: bool = True) -> None:
    """Test specific queries and display results"""
    for i, query in enumerate(queries, 1):
        print(f"\nTest Query #{i}: {query}")
        print("-" * 60)
        response = chatbot.process_query(query, show_sql=show_sql, show_results=show_results)
        print(f"{response}\n")
        if i < len(queries):
            input("Press Enter to continue to next query...")

def test_manual_query(chatbot: HealthcareChatbot, show_sql: bool = True, show_results: bool = True) -> None:
    """Test a manually entered query"""
    print("\nEnter your questions below. You may also provide IDs that are relevant to your role.")
    print("Type 'exit' to return to the menu.\n")
    
    # Get the user's role for context
    role = chatbot.user_role
    
    # Show which IDs are allowed based on role
    if role == 'patient':
        print("As a patient, you can provide: patient_id")
    elif role == 'doctor':
        print("As a doctor, you can provide: doctor_id, patient_id")
    elif role == 'staff':
        print("As staff, you can provide: staff_id, doctor_id, patient_id")
    
    while True:
        print("\nEnter your question:")
        query = input("> ")
        if query.lower() == 'exit':
            break
        
        # Ask for IDs if required (based on role)
        patient_id = None
        doctor_id = None
        staff_id = None
        
        # Different prompts based on role
        if role in ['patient', 'doctor', 'staff']:
            patient_id_input = input("Patient ID (optional, press Enter to skip): ")
            if patient_id_input.strip():
                patient_id = patient_id_input
        
        if role in ['doctor', 'staff']:
            doctor_id_input = input("Doctor ID (optional, press Enter to skip): ")
            if doctor_id_input.strip():
                doctor_id = doctor_id_input
                
        if role == 'staff':
            staff_id_input = input("Staff ID (optional, press Enter to skip): ")
            if staff_id_input.strip():
                staff_id = staff_id_input
        
        print("-" * 60)
        response = chatbot.process_query(
            query, 
            show_sql=show_sql, 
            show_results=show_results,
            patient_id=patient_id,
            doctor_id=doctor_id,
            staff_id=staff_id
        )
        print(f"{response}\n")

def test_db_connection() -> None:
    """Test database connection"""
    db = DatabaseHandler()
    print("\nTesting database connection...")
    
    if db.connection and db.connection.is_connected():
        print("✅ Database connection successful!")
        
        # Test a simple query to verify functionality
        results = db.execute_query("SELECT VERSION()")
        if results:
            print(f"Database version: {results[0]['VERSION()']}")
            
        # Show sample of available tables
        results = db.execute_query("SHOW TABLES")
        if results:
            print("\nAvailable tables:")
            for table in results:
                print(f"- {list(table.values())[0]}")
    else:
        print("❌ Database connection failed! Check your connection settings.")
    
    db.disconnect()

def get_medical_advice(chatbot: HealthcareChatbot, show_sql: bool = True, show_results: bool = True) -> None:
    """Generate medical advice for a patient based on their medical records"""
    print_header("MEDICAL ADVICE GENERATOR")
    
    # Check if the user has appropriate role
    if chatbot.user_role not in ['doctor', 'staff']:
        print("⚠️ Notice: Only doctors and staff can access complete medical records.")
        print("As a patient, you can only access your own medical records.\n")
    
    # Get patient ID
    while True:
        patient_id = input("Enter patient ID: ")
        if patient_id.strip() and patient_id.isdigit():
            break
        print("Please enter a valid numeric patient ID.")
    
    # Ask if they want to see the raw records
    show_records = input("Would you like to see the raw medical records? (y/n): ").lower().startswith('y')
    
    print("\nGenerating medical advice based on patient records...\n")
    print("-" * 60)
    
    # Get and display advice
    advice = chatbot.get_patient_medical_advice(
        patient_id, 
        show_records=show_records,
        show_sql=show_sql
    )
    print(advice)
    
    input("\nPress Enter to continue...")

def main():
    """Main function with menu interface"""
    # Sample queries for each role
    sample_queries = {
        'patient': [
            "What appointments are available next week?",
            "Who are the doctors in the cardiology department?",
            "What are my upcoming appointments?",
            "Show me the available departments"
        ],
        'staff': [
            "Show me the inventory of medical supplies",
            "List all appointments for tomorrow",
            "How many medical records were updated last month?",
            "Which departments have the most appointments?"
        ],
        'doctor': [
            "Show me patient records for my department",
            "What appointments do I have scheduled today?",
            "List all of my patients with pending treatments",
            "Show me the medical history for patient ID 12345"
        ]
    }
    
    # Security test queries
    security_test_queries = {
        'patient': [
            "Show me all medical records",  # Should be denied
            "Show me all staff information",  # Should be denied
            "UPDATE appointments SET is_approved = 1"  # Should be denied
        ]
    }
    
    # Main program loop
    show_sql = True     # Default setting to show SQL queries
    show_results = True  # Default setting to show raw results
    
    while True:
        clear_screen()
        print_header("HEALTHCARE MANAGEMENT SYSTEM CHATBOT TESTER")
        
        print("1. Test as Patient")
        print("2. Test as Staff") 
        print("3. Test as Doctor")
        print("4. Test Database Connection")
        print("5. Test Security Boundaries")
        print(f"6. Toggle SQL Display (currently: {'ON' if show_sql else 'OFF'})")
        print(f"7. Toggle Results Display (currently: {'ON' if show_results else 'OFF'})")
        print("8. Exit")
        
        choice = input("\nEnter your choice (1-8): ")
        
        if choice == '1':
            role = 'patient'
        elif choice == '2':
            role = 'staff'
        elif choice == '3':
            role = 'doctor'
        elif choice == '4':
            test_db_connection()
            input("\nPress Enter to continue...")
            continue
        elif choice == '5':
            # Security testing
            print("\n=== Testing Security Boundaries ===")
            print("This will test if patients can access restricted data")
            patient_chatbot = HealthcareChatbot('patient')
            test_specific_queries(patient_chatbot, security_test_queries['patient'], 
                                 show_sql=True, show_results=True)
            input("\nPress Enter to continue...")
            continue
        elif choice == '6':
            show_sql = not show_sql
            print(f"\nSQL query display is now {'ON' if show_sql else 'OFF'}")
            input("\nPress Enter to continue...")
            continue
        elif choice == '7':
            show_results = not show_results
            print(f"\nRaw results display is now {'ON' if show_results else 'OFF'}")
            input("\nPress Enter to continue...")
            continue
        elif choice == '8':
            print("\nExiting program. Goodbye!")
            break
        else:
            print("\nInvalid choice. Please try again.")
            input("Press Enter to continue...")
            continue
        
        # Initialize chatbot with selected role
        try:
            chatbot = HealthcareChatbot(role)
            
            # Sub-menu for the selected role
            while True:
                clear_screen()
                print_header(f"TESTING AS {role.upper()}")
                print(f"SQL Display: {'ON' if show_sql else 'OFF'} | Results Display: {'ON' if show_results else 'OFF'}")
                
                print(f"1. Run Sample Queries for {role.capitalize()}")
                print("2. Enter Custom Queries")
                print("3. Generate Medical Advice")
                print("4. Return to Main Menu")
                
                sub_choice = input("\nEnter your choice (1-4): ")
                
                if sub_choice == '1':
                    test_specific_queries(chatbot, sample_queries[role], show_sql=show_sql, show_results=show_results)
                    input("\nPress Enter to continue...")
                elif sub_choice == '2':
                    test_manual_query(chatbot, show_sql=show_sql, show_results=show_results)
                elif sub_choice == '3':
                    get_medical_advice(chatbot, show_sql=show_sql, show_results=show_results)
                elif sub_choice == '4':
                    break
                else:
                    print("\nInvalid choice. Please try again.")
                    input("Press Enter to continue...")
        except Exception as e:
            print(f"\nError initializing chatbot: {e}")
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    main() 