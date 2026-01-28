"""Web scraper for extracting content from primesandzooms.com."""

import asyncio
import requests
from bs4 import BeautifulSoup
from typing import List, Set, Dict, Any
from urllib.parse import urljoin, urlparse
from langchain.schema import Document


class WebScraper:
    """Scrapes content from websites for RAG ingestion."""
    
    def __init__(self, base_domain: str = "primesandzooms.com"):
        """Initialize scraper with base domain."""
        self.base_domain = base_domain
        self.visited_urls: Set[str] = set()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (compatible; PrimesAndZoomsBot/1.0)"
        }
    
    async def scrape_urls(self, urls: List[str], depth: int = 1) -> List[Document]:
        """Scrape content from URLs and optionally crawl linked pages.
        
        Args:
            urls: List of seed URLs to scrape
            depth: How many levels deep to crawl (1 = only seed URLs)
            
        Returns:
            List of LangChain Document objects
        """
        documents = []
        urls_to_process = [(url, 0) for url in urls]  # (url, current_depth)
        
        while urls_to_process:
            url, current_depth = urls_to_process.pop(0)
            
            if url in self.visited_urls:
                continue
            
            if current_depth > depth:
                continue
            
            self.visited_urls.add(url)
            
            # Scrape the page
            doc, links = await self._scrape_page(url)
            
            if doc:
                documents.append(doc)
            
            # Add discovered links for crawling
            if current_depth < depth:
                for link in links:
                    if link not in self.visited_urls:
                        urls_to_process.append((link, current_depth + 1))
        
        return documents
    
    async def _scrape_page(self, url: str) -> tuple[Document | None, List[str]]:
        """Scrape a single page.
        
        Args:
            url: URL to scrape
            
        Returns:
            Tuple of (Document or None, list of discovered URLs)
        """
        try:
            # Run sync request in thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.get(url, headers=self.headers, timeout=10)
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "lxml")
            
            # Extract title
            title = soup.title.string if soup.title else urlparse(url).path
            
            # Remove unwanted elements
            for element in soup.find_all(["script", "style", "nav", "footer", "header"]):
                element.decompose()
            
            # Extract main content
            main_content = soup.find("main") or soup.find("article") or soup.find("body")
            
            if main_content:
                text = main_content.get_text(separator="\n", strip=True)
            else:
                text = soup.get_text(separator="\n", strip=True)
            
            # Clean up text
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            cleaned_text = "\n".join(lines)
            
            # Skip very short pages
            if len(cleaned_text) < 100:
                return None, []
            
            # Create document
            doc = Document(
                page_content=cleaned_text,
                metadata={
                    "source": url,
                    "title": title,
                    "content_type": "webpage"
                }
            )
            
            # Extract links for crawling
            links = self._extract_links(soup, url)
            
            return doc, links
            
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return None, []
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract same-domain links from page."""
        links = []
        
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            
            # Convert relative URLs to absolute
            full_url = urljoin(base_url, href)
            parsed = urlparse(full_url)
            
            # Only include same-domain links
            if self.base_domain in parsed.netloc:
                # Clean URL (remove fragments, trailing slashes)
                clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")
                
                # Skip non-HTML resources
                if not any(clean_url.endswith(ext) for ext in [".pdf", ".jpg", ".png", ".gif", ".css", ".js"]):
                    links.append(clean_url)
        
        return list(set(links))