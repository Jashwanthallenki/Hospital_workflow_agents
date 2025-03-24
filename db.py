import sqlite3
from contextlib import closing

def init_db():
    try:
        with closing(sqlite3.connect('hospital.db')) as conn:
            c = conn.cursor()
            
            # Create table if it doesn't exist
            c.execute('''CREATE TABLE IF NOT EXISTS appointments
                        (id INTEGER PRIMARY KEY, patient_name TEXT, doctor_name TEXT, date TEXT, time TEXT)''')
                        
            conn.commit()
            print("Database initialized.")
    except Exception as e:
        print(f"Database initialization error: {str(e)}")

# Run database initialization
if __name__ == "__main__":
    init_db()
