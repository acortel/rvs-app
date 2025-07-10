import os

def get_config():
    return {
        'CLIENT_ID': os.getenv('CLIENT_ID'),
        'CLIENT_SECRET': os.getenv('CLIENT_SECRET'),
        'BASE_URL': os.getenv('BASE_URL', 'https://ws.everify.gov.ph/api'),
        'POSTGRES_CONFIG': {
            'host': os.getenv('PGHOST', 'localhost'),
            'port': int(os.getenv('PGPORT', 5432)),
            'user': os.getenv('PGUSER', 'postgres'),
            'password': os.getenv('PGPASSWORD', ''),
            'dbname': os.getenv('PGDATABASE', 'rvs_db')
        }
    }
