from typing import List, Dict, Any
import httpx
from bs4 import BeautifulSoup
from datetime import datetime
import hashlib

from ..config.settings import settings

class ConfluenceService:
    def __init__(self):
        self.base_url = str(settings.CONFLUENCE_URL)
        self.space = settings.CONFLUENCE_SPACE
        self.client = httpx.Client(timeout=30.0)
    
    def _generate_doc_id(self, page_id: str) -> str:
        """Generate a unique document ID."""
        return f"confluence_{page_id}"
    
    def _clean_html(self, html: str) -> str:
        """Clean HTML content and extract text."""
        soup = BeautifulSoup(html, 'html.parser')
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        # Get text
        text = soup.get_text()
        # Break into lines and remove leading/trailing space
        lines = (line.strip() for line in text.splitlines())
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # Drop blank lines
        text = ' '.join(chunk for chunk in chunks if chunk)
        return text
    
    async def fetch_pages(self) -> List[Dict[str, Any]]:
        """Fetch all pages from the Confluence space."""
        pages = []
        start = 0
        limit = 25
        
        while True:
            # Get page list
            response = await self.client.get(
                f"{self.base_url}/rest/api/content",
                params={
                    "spaceKey": self.space,
                    "start": start,
                    "limit": limit,
                    "expand": "version"
                }
            )
            response.raise_for_status()
            data = response.json()
            
            # Process pages
            for page in data["results"]:
                # Get page content
                content_response = await self.client.get(
                    f"{self.base_url}/rest/api/content/{page['id']}",
                    params={"expand": "body.storage"}
                )
                content_response.raise_for_status()
                content_data = content_response.json()
                
                # Clean and process content
                content = self._clean_html(content_data["body"]["storage"]["value"])
                
                # Create document
                doc = {
                    "id": self._generate_doc_id(page["id"]),
                    "content": content,
                    "source_type": "confluence",
                    "source_id": page["id"],
                    "title": page["title"],
                    "url": f"{self.base_url}{page['_links']['webui']}",
                    "last_updated": content_data["version"]["when"]
                }
                pages.append(doc)
            
            # Check if there are more pages
            if len(data["results"]) < limit:
                break
            start += limit
        
        return pages
    
    async def fetch_single_page(self, page_id: str) -> Dict[str, Any]:
        """Fetch a single page from Confluence."""
        # Get page content
        response = await self.client.get(
            f"{self.base_url}/rest/api/content/{page_id}",
            params={"expand": "body.storage,version"}
        )
        response.raise_for_status()
        data = response.json()
        
        # Clean and process content
        content = self._clean_html(data["body"]["storage"]["value"])
        
        # Create document
        doc = {
            "id": self._generate_doc_id(page_id),
            "content": content,
            "source_type": "confluence",
            "source_id": page_id,
            "title": data["title"],
            "url": f"{self.base_url}{data['_links']['webui']}",
            "last_updated": data["version"]["when"]
        }
        
        return doc
    
    async def search_pages(self, query: str) -> List[Dict[str, Any]]:
        """Search pages in Confluence."""
        response = await self.client.get(
            f"{self.base_url}/rest/api/content",
            params={
                "spaceKey": self.space,
                "cql": f"text ~ '{query}'",
                "expand": "version"
            }
        )
        response.raise_for_status()
        data = response.json()
        
        pages = []
        for page in data["results"]:
            doc = await self.fetch_single_page(page["id"])
            pages.append(doc)
        
        return pages 