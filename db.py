import sqlite3
from contextlib import closing

def init_db():
    try:
        with closing(sqlite3.connect('hospital.db')) as conn:
            c = conn.cursor()
            
            # Create table if it doesn't exist
            c.execute('''CREATE TABLE IF NOT EXISTS appointments
                        (id INTEGER PRIMARY KEY, patient_name TEXT, doctor_name TEXT, date TEXT, time TEXT)''')
            
            # Insert random data
            sample_data = [
                ('John Doe', 'Dr. Smith', '2025-04-10', '10:00 AM'),
                ('Alice Brown', 'Dr. Johnson', '2025-04-11', '02:30 PM'),
                ('Bob White', 'Dr. Taylor', '2025-04-12', '11:15 AM'),
                ('Emma Wilson', 'Dr. Lee', '2025-04-13', '04:45 PM'),
                ('Michael Green', 'Dr. Adams', '2025-04-14', '09:00 AM')
            ]
            
            c.executemany('''INSERT INTO appointments (patient_name, doctor_name, date, time) 
                             VALUES (?, ?, ?, ?)''', sample_data)
            
            conn.commit()
            print("Database initialized with sample data.")
    except Exception as e:
        print(f"Database initialization error: {str(e)}")

# Run database initialization
if __name__ == "__main__":
    init_db()
