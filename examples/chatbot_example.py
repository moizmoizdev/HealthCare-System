from chatbot.chatbot import HealthcareChatbot

def main():
    # Example usage for different user roles
    roles = ['patient', 'staff', 'doctor']
    
    for role in roles:
        print(f"\n=== Testing chatbot for {role} ===")
        chatbot = HealthcareChatbot(role)
        
        # Example questions
        questions = [
            "What appointments are available for Dr. Smith next week?",
            "Show me the inventory of medical supplies",
            "What are the available departments?",
            "Show me my medical records"
        ]
        
        for question in questions:
            print(f"\nQuestion: {question}")
            response = chatbot.process_query(question)
            print(f"Response: {response}")

if __name__ == "__main__":
    main() 