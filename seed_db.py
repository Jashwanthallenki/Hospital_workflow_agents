import sqlite3
from contextlib import closing

def seed_db():
    try:
        with closing(sqlite3.connect('hospital.db')) as conn:
            c = conn.cursor()
            
            # Insert sample appointments
            sample_data = [
                ("John Doe", "Dr. Smith", "2025-03-25", "10:00 AM"),
                ("Jane Doe", "Dr. Brown", "2025-03-26", "02:30 PM"),
                ("Alice Johnson", "Dr. Green", "2025-03-27", "11:45 AM"),
                ("Bob Williams", "Dr. Adams", "2025-03-28", "04:15 PM"),
                ("Charlie Davis", "Dr. Smith", "2025-03-29", "09:00 AM")
            ]

            c.executemany("""
                INSERT INTO appointments (patient_name, doctor_name, date, time) 
                VALUES (?, ?, ?, ?)
            """, sample_data)
            
            conn.commit()
            print("Sample data inserted successfully.")
    
    except Exception as e:
        print(f"Error seeding database: {str(e)}")

# Run database seeding
if __name__ == "__main__":
    seed_db()
