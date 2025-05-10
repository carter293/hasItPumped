"""
Database models and connection setup for the Solana Token Analysis API.
"""

import os
from pathlib import Path 
from dotenv import load_dotenv
from sqlalchemy import Boolean, Column, Date, Float, String, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base

# Load environment variables
load_dotenv()

# Get the absolute path to the assets directory
pkg_root = Path(__file__).parent.parent
assets_dir = pkg_root / 'assets'
assets_dir.mkdir(exist_ok=True)  # Ensure the assets directory exists

db_path = str(assets_dir / 'solana_tokens.db')

# Create absolute filepath for the database
DATABASE_URL = os.getenv(
    "DATABASE_URL", f"sqlite:///{db_path}"
)

print(f"Database will be created at: {db_path}")

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False}  # Needed for SQLite
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class TokenData(Base):
    """SQLAlchemy model for token price data"""

    __tablename__ = "token_data"

    id = Column(String, primary_key=True)  # composite key: mint_address + date
    mint_address = Column(String, index=True)
    date = Column(Date, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    created_at = Column(Date)
    is_pre_peak = Column(
        Boolean, nullable=True
    )  # True for pre_peak, False for post_peak


def init_db():
    """Initialize the database tables"""
    # Ensure the directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Verify the file was created
    if os.path.exists(db_path):
        print(f"Database file created at: {db_path}")
    else:
        print(f"WARNING: Database file not created at: {db_path}")


def get_db():
    """Dependency to get DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()