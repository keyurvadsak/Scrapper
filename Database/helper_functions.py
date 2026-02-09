from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from Database.models import Links, Page, Tag, Website
from utils.logger_config import setup_logger

logger = setup_logger(__name__)

async def save_website(session, base_url, name):
    """Create or get existing website record."""
    logger.debug(f"Saving website - Base URL: {base_url}, Name: {name}")
    stmt = (
        insert(Website)
        .values(base_url=base_url, name=name)
        .on_conflict_do_update(
            index_elements=[Website.base_url],
            set_={"name": name}
        )
        .returning(Website.id)
    )
    result = await session.execute(stmt)
    website_id = result.scalar_one()
    logger.info(f"Website saved/retrieved - ID: {website_id}")
    return website_id

async def save_link(session, url, website_id):
    logger.debug(f"Saving link: {url} for website_id: {website_id}")
    stmt = insert(Links).values(url=url, website_id=website_id).on_conflict_do_nothing()
    await session.execute(stmt)

async def save_page(session, name, url, title, website_id):
    logger.debug(f"Saving page - Name: {name}, URL: {url}, Website ID: {website_id}")
    stmt = (
        insert(Page)
        .values(name=name, url=url, title=title, website_id=website_id)
        .on_conflict_do_update(
            index_elements=[Page.url],
            set_={"title": title, "website_id": website_id}
        )
        .returning(Page.id)
    )

    result = await session.execute(stmt)
    page_id = result.scalar_one()
    logger.debug(f"Page saved - ID: {page_id}")
    return page_id

async def save_tag(session, page_id, tags_data):
    """
    Save tags for a page using JSONB columns.
    
    Args:
        session: Database session
        page_id: ID of the page
        tags_data: Dictionary with tag types as keys and lists of tag data as values
                   Example: {
                       "h1": [{"text": "Heading 1"}],
                       "p": [{"text": "Paragraph text"}],
                       "img": [{"src": "image.jpg", "alt": "Image"}],
                       ...
                   }
    """
    logger.debug(f"Saving tags for page_id: {page_id}")
    
    # Prepare values for JSONB columns
    tag_values = {
        "page_id": page_id,
        "h1": tags_data.get("h1"),
        "h2": tags_data.get("h2"),
        "h3": tags_data.get("h3"),
        "h4": tags_data.get("h4"),
        "h5": tags_data.get("h5"),
        "h6": tags_data.get("h6"),
        "p": tags_data.get("p"),
        "th": tags_data.get("th"),
        "td": tags_data.get("td"),
        "li": tags_data.get("li"),
        "a": tags_data.get("a"),
        "img": tags_data.get("img"),
        "audio": tags_data.get("audio"),
        "video": tags_data.get("video"),
    }
    
    stmt = (
        insert(Tag)
        .values(**tag_values)
    )
    await session.execute(stmt)
    logger.info(f"Tags saved for page_id: {page_id}")


async def get_all_links(session, website_id):
    logger.debug(f"Retrieving all links for website_id: {website_id}")
    result = await session.execute(
        select(Links.url).where(Links.website_id == website_id)
    )
    links = [row[0] for row in result.all()]
    logger.info(f"Retrieved {len(links)} links for website_id: {website_id}")
    return links

