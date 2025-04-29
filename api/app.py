from flask import Flask, request, jsonify
from flask_cors import CORS
from typing import Dict, Any
import os
import sys
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chatbot.chatbot import HealthcareChatbot
from database.db_handler import DatabaseHandler

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

#since there are 3 ttypes of chatbot access levels
chatbots = {
    'patient': HealthcareChatbot('patient'),
    'staff': HealthcareChatbot('staff'),
    'doctor': HealthcareChatbot('doctor')
}

@app.route('/api/query', methods=['POST'])
def process_query():
    """Process a user query and return results"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'role' not in data or 'query' not in data:
            return jsonify({'error': 'Missing required fields: role and query'}), 400
            
        role = data['role']
        if role not in chatbots:
            return jsonify({'error': f'Invalid role. Must be one of: {", ".join(chatbots.keys())}'}), 400
            
        # Get optional parameters
        show_sql = data.get('show_sql', False)
        show_results = data.get('show_results', False)
        
        # Get the appropriate ID based on role
        id_param = None
        if role == 'patient':
            id_param = data.get('patient_id')
        elif role == 'staff':
            id_param = data.get('staff_id')
        elif role == 'doctor':
            id_param = data.get('doctor_id')
            
        # Process the query with the appropriate ID
        response = chatbots[role].process_query(
            data['query'],
            show_sql=show_sql,
            show_results=show_results,
            patient_id=data.get('patient_id'),
            staff_id=data.get('staff_id'),
            doctor_id=data.get('doctor_id')
        )
        
        return jsonify({'response': response})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/medical-advice', methods=['POST'])
def get_medical_advice():
    """Get medical advice for a patient"""
    received_req_time = time.time()
    print("Received Request time: "+str(received_req_time))
    try:
        data = request.get_json()
        print("received results: "+str(time.time()-received_req_time))

        
            
        
            
        # Get optional parameters
        show_records = data.get('show_records', False)
        show_sql = data.get('show_sql', False)
        
        # Get medical advice
        advice = chatbots["staff"].get_patient_medical_advice(
            data['patient_id'],
            show_records=show_records,
            show_sql=show_sql
        )
        print("got medical advice results: "+str(time.time()-received_req_time))

        return jsonify({'advice': advice})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 