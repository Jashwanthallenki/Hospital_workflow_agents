from flask import Flask, request, jsonify
import sqlite3
from contextlib import closing
from db import init_db
from flask_cors import CORS  # Import CORS

class AppointmentSchedulerAgent:
    def __init__(self):
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for all routes

        self.query = None
        self.intent = None
        self.entities = {}
        self.metadata = {}

        self.app.route('/schedule_appointment', methods=['POST'])(self.schedule_appointment)
        self.app.route('/health', methods=['GET'])(self.health_check)

    def health_check(self):
        return jsonify({"status": "ok", "service": "scheduler-agent"})

    def schedule_appointment(self):
        try:
            data = request.json
            if not data:
                return jsonify({'error': 'No data provided'}), 400
                
            self.query = data.get('query')
            self.intent = data.get('intent')
            self.entities = data.get('entities', {})
            self.metadata = data.get('metadata', {})

            patient_name = self.entities.get('patient_name')
            doctor_name = self.entities.get('doctor_name')
            date = self.entities.get('date')
            time = self.entities.get('time')
            
            missing_fields = []
            if not patient_name:
                missing_fields.append("patient name")
            if not doctor_name:
                missing_fields.append("doctor name")
            if not date:
                missing_fields.append("date")
            if not time:
                missing_fields.append("time")
                
            if missing_fields:
                return jsonify({
                    'response': f"I need more information to schedule the appointment. Missing: {', '.join(missing_fields)}"
                })

            with closing(sqlite3.connect('hospital.db')) as conn:
                c = conn.cursor()
                
                # Check if doctor is already booked at that time OR patient has another appointment with the same doctor on the same date
                c.execute("""
                    SELECT COUNT(*) FROM appointments 
                    WHERE (doctor_name = ? AND date = ? AND time = ?) 
                    OR (patient_name = ? AND doctor_name = ? AND date = ?)
                """, (doctor_name, date, time, patient_name, doctor_name, date))
                
                count = c.fetchone()[0]
                
                if count > 0:
                    return jsonify({
                        'response': f"Dr. {doctor_name} is already booked at {time}, or {patient_name} already has an appointment with Dr. {doctor_name} on {date}. Please choose another time."
                    })
                
                # Insert the appointment
                c.execute("""
                    INSERT INTO appointments (patient_name, doctor_name, date, time) 
                    VALUES (?, ?, ?, ?)
                """, (patient_name, doctor_name, date, time))
                conn.commit()

            return jsonify({
                'response': f"Great! I've scheduled an appointment for {patient_name} with Dr. {doctor_name} on {date} at {time}."
            })
            
        except Exception as e:
            print(f"Error scheduling appointment: {str(e)}")
            return jsonify({
                'error': f"Failed to schedule appointment: {str(e)}"
            }), 500


if __name__ == '__main__':
    print("Starting Scheduler Agent on http://localhost:5001...")
    init_db()  # Initialize the database
    scheduler = AppointmentSchedulerAgent()
    scheduler.app.run(port=5001, debug=True, threaded=True) 
