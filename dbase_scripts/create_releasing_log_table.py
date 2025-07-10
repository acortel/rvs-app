import psycopg2
from db_config import POSTGRES_CONFIG

def create_releasing_log_table():
    """Create the releasing_log table in the database."""
    
    # SQL command to create the table
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS releasing_log (
        id SERIAL PRIMARY KEY,
        doc_owner TEXT NOT NULL,
        doc_type TEXT NOT NULL,
        copy_no INTEGER NOT NULL,
        received_by TEXT NOT NULL,
        released_by TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    conn = None
    try:
        # Connect to the database
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cur = conn.cursor()
        
        # Create the table
        cur.execute(create_table_sql)
        
        # Commit the changes
        conn.commit()
        
        print("Successfully created releasing_log table!")
        
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error creating table: {error}")
    finally:
        if conn is not None:
            conn.close()

if __name__ == "__main__":
    create_releasing_log_table() 