from flask import Flask, request, jsonify
import sqlite3
from contextlib import closing
import datetime  # Import datetime module

class AppointmentInquirerAgent:
    def __init__(self):
        self.app = Flask(__name__)
        self.query = None
        self.intent = None
        self.entities = {}
        self.metadata = {}

        self.app.route('/inquire_appointment', methods=['POST'])(self.inquire_appointment)
        self.app.route('/get_doctors', methods=['POST'])(self.get_doctors)
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

    def get_doctors(self):
        try:
            data = request.json
            if not data:
                return jsonify({'error': 'No data provided'}), 400

            self.query = data.get('query')
            self.intent = data.get('intent')
            self.entities = data.get('entities', {})
            self.metadata = data.get('metadata', {})

            specialty = self.entities.get('specialist_name')  # Fix the key to match the input

            # Get current date to filter availability
            current_date = datetime.datetime.now().date()  # Use datetime.datetime.now()

            with closing(sqlite3.connect('hospital.db')) as conn:
                c = conn.cursor()

                if specialty:
                    c.execute("""
                        SELECT d.name, d.specialty, a.available_date, a.available_time 
                        FROM doctors d
                        JOIN availability a ON d.name = a.doctor_name
                        WHERE d.specialty = ? AND a.available_date >= ?
                        """, (specialty, current_date))
                else:
                    c.execute("""
                        SELECT d.name, d.specialty, a.available_date, a.available_time 
                        FROM doctors d
                        JOIN availability a ON d.name = a.doctor_name
                        WHERE a.available_date >= ?
                        """, (current_date,))

                doctors = c.fetchall()

            if doctors:
                response = "Here are the available doctors:\n"
                for doc in doctors:
                    response += f"- Dr. {doc[0]} ({doc[1]}) available on {doc[2]} at {doc[3]}\n"
            else:
                response = "No doctors found."

            return jsonify({'response': response})

        except Exception as e:
            print(f"Error retrieving doctor details: {str(e)}")
            return jsonify({
                'error': f"Failed to retrieve doctor details: {str(e)}"
            }), 500

if __name__ == '__main__':
    print("Starting Inquirer Agent on http://localhost:5002...")
    inquirer = AppointmentInquirerAgent()
    inquirer.app.run(port=5002, debug=True, threaded=True)
