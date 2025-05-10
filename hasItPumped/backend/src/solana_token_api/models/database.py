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

# Get database URL from environment or use default
pkg_root = Path(__file__).parent.parent
db_path = str(pkg_root / 'assets' / 'solana_tokens.db')

DATABASE_URL = os.getenv(
    "DATABASE_URL", f"sqlite:///{db_path}"
)
engine = create_engine(DATABASE_URL)

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
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency to get DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
