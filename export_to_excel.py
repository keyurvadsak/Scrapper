"""
Export scraped data to Excel format.
Creates one Excel file per website with overview and page sheets.
"""
import asyncio
import os
from pathlib import Path
from sqlalchemy import select
from Database.db import AsyncSessionLocal, init_db
from Database.models import Website, Page
from utils.structured_data import create_excel_workbook
from utils.logger_config import setup_logger

logger = setup_logger(__name__)


async def export_website_to_excel(website_id, output_dir="exports"):
    """
    Export a single website to Excel format.
    
    Args:
        website_id: ID of the website to export
        output_dir: Directory to save Excel files
    """
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    async with AsyncSessionLocal() as session:
        # Get website data
        website_result = await session.execute(
            select(Website).where(Website.id == website_id)
        )
        website = website_result.scalar_one_or_none()
        
        if not website:
            logger.error(f"Website with ID {website_id} not found")
            print(f"❌ Website with ID {website_id} not found")
            return None
        
        logger.info(f"Exporting website: {website.name} (ID: {website_id})")
        print(f"\n📊 Exporting website: {website.name}")
        
        # Get all pages for this website with their tags
        pages_result = await session.execute(
            select(Page).where(Page.website_id == website_id)
        )
        pages = pages_result.scalars().all()
        
        if not pages:
            logger.warning(f"No pages found for website ID {website_id}")
            print(f"⚠️  No pages found for this website")
            return None
        
        logger.info(f"Found {len(pages)} pages to export")
        print(f"   Found {len(pages)} pages")
        
        # Prepare data for Excel export
        website_data = {
            'name': website.name,
            'base_url': website.base_url
        }
        
        pages_data = []
        index = 1
        for page in pages:
            # Get tags for this page
            from Database.models import Tag
            tag_result = await session.execute(
                select(Tag).where(Tag.page_id == page.id)
            )
            tag = tag_result.scalar_one_or_none()
            
            # Prepare tags data
            tags_dict = {}
            if tag:
                # Convert JSONB columns to dict
                for tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li', 'th', 'td', 'a', 'img', 'video', 'audio']:
                    tag_value = getattr(tag, tag_name, None)
                    if tag_value:
                        tags_dict[tag_name] = tag_value
            
            pages_data.append({
                'name': page.name,
                'url': page.url,
                'title': page.title,
                'tags': tags_dict
            })
        
        # Create safe filename
        safe_filename = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in website.name)
        output_path = os.path.join(output_dir, f"{safe_filename}.xlsx")
        
        # Create Excel workbook
        create_excel_workbook(website_data, pages_data, output_path)
        
        print(f"✅ Exported to: {output_path}\n")
        return output_path


async def export_all_websites(output_dir="exports"):
    """
    Export all websites to Excel format.
    
    Args:
        output_dir: Directory to save Excel files
    """
    async with AsyncSessionLocal() as session:
        # Get all websites
        result = await session.execute(select(Website))
        websites = result.scalars().all()
        
        if not websites:
            logger.warning("No websites found in database")
            print("❌ No websites found in database")
            return
        
        logger.info(f"Found {len(websites)} websites to export")
        print(f"\n📊 Exporting {len(websites)} website(s)...\n")
        
        exported_count = 0
        for website in websites:
            result = await export_website_to_excel(website.id, output_dir)
            if result:
                exported_count += 1
        
        print(f"\n{'='*60}")
        print(f"✅ Export complete! {exported_count}/{len(websites)} websites exported")
        print(f"📁 Files saved to: {os.path.abspath(output_dir)}")
        print(f"{'='*60}\n")


async def main():
    """Main function with user menu."""
    await init_db()
    
    print("\n" + "="*60)
    print("📊 EXCEL EXPORT TOOL")
    print("="*60 + "\n")
    
    print("Choose an option:")
    print("  1. Export all websites")
    print("  2. Export specific website")
    
    choice = input("\nEnter your choice (1-2): ").strip()
    
    if choice == "1":
        await export_all_websites()
    elif choice == "2":
        # List available websites
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Website))
            websites = result.scalars().all()
            
            if not websites:
                print("❌ No websites found in database")
                return
            
            print("\nAvailable websites:")
            for website in websites:
                print(f"  {website.id}. {website.name} - {website.base_url}")
            
            website_id = input("\nEnter website ID to export: ").strip()
            
            try:
                website_id = int(website_id)
                await export_website_to_excel(website_id)
            except ValueError:
                print("❌ Invalid website ID")
    else:
        print("❌ Invalid choice")


if __name__ == "__main__":
    asyncio.run(main())
