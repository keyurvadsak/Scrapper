import asyncio
import time
from playwright.async_api import async_playwright
from urllib.parse import urlparse
from Database.db import AsyncSessionLocal
from Database.helper_functions import save_page, save_tag, get_all_links
from config import DEFAULT_TAGS
from utils.logger_config import setup_logger

logger = setup_logger(__name__)

def extract_name(url: str) -> str:
    path = urlparse(url).path.strip("/")
    return path.split("/")[-1] if path else "home"


async def extract_tags_from_page(page, tags: list[str]) -> dict:
    """
    Extract tags from a Playwright page and return formatted data.
    
    Args:
        page: Playwright page object
        tags: List of HTML tags to extract
        
    Returns:
        Dictionary with tag data formatted by tag type
    """
    tags_data = {}
    text_only_tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'th', 'td', 'li']
    link_tags = ['a']
    media_tags = ['img', 'audio', 'video']
    
    for tag in tags:
        elements = await page.locator(tag).evaluate_all("""
            els => els.map(el => ({
                text: el.textContent?.trim() || null,
                href: el.getAttribute?.("href"),
                src: el.getAttribute?.("src"),
                alt: el.getAttribute?.("alt")
            }))
        """)

        # Format data based on tag type
        formatted_data = {}
        
        if tag in text_only_tags:
            for idx, el in enumerate(elements, 1):
                formatted_data[str(idx)] = el["text"]
        
        elif tag in link_tags:
            for idx, el in enumerate(elements, 1):
                formatted_data[str(idx)] = {
                    "text": el["text"],
                    "href": el["href"]
                }
        
        elif tag in media_tags:
            for idx, el in enumerate(elements, 1):
                formatted_data[str(idx)] = {
                    "alt": el["alt"],
                    "src": el["src"]
                }

        tags_data[tag] = formatted_data
        logger.debug(f"Extracted {len(elements)} <{tag}> tags")

    return tags_data


async def scrape_tags(urls: list[str] | None = None, tags: list[str] | None = None, website_id: int | None = None):

    tags = tags or DEFAULT_TAGS  # fallback to default tags
    logger.info(f"Starting tag scraping - Tags: {tags}, Website ID: {website_id}")

    async with AsyncSessionLocal() as session:
        # decide which URLs to scrape
        if urls:
            # urls already provided
            logger.info(f"Using provided URLs: {len(urls)} pages")
            pass
        else:
            # fetch all links from database for this website
            if website_id is None:
                logger.error("website_id is required when urls are not provided")
                raise ValueError("website_id is required when urls are not provided")
            urls = await get_all_links(session, website_id)
            logger.info(f"Retrieved {len(urls)} URLs from database for website_id: {website_id}")

    start_time = time.time()  # Start timing
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        )
        page = await browser.new_page()

        try:
            for idx, current_url in enumerate(urls, 1):
                logger.info(f"Scraping page {idx}/{len(urls)}: {current_url}")
                print(f"🔍 Scraping {current_url}")

                try:
                    await page.goto(
                        current_url,
                        wait_until="domcontentloaded",
                        timeout=80000
                    )
                    logger.debug(f"Page loaded successfully: {current_url}")
                except Exception as e:
                    logger.error(f"Failed to load {current_url}: {e}")
                    print(f"❌ Failed to load {current_url}: {e}")
                    continue

                title = await page.title()
                name = extract_name(current_url)
                logger.debug(f"Page title: '{title}', Name: '{name}'")

                async with AsyncSessionLocal() as session:
                    page_id = await save_page(session, name, current_url, title, website_id)
                    logger.debug(f"Saved page to database - ID: {page_id}")

                    # Extract tags using the helper function
                    tags_data = await extract_tags_from_page(page, tags)
                    
                    # Count total elements
                    total_elements = sum(len(tag_elements) for tag_elements in tags_data.values())
                    logger.info(f"Extracted {total_elements} total elements from {current_url}")

                    # Save all tags at once
                    await save_tag(session, page_id, tags_data)
                    await session.commit()
                    logger.info(f"Tags saved for page_id: {page_id}")
                    print(f"✅ Saved {total_elements} tags for {current_url}")

        finally:
            logger.info("Closing browser")
            print("🔒 Closing browser")
            await browser.close()
            
    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.info(f"Tag scraping completed in {elapsed_time:.2f} seconds")
    print(f"\n⏱️  Tag scraping completed in {elapsed_time:.2f} seconds")
    return elapsed_time
