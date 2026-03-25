"""
Script to import Romanian postal codes from SQL file into MongoDB
Source: https://github.com/romania/localitati

Usage:
    python scripts/import_postal_codes.py
"""

import re
import sys
import os
import asyncio
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# SQL Insert pattern
INSERT_PATTERN = re.compile(
    r"\((\d+),\s*'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)'\)"
)

def parse_sql_file(sql_content):
    """Parse SQL file and extract postal code records"""
    records = []
    
    # Find all INSERT statements
    for match in INSERT_PATTERN.finditer(sql_content):
        record = {
            'id': int(match.group(1)),
            'judet': match.group(2).strip(),
            'localitate': match.group(3).strip(),
            'tip_artera': match.group(4).strip() if match.group(4) else None,
            'denumire_artera': match.group(5).strip() if match.group(5) else None,
            'numar_bloc': match.group(6).strip() if match.group(6) else None,
            'cod_postal': match.group(7).strip()
        }
        records.append(record)
    
    return records

def normalize_judet(judet):
    """Normalize county name for matching"""
    # Remove diacritics and normalize
    replacements = {
        'ş': 's', 'Ş': 'S', 'ș': 's', 'Ș': 'S',
        'ţ': 't', 'Ţ': 'T', 'ț': 't', 'Ț': 'T',
        'ă': 'a', 'Ă': 'A',
        'â': 'a', 'Â': 'A',
        'î': 'i', 'Î': 'I'
    }
    
    result = judet
    for old, new in replacements.items():
        result = result.replace(old, new)
    
    return result.upper()

def normalize_localitate(localitate):
    """Normalize locality name for matching"""
    # Remove text in parentheses, normalize diacritics
    result = re.sub(r'\([^)]*\)', '', localitate).strip()
    
    replacements = {
        'ş': 's', 'Ş': 'S', 'ș': 's', 'Ș': 'S',
        'ţ': 't', 'Ţ': 'T', 'ț': 't', 'Ț': 'T',
        'ă': 'a', 'Ă': 'A',
        'â': 'a', 'Â': 'A',
        'î': 'i', 'Î': 'I'
    }
    
    for old, new in replacements.items():
        result = result.replace(old, new)
    
    return result.upper()

async def import_postal_codes():
    """Import postal codes into MongoDB"""
    
    # Connect to MongoDB
    mongo_url = os.environ.get('MONGO_URL')
    db_name = os.environ.get('DB_NAME', 'mfirme_app')
    
    if not mongo_url:
        print("ERROR: MONGO_URL not set in environment")
        return
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print(f"Connected to MongoDB: {db_name}")
    
    # Fetch SQL from GitHub
    import aiohttp
    
    sql_url = "https://raw.githubusercontent.com/romania/localitati/refs/heads/master/coduri_postale.sql"
    
    print(f"Fetching SQL from: {sql_url}")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(sql_url) as response:
            if response.status != 200:
                print(f"ERROR: Failed to fetch SQL file: {response.status}")
                return
            sql_content = await response.text()
    
    print(f"Fetched SQL file: {len(sql_content)} bytes")
    
    # Parse SQL
    records = parse_sql_file(sql_content)
    print(f"Parsed {len(records)} postal code records")
    
    if not records:
        print("ERROR: No records found in SQL file")
        return
    
    # Add normalized fields for matching
    for record in records:
        record['judet_normalized'] = normalize_judet(record['judet'])
        record['localitate_normalized'] = normalize_localitate(record['localitate'])
    
    # Drop existing collection and create new one
    await db.postal_codes.drop()
    print("Dropped existing postal_codes collection")
    
    # Insert records in batches
    batch_size = 1000
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        await db.postal_codes.insert_many(batch)
        print(f"Inserted batch {i // batch_size + 1}: {len(batch)} records")
    
    # Create indexes for fast lookup
    await db.postal_codes.create_index("cod_postal")
    await db.postal_codes.create_index("judet")
    await db.postal_codes.create_index("localitate")
    await db.postal_codes.create_index("judet_normalized")
    await db.postal_codes.create_index("localitate_normalized")
    await db.postal_codes.create_index([("judet_normalized", 1), ("localitate_normalized", 1)])
    
    print("Created indexes")
    
    # Create aggregated locality lookup collection
    # This groups postal codes by locality for easier matching
    pipeline = [
        {
            "$group": {
                "_id": {
                    "judet": "$judet",
                    "judet_normalized": "$judet_normalized",
                    "localitate": "$localitate",
                    "localitate_normalized": "$localitate_normalized"
                },
                "postal_codes": {"$addToSet": "$cod_postal"},
                "count": {"$sum": 1}
            }
        },
        {
            "$project": {
                "_id": 0,
                "judet": "$_id.judet",
                "judet_normalized": "$_id.judet_normalized",
                "localitate": "$_id.localitate",
                "localitate_normalized": "$_id.localitate_normalized",
                "postal_codes": 1,
                "postal_code_count": "$count",
                "primary_postal_code": {"$arrayElemAt": ["$postal_codes", 0]}
            }
        }
    ]
    
    await db.localities.drop()
    
    localities = await db.postal_codes.aggregate(pipeline).to_list(length=None)
    
    if localities:
        await db.localities.insert_many(localities)
        print(f"Created localities collection with {len(localities)} unique localities")
        
        # Create indexes on localities
        await db.localities.create_index([("judet_normalized", 1), ("localitate_normalized", 1)])
        await db.localities.create_index("localitate_normalized")
        await db.localities.create_index("judet")
    
    # Print summary
    print("\n=== Import Complete ===")
    print(f"Total postal codes: {len(records)}")
    print(f"Unique localities: {len(localities)}")
    
    # Sample data
    sample = await db.postal_codes.find_one({"judet": "București"})
    if sample:
        print(f"\nSample record (București):")
        print(f"  Localitate: {sample.get('localitate')}")
        print(f"  Cod postal: {sample.get('cod_postal')}")
    
    client.close()
    print("\nDone!")

if __name__ == "__main__":
    asyncio.run(import_postal_codes())
