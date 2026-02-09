import asyncio
import time
from urllib.parse import urlparse

from Database.db import init_db, AsyncSessionLocal
from Database.helper_functions import get_all_links, save_website
from Scrapers.link_scraper import scrape_links
from Scrapers.tags_scraper import scrape_tags
from config import DEFAULT_TAGS
from utils.logger_config import setup_logger

logger = setup_logger(__name__)


def get_user_input():
    """Interactive CLI to gather user input for scraping."""
    
    logger.info("Starting interactive mode for user input")
    
    print("\n" + "="*60)
    print("🕷️  WEB SCRAPER - Interactive Mode")
    print("="*60)
    print("\nChoose a scraping mode:\n")
    print("  1️⃣  Scrape WHOLE WEBSITE with default tags")
    print("     → Provide: base_url only")
    print("     → Scrapes: All pages with default tags\n")
    
    print("  2️⃣  Scrape ALL PAGES with CUSTOM TAGS")
    print("     → Provide: base_url + custom tags")
    print("     → Scrapes: All pages with your specified tags\n")
    
    print("  3️⃣  Scrape SPECIFIC PAGE with CUSTOM TAGS")
    print("     → Provide: specific URL + custom tags")
    print("     → Scrapes: Only that page with your specified tags\n")
    
    print("="*60)
    
    # Get mode selection
    while True:
        mode = input("\n👉 Enter mode (1, 2, or 3): ").strip()
        if mode in ["1", "2", "3"]:
            break
        print("❌ Invalid choice. Please enter 1, 2, or 3.")
    
    print()
    
    # Mode 1: Whole website with default tags
    if mode == "1":
        base_url = input("🌐 Enter base URL (e.g., http://example.com): ").strip()
        if not base_url:
            raise ValueError("❌ Base URL cannot be empty")
        
        print(f"\n✅ Mode: Scrape whole website")
        print(f"   Base URL: {base_url}")
        print(f"   Tags: {', '.join(DEFAULT_TAGS)} (default)")
        
        logger.info(f"Mode 1 selected - Base URL: {base_url}, Tags: {DEFAULT_TAGS}")
        
        return {
            "base_url": base_url,
            "url": None,
            "tags": DEFAULT_TAGS
        }
    
    # Mode 2: All pages with custom tags
    elif mode == "2":
        base_url = input("🌐 Enter base URL (e.g., http://example.com): ").strip()
        if not base_url:
            raise ValueError("❌ Base URL cannot be empty")
        
        tags_input = input("🏷️  Enter tags (comma-separated, e.g., h1, p, a): ").strip()
        if not tags_input:
            raise ValueError("❌ Tags cannot be empty")
        
        tags = [tag.strip() for tag in tags_input.split(",")]
        
        print(f"\n✅ Mode: Scrape all pages with custom tags")
        print(f"   Base URL: {base_url}")
        print(f"   Tags: {', '.join(tags)}")
        
        logger.info(f"Mode 2 selected - Base URL: {base_url}, Tags: {tags}")
        
        return {
            "base_url": base_url,
            "url": None,
            "tags": tags
        }
    
    # Mode 3: Specific page with custom tags
    else:  # mode == "3"
        url = input("🔗 Enter specific page URL: ").strip()
        if not url:
            raise ValueError("❌ URL cannot be empty")
        
        tags_input = input("🏷️  Enter tags (comma-separated, e.g., h1, p, a): ").strip()
        if not tags_input:
            raise ValueError("❌ Tags cannot be empty")
        
        tags = [tag.strip() for tag in tags_input.split(",")]
        
        print(f"\n✅ Mode: Scrape specific page with custom tags")
        print(f"   URL: {url}")
        print(f"   Tags: {', '.join(tags)}")
        
        logger.info(f"Mode 3 selected - URL: {url}, Tags: {tags}")
        
        return {
            "base_url": None,
            "url": url,
            "tags": tags
        }


async def main():
    """Main function to orchestrate the scraping process."""
    
    logger.info("="*60)
    logger.info("Web Scraper Application Started")
    logger.info("="*60)
    
    # Initialize database
    await init_db()  # FIX: Added await
    logger.info("Database initialized successfully")
    
    # Get user input
    try:
        config = get_user_input()
    except ValueError as e:
        logger.error(f"Invalid user input: {e}")
        print(f"\n{e}")
        return
    except KeyboardInterrupt:
        logger.warning("Scraping cancelled by user (KeyboardInterrupt)")
        print("\n\n❌ Scraping cancelled by user.")
        return
    
    base_url = config["base_url"]
    url = config["url"]
    tags = config["tags"]
    
    logger.info(f"Configuration - Base URL: {base_url}, URL: {url}, Tags: {tags}")
    
    print("\n" + "="*60)
    print("🚀 Starting scraper...")
    print("="*60 + "\n")
    
    try:
        # ------------------------
        # CASE 1: Specific page
        # ------------------------
        if url:
            logger.info("Starting Mode 1: Specific page scraping")
            print("🎯 Scraping single page\n")
            
            process_start_time = time.time()
            
            # Extract base_url from the specific page URL
            parsed = urlparse(url)
            base_url_extracted = f"{parsed.scheme}://{parsed.netloc}"
            website_name = parsed.netloc or "unknown"
            
            # Create website record
            async with AsyncSessionLocal() as session:
                website_id = await save_website(session, base_url_extracted, website_name)
                await session.commit()
                print(f"📝 Website ID: {website_id} for {base_url_extracted}\n")
            
            await scrape_tags(urls=[url], tags=tags, website_id=website_id)
            
            process_end_time = time.time()
            total_time = process_end_time - process_start_time
            
            logger.info(f"Mode 1 completed successfully - Total time: {total_time:.2f}s")
            print("\n" + "="*60)
            print("✅ Scraping complete!")
            print(f"⏱️  Total process time: {total_time:.2f} seconds")
            print("="*60)
            return
        
        # ------------------------
        # CASE 2 & 3: Whole website
        # ------------------------
        if base_url:
            logger.info("Starting Mode 2/3: Whole website scraping with combined link and tag scraping")
            process_start_time = time.time()
            
            print("🌐 Crawling website and scraping tags in one pass...\n")
            
            # Combined link and tag scraping
            website_id = await scrape_links(base_url, tags)
            
            process_end_time = time.time()
            total_time = process_end_time - process_start_time
            
            logger.info(f"Mode 2/3 completed successfully - Total: {total_time:.2f}s")
            print("\n" + "="*60)
            print("✅ Scraping complete!")
            print(f"\n⏱️  Total time: {total_time:.2f} seconds")
            print("="*60)
            return
        
        raise ValueError("❌ You must provide either base_url or url")
    
    except Exception as e:
        logger.critical(f"Critical error in main: {e}", exc_info=True)
        print(f"\n❌ Error during scraping: {e}")
        raise

if __name__ == "__main__":
    logger.info("Application entry point")
    asyncio.run(main())
    logger.info("Application finished")
