import time
import asyncio
import random
from urllib.parse import urlparse

from playwright.async_api import async_playwright
from Database.db import AsyncSessionLocal
from Database.helper_functions import (
    save_link,
    save_website,
    save_page,
    save_tag,
)
from Scrapers.tags_scraper import extract_tags_from_page
from utils.logger_config import setup_logger

logger = setup_logger(__name__)

# ---------------- CONFIG ----------------
WORKERS = 5

DELAY_RANGE = (2.8, 5.0)
# ---------------------------------------


def extract_name(url: str) -> str:
    """Extract page name from URL."""
    path = urlparse(url).path.strip("/")
    return path.split("/")[-1] if path else "home"


async def launch_browser(playwright):
    logger.info("🌐 Launching browser (no proxy)")
    return await playwright.chromium.launch(headless=False)


async def worker(playwright, queue, visited, base_url, website_id, tags):
    browser = await launch_browser(playwright)
    page = await browser.new_page()

    # ---- Anti-bot headers ----
    await page.set_extra_http_headers({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/121.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;q=0.9,"
            "image/webp,*/*;q=0.8"
        ),
        "Referer": "https://www.google.com/",
    })

    # Hide webdriver flag
    await page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)

    async with AsyncSessionLocal() as session:
        while True:
            url = await queue.get()
            try:
                if url is None:
                    break

                if url in visited:
                    continue
                
                if url.endswith(("#",".jpg", ".jpeg", ".png", ".gif", ".svg", ".pdf", ".zip", ".mp4", ".mp3", ".avi", ".wmv", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".exe", ".dmg", ".iso", ".tar", ".gz", ".rar", ".7z", ".css", ".js", ".json", ".xml", ".rss", ".atom", ".woff", ".woff2", ".ttf", ".eot", ".ico")):
                    continue
                visited.add(url)
                logger.info(f"🔗 Visiting: {url}")

                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=50000)
                    await asyncio.sleep(random.uniform(*DELAY_RANGE))
                except Exception as e:
                    logger.error(f"❌ Page load failed: {url} | {e}")
                    continue

                title = await page.title()
                name = extract_name(url)

                await save_link(session, url, website_id)
                page_id = await save_page(session, name, url, title, website_id)

                tags_data = await extract_tags_from_page(page, tags)
                await save_tag(session, page_id, tags_data)
                await session.commit()

                links = await page.locator("a").evaluate_all(
                    "els => els.map(el => el.href)"
                )

                for link in links:
                    if link and link.startswith(base_url) and link not in visited and not link.endswith(("#",".jpg", ".jpeg", ".png", ".gif", ".svg", ".pdf", ".zip", ".mp4", ".mp3", ".avi", ".wmv", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".exe", ".dmg", ".iso", ".tar", ".gz", ".rar", ".7z", ".css", ".js", ".json", ".xml", ".rss", ".atom", ".woff", ".woff2", ".ttf", ".eot", ".ico")):
                        await queue.put(link)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Unexpected error on {url}: {e}", exc_info=True)
            finally:
                queue.task_done()

    await browser.close()


async def scrape_links(base_url, tags):
    """Main function to start full website scraping."""

    logger.info(f"🚀 Starting scraping for: {base_url}")

    async with AsyncSessionLocal() as session:
        parsed = urlparse(base_url)
        website_name = parsed.netloc or "unknown"

        website_id = await save_website(session, base_url, website_name)
        await session.commit()

        logger.info(f"📝 Website ID: {website_id}")

    queue = asyncio.Queue()
    visited = set()

    await queue.put(base_url)

    async with async_playwright() as p:
        start_time = time.time()

        tasks = [
            asyncio.create_task(
                worker(p, queue, visited, base_url, website_id, tags)
            )
            for _ in range(WORKERS)
        ]

        await queue.join()

        for task in tasks:
            task.cancel()

        elapsed = time.time() - start_time

        logger.info(f"✅ Scraping completed: {len(visited)} pages in {elapsed:.2f}s")
        print(f"✅ Scraped {len(visited)} pages in {elapsed:.2f} seconds")

        return website_id
