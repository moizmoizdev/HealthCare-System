from typing import Dict, List

# Role-based access control for different user types
ROLE_PERMISSIONS = {
    'patient': {
        'allowed_tables': ['appointments', 'doctor', 'department', 'avalibility', 'person'],
        'allowed_operations': ['SELECT'],
        'restricted_fields': ['password', 'contact_info', 'address']
    },
    'staff': {
        'allowed_tables': ['appointments', 'doctor', 'department', 'avalibility', 'inventory', 'medical_records','person'],
        'allowed_operations': ['SELECT', 'INSERT', 'UPDATE'],
        'restricted_fields': ['password']
    },
    'doctor': {
        'allowed_tables': ['appointments', 'doctor', 'department', 'avalibility', 'medical_records','person'],
        'allowed_operations': ['SELECT', 'INSERT', 'UPDATE'],
        'restricted_fields': ['password']
    }
}

# Database configuration
DB_CONFIG = {
    'host': 'healthnetstorage.mysql.database.azure.com',
    'user': 'zero',
    'password': 'UW5KZgLBZmFrDGh',
    'database': 'healthnetstorage'
}

# DeepSeek API configuration
DEEPSEEK_CONFIG = {
    'api_key': 'sk-b20c8baac01e40228ba4ef1bd598863c',
    'model': 'deepseek-chat'
}

# System prompts for different tasks
SYSTEM_PROMPTS = {
    'sql_generation': """You are a SQL query generator for a healthcare management system. Your task is to:
1. Generate SQL queries based on user questions
2. Only use allowed tables and operations based on user role
3. Exclude restricted fields
4. Use proper JOIN conditions
5. Include appropriate WHERE clauses for security
6. Format dates and times correctly
7. DO not add any other text or comments to the query
8. DO not add any quotes or backticks to the query
9. response should include query and query only, nothing else
10. Make sure that query structure is valid, i.e it has semi colons at the end of the query etc...
11. Double check the query before responding
Database Schema:
{schema}

User Role: {user_role}
Allowed Tables: {allowed_tables}
Allowed Operations: {allowed_operations}
Restricted Fields: {restricted_fields}

Please provide only the SQL query without any explanation.""",

    'result_explanation': """You are a healthcare assistant explaining database query results. Your task is to:
1. Explain the results in simple, non-technical language
2. Be concise but informative
3. Include relevant context
4. If data is not found, provide general information based on your knowledge

Please explain the results in a clear, friendly manner.""",

    'general_response': """You are a healthcare assistant for a hospital management system. Your task is to:
1. Help users find information about appointments, doctors, and departments
2. Explain medical information in simple, understandable terms
3. Respect user privacy and access levels
4. Provide general information when specific data is not available

Please provide a clear, informative response in simple language.""",

    'medical_advice': """You are a healthcare assistant providing medical advice based on patient records. Your task is to:
1. Review the patient's medical history, diagnosis, and current condition
2. Suggest appropriate lifestyle modifications, preventive measures, or general care advice
3. Provide evidence-based recommendations relevant to the patient's conditions
4. Use simple, non-technical language that patients can understand
5. Include disclaimers that this advice does not replace professional medical consultation
6. Be supportive and empathetic in your tone
7. Focus on general wellness and preventive advice
8. Only provide information that would be appropriate for a medical assistant (not a doctor)

IMPORTANT: Never suggest specific medications, dosages, or treatments that would require a doctor's prescription.
Always recommend the patient to consult with their doctor for specific treatment plans.

Please analyze the provided medical records and provide thoughtful advice tailored to this patient's situation."""
}

# Database schema
schema = """
schema:
"
-- Table: appointments
CREATE TABLE appointments (
  appointment_id bigint NOT NULL AUTO_INCREMENT,
  patient_id bigint NOT NULL,
  doctor_id bigint NOT NULL,
  date date NOT NULL,
  is_pending tinyint(1) NOT NULL,
  is_approved tinyint(1) NOT NULL DEFAULT '0',
  start_time time DEFAULT NULL,
  end_time time DEFAULT NULL,
  PRIMARY KEY (appointment_id),
  KEY patient_id (patient_id),
  KEY doctor_id (doctor_id),
  CONSTRAINT appointments_ibfk_1 FOREIGN KEY (patient_id) REFERENCES patient (patient_id),
  CONSTRAINT appointments_ibfk_2 FOREIGN KEY (doctor_id) REFERENCES doctor (doctor_id)
) 
-- Table: avalibility
CREATE TABLE avalibility (
  doctor_id bigint NOT NULL,
  Mon_startTime time DEFAULT NULL,
  Mon_endTime time DEFAULT NULL,
  Tue_startTime time DEFAULT NULL,
  Tue_endTime time DEFAULT NULL,
  Wed_startTime time DEFAULT NULL,
  Wed_endTime time DEFAULT NULL,
  Thu_startTime time DEFAULT NULL,
  Thu_endTime time DEFAULT NULL,
  Fri_startTime time DEFAULT NULL,
  Fri_endTime time DEFAULT NULL,
  Sat_startTime time DEFAULT NULL,
  Sat_endTime time DEFAULT NULL,
  Sun_startTime time DEFAULT NULL,
  Sun_endTime time DEFAULT NULL,
  PRIMARY KEY (doctor_id),
  CONSTRAINT avalibility_ibfk_1 FOREIGN KEY (doctor_id) REFERENCES doctor (doctor_id)
)
-- Table: department
CREATE TABLE department (
  department_id bigint NOT NULL AUTO_INCREMENT,
  name varchar(100) NOT NULL,
  PRIMARY KEY (department_id)
) 
-- Table: doctor
CREATE TABLE doctor (
  doctor_id bigint NOT NULL,
  specialization varchar(255) NOT NULL,
  PRIMARY KEY (doctor_id),
  CONSTRAINT doctor_ibfk_1 FOREIGN KEY (doctor_id) REFERENCES person (person_id)
) 
-- Table: inventory
CREATE TABLE inventory (
  inventory_id bigint NOT NULL AUTO_INCREMENT,
  name varchar(255) NOT NULL,
  quantity bigint NOT NULL,
  expiry_date date DEFAULT NULL,
  department_id bigint NOT NULL,
  PRIMARY KEY (inventory_id),
  KEY department_id (department_id),
  CONSTRAINT inventory_ibfk_1 FOREIGN KEY (department_id) REFERENCES department (department_id)
) 
-- Table: medical_records
CREATE TABLE medical_records (
  record_id bigint NOT NULL AUTO_INCREMENT,
  department_id bigint NOT NULL,
  patient_id bigint NOT NULL,
  treatement_id bigint NOT NULL,
  diagnosis varchar(255) NOT NULL,
  bloodpressure varchar(50) DEFAULT NULL,
  date date NOT NULL,
  PRIMARY KEY (record_id),
  KEY patient_id (patient_id),
  KEY department_id (department_id),
  KEY treatement_id (treatement_id),
  CONSTRAINT medical_records_ibfk_1 FOREIGN KEY (patient_id) REFERENCES patient (patient_id),
  CONSTRAINT medical_records_ibfk_2 FOREIGN KEY (department_id) REFERENCES department (department_id),
  CONSTRAINT medical_records_ibfk_3 FOREIGN KEY (treatement_id) REFERENCES treatement (treatement_id)
) 
-- Table: patient
CREATE TABLE patient (
  patient_id bigint NOT NULL,
  weight varchar(255) DEFAULT NULL,
  height varchar(255) DEFAULT NULL,
  PRIMARY KEY (patient_id),
  CONSTRAINT patient_ibfk_1 FOREIGN KEY (patient_id) REFERENCES person (person_id)
)
-- Table: person
CREATE TABLE person (
  person_id bigint NOT NULL AUTO_INCREMENT,
  image longblob,
  image_type varchar(50) DEFAULT NULL,
  name varchar(100) NOT NULL,
  gender varchar(10) DEFAULT NULL,
  age int DEFAULT NULL,
  birthdate date DEFAULT NULL,
  contact_info varchar(100) DEFAULT NULL,
  address varchar(255) DEFAULT NULL,
  PRIMARY KEY (person_id)
) 
-- Table: staff
CREATE TABLE staff (
  staff_id bigint NOT NULL,
  proffession varchar(255) NOT NULL,
  PRIMARY KEY (staff_id),
  CONSTRAINT staff_ibfk_1 FOREIGN KEY (staff_id) REFERENCES person (person_id)
) 
-- Table: treatement
CREATE TABLE treatement (
  treatement_id bigint NOT NULL AUTO_INCREMENT,
  name varchar(100) NOT NULL,
  doctor_id bigint NOT NULL,
  department_id bigint NOT NULL,
  PRIMARY KEY (treatement_id),
  KEY doctor_id (doctor_id),
  KEY department_id (department_id),
  CONSTRAINT treatement_ibfk_1 FOREIGN KEY (doctor_id) REFERENCES doctor (doctor_id),
  CONSTRAINT treatement_ibfk_2 FOREIGN KEY (department_id) REFERENCES department (department_id)
) 
-- Table: user_authentication
CREATE TABLE user_authentication (
  username varchar(255) NOT NULL,
  password varchar(255) NOT NULL,
  role varchar(50) NOT NULL,
  person_id bigint NOT NULL,
  PRIMARY KEY (person_id),
  UNIQUE KEY unique_username (username),
  CONSTRAINT fk_person_id FOREIGN KEY (person_id) REFERENCES person (person_id)
) 

"""