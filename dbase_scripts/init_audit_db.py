import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from db_config import POSTGRES_CONFIG

def init_audit_db():
    # First connect to PostgreSQL server to create database if it doesn't exist
    conn = psycopg2.connect(
        host=POSTGRES_CONFIG['host'],
        user=POSTGRES_CONFIG['user'],
        password=POSTGRES_CONFIG['password']
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    # Create database if it doesn't exist
    try:
        cursor.execute("CREATE DATABASE rvs_dbase")
        print("Database 'rvs_dbase' created successfully")
    except psycopg2.errors.DuplicateDatabase:
        print("Database 'rvs_dbase' already exists")
    finally:
        cursor.close()
        conn.close()

    # Now connect to the rvs_dbase database to create table
    conn = psycopg2.connect(**POSTGRES_CONFIG)
    cursor = conn.cursor()

    # Create audit_log table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_log (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) NOT NULL,
            action VARCHAR(255) NOT NULL,
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create index on username and timestamp for faster queries
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_audit_username 
        ON audit_log(username)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_audit_timestamp 
        ON audit_log(timestamp)
    ''')

    conn.commit()
    print("Audit log table and indexes created successfully")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    init_audit_db() 