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

def validate_config():
    """Validate that required configuration is present."""
    config = get_config()
    missing = []
    
    if not config['CLIENT_ID']:
        missing.append('CLIENT_ID')
    if not config['CLIENT_SECRET']:
        missing.append('CLIENT_SECRET')
    
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    return config
