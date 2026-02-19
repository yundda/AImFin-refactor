import MySQLdb
import os

HOST = "localhost"
PORT = 3306
USER = "root"
PASSWORD = "1234"
DB_NAME = "aim_fin"

def reset_database():
    try:
        conn = MySQLdb.connect(host=HOST, port=PORT, user=USER, passwd=PASSWORD)
        cursor = conn.cursor()
        
        print(f"Dropping database '{DB_NAME}' if exists...")
        cursor.execute(f"DROP DATABASE IF EXISTS {DB_NAME};")
        
        print(f"Creating database '{DB_NAME}'...")
        cursor.execute(f"CREATE DATABASE {DB_NAME} CHARACTER SET utf8mb4;")
        
        print("Database reset complete.")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    reset_database()
