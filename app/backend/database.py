import psycopg2 # Use the PostgreSQL adapter
from psycopg2 import Error
import os
from dotenv import load_dotenv

# Load your existing environment variables
load_dotenv()

def get_db_connection():
    """
    Establishes a connection to the PostgreSQL database on System A
    using its local IP address.
    """
    try:
        connection = psycopg2.connect(
            # Read from environment variables for Render deployment, fallback to local settings
            host=os.getenv("DB_HOST", "192.168.1.6"), 
            
            # Your PostgreSQL credentials
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "12345"),
            database=os.getenv("DB_NAME", "sevenext"),
            port=int(os.getenv("DB_PORT", 5432)),
            
            # Optional: Prevents the app from hanging if the network is down
            connect_timeout=10 
        )
        
        # Test if the connection is successful
        if connection:
            print("Successfully connected to the Office PostgreSQL database!")
            return connection
            
    except Error as e:
        print(f"Database connection error: {e}")
        print("Tip: Ensure System A Firewall allows Port 5432 and pg_hba.conf is updated.")
        raise Exception("Failed to connect to the database")

# Test the connection when running this file directly
if __name__ == "__main__":
    get_db_connection()