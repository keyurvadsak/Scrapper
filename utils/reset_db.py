"""
Script to drop and recreate all database tables.
Use this when you need to apply schema changes.
"""
import asyncio
from Database.db import engine, Base
from Database.models import Website, Links, Page, Tag
from logger_config import setup_logger

logger = setup_logger(__name__)

async def reset_database():
    """Drop all tables and recreate them with the current schema."""
    logger.info("Starting database reset...")
    print("\n⚠️  WARNING: This will delete ALL data in the database!")
    confirm = input("Are you sure you want to continue? (yes/no): ").strip().lower()
    
    if confirm != "yes":
        print("❌ Database reset cancelled.")
        return
    
    async with engine.begin() as conn:
        # Drop all tables
        logger.info("Dropping all tables...")
        print("\n🗑️  Dropping all tables...")
        await conn.run_sync(Base.metadata.drop_all)
        logger.info("All tables dropped successfully")
        print("✅ All tables dropped successfully")
        
        # Recreate all tables
        logger.info("Creating all tables with new schema...")
        print("\n🔨 Creating all tables with new schema...")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("All tables created successfully")
        print("✅ All tables created successfully")
    
    print("\n✅ Database reset complete!")
    print("   You can now run the scraper with the new schema.\n")
    logger.info("Database reset complete")

if __name__ == "__main__":
    asyncio.run(reset_database())
