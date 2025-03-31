from flask import Flask, request, jsonify
from dotenv import load_dotenv
import requests
import os
import json
import google.generativeai as genai
from flask_cors import CORS  # Import CORS
from db import init_db

load_dotenv()
# Configure Google Gemini API using environment variable
genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))

class ParentAgent:
    def __init__(self):
        self.app = Flask(__name__)
        CORS(self.app, resources={r"/*": {"origins": "*"}})  # Enable CORS for all routes

        self.query = None
        self.intent = None
        self.entities = {}
        self.metadata = {}

        # Define routes
        self.app.add_url_rule('/process_query', 'process_query', self.process_query, methods=['POST', 'OPTIONS'])
        self.app.add_url_rule('/health', 'health_check', self.health_check, methods=['GET'])

    def health_check(self):
        return jsonify({"status": "ok", "service": "parent-agent"})

    def get_intent_and_entities(self, query):
        try:
            model = genai.GenerativeModel('gemini-2.0-pro-exp')
            prompt = f"""Analyze the following query for a hospital management system: '{query}'

            Determine the intent and extract relevant entities.

            Possible intents:
            - schedule_appointment
            - inquire_appointment
            - get_doctor_details

            For schedule_appointment, extract:
            - patient_name
            - doctor_name
            - date
            - time

            For inquire_appointment, extract:
            - patient_name

            For get_doctor_details, extract:
            - disease_name (Identify the disease from symptoms)
            - specilaist name (from the disease name identify which specialist can cure the disease like heart disesae can be cured by cardiolgist etc)
                available specialists :
                
                Cardiologist
                Dermatologist
                Neurologist
                Pediatrician
                Orthopedic
                General Physician

            Return the result in JSON format with keys 'intent' and 'entities'."""

            
            response = model.generate_content(prompt)
            response_text = response.text.strip()
            print(response_text)
            
            try:
                # Extract JSON from response
                json_str = response_text.split("```json")[-1].split("```")[0].strip() if "```json" in response_text else response_text
                result = json.loads(json_str)
                return result.get('intent', ''), result.get('entities', {})
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON from response: {response_text}")
                print(f"JSON error: {str(e)}")
                return '', {}
        except Exception as e:
            print(f"Error in intent recognition: {str(e)}")
            return '', {}

    def process_query(self):
        try:
            if request.method == "OPTIONS":
                return self.preflight_response()  # Handle preflight request

            data = request.json
            if not data or 'query' not in data:
                return jsonify({'error': 'Query is required'}), 400

            self.query = data.get('query', '')
            self.intent, self.entities = self.get_intent_and_entities(self.query)
            self.metadata = {'timestamp': data.get('timestamp', ''), 'user_id': data.get('user_id', '')}

            # Define child agent URL based on intent
            child_agent_url = None
            if self.intent == 'schedule_appointment':
                child_agent_url = 'http://localhost:5001/schedule_appointment'
            elif self.intent == 'inquire_appointment':
                child_agent_url = 'http://localhost:5002/inquire_appointment'
            elif self.intent == 'get_doctor_details':
                child_agent_url = 'http://localhost:5002/get_doctors'

            if not child_agent_url:
                return jsonify({'response': "I couldn't understand what you want to do. Please try asking about appointments or scheduling one."})

            payload = {
                'query': self.query,
                'intent': self.intent,
                'entities': self.entities,
                'metadata': self.metadata
            }

            try:
                response = requests.post(child_agent_url, json=payload, timeout=10)
                response.raise_for_status()
                return jsonify(response.json())
            except requests.RequestException as e:
                print(f"Error communicating with child agent: {str(e)}")
                return jsonify({'error': f"Internal communication error: {str(e)}"}), 500

        except Exception as e:
            print(f"Error processing query: {str(e)}")
            return jsonify({'error': f"Failed to process request: {str(e)}"}), 500

    def preflight_response(self):
        """Handles CORS preflight requests (OPTIONS)."""
        response = jsonify({'message': 'CORS preflight successful'})
        response.headers.add("Access-Control-Allow-Origin", "*")  # Allow all origins
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")  # Allowed methods
        response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")  # Allowed headers
        return response

if __name__ == '__main__':
    print("Starting Parent Agent on http://localhost:5000...")
    init_db()  # Initialize the database
    parent = ParentAgent()
    parent.app.run(host='0.0.0.0', port=5000, debug=True)
