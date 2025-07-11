# eVerify Python SDK

A modular Python package for integrating eVerify functionality into Python desktop applications.

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
export CLIENT_ID="your_client_id"
export CLIENT_SECRET="your_client_secret"
export PGHOST="localhost"
export PGPORT="5432"
export PGUSER="postgres"
export PGPASSWORD="your_password"
export PGDATABASE="rvs_db"
```

## Quick Start

```python
from everify import EVerifyClient, EVerifyDB, validate_config

# Validate configuration
config = validate_config()

# Initialize client
client = EVerifyClient(
    client_id=config['CLIENT_ID'],
    client_secret=config['CLIENT_SECRET']
)

# Verify a person
result = client.verify_person({
    "first_name": "JANE",
    "last_name": "DOE",
    "birth_date": "1990-01-01"
})

# Store verification in database
db = EVerifyDB()
db.store_verification(person_data)
```

## Features

- **Person Verification**: Verify individuals using personal information
- **QR Code Verification**: Verify using QR codes
- **Face Liveness Check**: Integrate with face verification (requires liveness server)
- **Database Integration**: Store and retrieve verification records
- **Error Handling**: Comprehensive error handling and logging

## Usage Examples

See `example_usage.py` for complete examples.

## Configuration

The package uses environment variables for configuration. See `config.py` for details. 