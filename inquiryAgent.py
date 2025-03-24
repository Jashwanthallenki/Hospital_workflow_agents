from flask import Flask, request, jsonify
import sqlite3
from contextlib import closing
from db import init_db

class AppointmentInquirerAgent:
    def __init__(self):
        self.app = Flask(__name__)
        self.query = None
        self.intent = None
        self.entities = {}
        self.metadata = {}
        self.app.route('/inquire_appointment', methods=['POST'])(self.inquire_appointment)
        self.app.route('/health', methods=['GET'])(self.health_check)

    def health_check(self):
        return jsonify({"status": "ok", "service": "inquirer-agent"})

    def inquire_appointment(self):
        try:
            data = request.json
            if not data:
                return jsonify({'error': 'No data provided'}), 400
                
            self.query = data.get('query')
            self.intent = data.get('intent')
            self.entities = data.get('entities', {})
            self.metadata = data.get('metadata', {})

            patient_name = self.entities.get('patient_name')
            if not patient_name:
                return jsonify({
                    'response': "I need to know which patient's appointments you're asking about."
                })

            with closing(sqlite3.connect('hospital.db')) as conn:
                c = conn.cursor()
                c.execute("SELECT * FROM appointments WHERE patient_name = ? ORDER BY date, time", (patient_name,))
                appointments = c.fetchall()

            if appointments:
                if len(appointments) == 1:
                    appt = appointments[0]
                    response = f"{patient_name} has an appointment with Dr. {appt[2]} on {appt[3]} at {appt[4]}."
                else:
                    response = f"{patient_name} has the following appointments:\n"
                    for i, appt in enumerate(appointments, 1):
                        response += f"{i}. With Dr. {appt[2]} on {appt[3]} at {appt[4]}\n"
            else:
                response = f"No appointments found for {patient_name}."

            return jsonify({'response': response})
            
        except Exception as e:
            print(f"Error inquiring appointment: {str(e)}")
            return jsonify({
                'error': f"Failed to retrieve appointment information: {str(e)}"
            }), 500

if __name__ == '__main__':
    print("Starting Inquirer Agent on http://localhost:5002...")
    init_db()  # Initialize the database
    inquirer = AppointmentInquirerAgent()
    inquirer.app.run(port=5002, debug=True, threaded=True)