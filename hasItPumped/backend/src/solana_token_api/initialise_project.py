import os
import json
import argparse
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import sys

# Get the absolute path to the root of the project
project_root = Path(__file__).parent.parent.parent.absolute()

# Add src to the Python path
sys.path.insert(0, str(project_root / 'src'))

from solana_token_api.models.database import init_db, SessionLocal, TokenData
from solana_token_api.utils.logger import setup_logger

# Ensure assets directory exists
assets_dir = project_root / 'src' / 'solana_token_api' / 'assets'
assets_dir.mkdir(exist_ok=True)

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Setup script for Solana Token Analysis API")
    parser.add_argument(
        "--data-file", 
        type=str,
        default=str(project_root / "data" / "ohlcv_data.json"),
        help="Path to the JSON data file to load (default: data/ohlcv_data.json)"
    )
    parser.add_argument(
        "--recreate-db",
        action="store_true",
        help="Drop and recreate all database tables"
    )
    return parser.parse_args()

def load_existing_data(data_file, logger):
    """Load token data from a JSON file"""
    data_path = Path(data_file)
    if not data_path.exists():
        logger.error(f"File {data_file} not found")
        # Try alternative locations
        alt_paths = [
            project_root / "data" / "ohlcv_data.json",
            project_root / "backend" / "data" / "ohlcv_data.json"
        ]
        
        for alt_path in alt_paths:
            if alt_path.exists():
                logger.info(f"Found data file at alternative location: {alt_path}")
                data_path = alt_path
                break
        else:
            return 0
    
    logger.info(f"Loading data from {data_path}")
    
    try:
        with open(data_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse {data_path} as JSON")
        return 0
    except Exception as e:
        logger.error(f"Error reading {data_path}: {str(e)}")
        return 0
    
    # Create database session
    db = SessionLocal()
    
    try:
        count = 0
        for item in data:
            mint_address = item.get("mint_address")
            date_str = item.get("date")
            
            if not mint_address or not date_str:
                logger.warning("Skipping record with missing mint_address or date")
                continue
                
            try:
                date_obj = datetime.strptime(date_str.split('T')[0], "%Y-%m-%d").date()
            except ValueError:
                logger.warning(f"Skipping record with invalid date: {date_str}")
                continue
            
            # Check if record already exists
            record_id = f"{mint_address}_{date_str}"
            existing = db.query(TokenData).filter_by(id=record_id).first()
            
            if not existing:
                # Create new record
                try:
                    db_record = TokenData(
                        id=record_id,
                        mint_address=mint_address,
                        date=date_obj,
                        open=float(item.get("open", 0)),
                        high=float(item.get("high", 0)),
                        low=float(item.get("low", 0)),
                        close=float(item.get("close", 0)),
                        volume=float(item.get("volume", 0)),
                        created_at=datetime.strptime(
                            item.get("created_at", date_str.split('T')[0]), 
                            "%Y-%m-%d"
                        ).date()
                    )
                    db.add(db_record)
                    count += 1
                except Exception as e:
                    logger.warning(f"Error processing record: {str(e)}")
        
        db.commit()
        logger.info(f"Successfully loaded {count} records")
        return count
        
    except Exception as e:
        logger.error(f"Error during database import: {str(e)}")
        db.rollback()
        return 0
        
    finally:
        db.close()

# This section only runs when this file is executed directly
if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Create logs directory if it doesn't exist
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Set up logging
    logger = setup_logger("setup")
    
    # Parse arguments
    args = parse_args()
    
    # Print current working directory and database path for debugging
    logger.info(f"Current working directory: {os.getcwd()}")
    
    # Import database module to get path
    from solana_token_api.models.database import db_path
    logger.info(f"Database will be created at: {db_path}")
    
    # Initialize the database
    logger.info("Initializing database")
    init_db()
    logger.info("Database initialized successfully")
    
    # Verify the database was created
    db_file = Path(db_path.replace('sqlite:///', ''))
    if db_file.exists():
        logger.info(f"Verified database file exists at: {db_file}")
    else:
        logger.warning(f"Database file not found at expected location: {db_file}")
    
    # Load data if specified
    if args.data_file:
        count = load_existing_data(args.data_file, logger)
        if count > 0:
            logger.info(f"Successfully imported {count} records from {args.data_file}")
        else:
            logger.warning("No records were imported")
    
    logger.info("Setup completed successfully")