import requests
from bs4 import BeautifulSoup
import logging
import time
import re
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Any, Set
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class WebScraper:
    """Web scraper for extracting content from MOSDAC portal and similar sites"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.visited_urls = set()
        self.delay_between_requests = 1  # Respectful crawling
        
    def scrape_website(self, base_url: str, max_pages: int = 50, 
                      depth_limit: int = 2) -> List[Dict[str, Any]]:
        """Scrape website content starting from base URL"""
        try:
            logger.info(f"Starting scrape of {base_url}")
            
            scraped_data = []
            urls_to_visit = [(base_url, 0)]  # (url, depth)
            
            while urls_to_visit and len(scraped_data) < max_pages:
                current_url, depth = urls_to_visit.pop(0)
                
                if current_url in self.visited_urls or depth > depth_limit:
                    continue
                
                logger.info(f"Scraping: {current_url} (depth: {depth})")
                
                page_data = self.scrape_page(current_url)
                if page_data:
                    scraped_data.append(page_data)
                    
                    # Find new URLs to visit
                    if depth < depth_limit:
                        new_urls = self._extract_links(page_data.get('html', ''), current_url)
                        for new_url in new_urls:
                            if new_url not in self.visited_urls:
                                urls_to_visit.append((new_url, depth + 1))
                
                self.visited_urls.add(current_url)
                time.sleep(self.delay_between_requests)
            
            logger.info(f"Scraping completed. Collected {len(scraped_data)} pages")
            return scraped_data
            
        except Exception as e:
            logger.error(f"Error scraping website: {str(e)}")
            return []
    
    def scrape_page(self, url: str) -> Dict[str, Any]:
        """Scrape content from a single page"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract metadata
            title = self._extract_title(soup)
            description = self._extract_description(soup)
            keywords = self._extract_keywords(soup)
            
            # Extract main content
            content = self._extract_main_content(soup)
            
            # Extract structured data
            structured_data = self._extract_structured_data(soup)
            
            # Classify page type
            page_type = self._classify_page_type(url, title, content)
            
            return {
                'url': url,
                'title': title,
                'description': description,
                'content': content,
                'keywords': keywords,
                'page_type': page_type,
                'structured_data': structured_data,
                'scraped_at': datetime.now().isoformat(),
                'html': str(soup)  # Store for link extraction
            }
            
        except Exception as e:
            logger.error(f"Error scraping page {url}: {str(e)}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title"""
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()
        
        # Fallback to h1
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text().strip()
        
        return "Untitled"
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract page description"""
        # Try meta description first
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content'].strip()
        
        # Try Open Graph description
        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        if og_desc and og_desc.get('content'):
            return og_desc['content'].strip()
        
        # Fallback to first paragraph
        first_p = soup.find('p')
        if first_p:
            text = first_p.get_text().strip()
            return text[:200] + "..." if len(text) > 200 else text
        
        return ""
    
    def _extract_keywords(self, soup: BeautifulSoup) -> List[str]:
        """Extract keywords from page"""
        keywords = []
        
        # Try meta keywords
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords and meta_keywords.get('content'):
            keywords.extend([k.strip() for k in meta_keywords['content'].split(',')])
        
        # Extract from headers
        for header in soup.find_all(['h1', 'h2', 'h3']):
            text = header.get_text().strip()
            if text:
                # Simple keyword extraction from headers
                words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
                keywords.extend(words)
        
        # Extract domain-specific terms
        content = soup.get_text().lower()
        satellite_terms = [
            'satellite', 'data', 'download', 'ocean', 'land', 'atmospheric',
            'oceansat', 'resourcesat', 'insat', 'modis', 'landsat',
            'ndvi', 'sst', 'chlorophyll', 'precipitation', 'temperature'
        ]
        
        for term in satellite_terms:
            if term in content:
                keywords.append(term)
        
        # Remove duplicates and return
        return list(set(keywords))[:20]  # Limit to 20 keywords
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main text content from page"""
        # Remove script and style elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer']):
            element.decompose()
        
        # Try to find main content areas
        main_selectors = [
            'main', 'article', '.content', '#content',
            '.main-content', '#main-content', '.post-content'
        ]
        
        for selector in main_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                return main_content.get_text(separator=' ', strip=True)
        
        # Fallback to body content
        body = soup.find('body')
        if body:
            return body.get_text(separator=' ', strip=True)
        
        return soup.get_text(separator=' ', strip=True)
    
    def _extract_structured_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract structured data like JSON-LD, microdata, etc."""
        structured_data = {}
        
        # Extract JSON-LD
        json_ld_scripts = soup.find_all('script', {'type': 'application/ld+json'})
        for script in json_ld_scripts:
            try:
                data = json.loads(script.get_text())
                structured_data['json_ld'] = data
                break
            except json.JSONDecodeError:
                continue
        
        # Extract tables as structured data
        tables = soup.find_all('table')
        if tables:
            table_data = []
            for table in tables[:3]:  # Limit to first 3 tables
                rows = []
                for row in table.find_all('tr')[:10]:  # Limit rows
                    cells = [cell.get_text().strip() for cell in row.find_all(['td', 'th'])]
                    if cells:
                        rows.append(cells)
                if rows:
                    table_data.append(rows)
            structured_data['tables'] = table_data
        
        # Extract lists
        lists = soup.find_all(['ul', 'ol'])
        if lists:
            list_data = []
            for list_elem in lists[:5]:  # Limit to first 5 lists
                items = [li.get_text().strip() for li in list_elem.find_all('li')[:10]]
                if items:
                    list_data.append(items)
            structured_data['lists'] = list_data
        
        return structured_data
    
    def _classify_page_type(self, url: str, title: str, content: str) -> str:
        """Classify the type of page based on URL, title, and content"""
        url_lower = url.lower()
        title_lower = title.lower()
        content_lower = content.lower()
        
        # FAQ page
        if any(term in url_lower for term in ['faq', 'help', 'support']):
            return 'faq'
        
        if any(term in title_lower for term in ['faq', 'frequently asked', 'help']):
            return 'faq'
        
        # Documentation page
        if any(term in url_lower for term in ['doc', 'guide', 'manual', 'tutorial']):
            return 'documentation'
        
        if any(term in title_lower for term in ['guide', 'manual', 'documentation']):
            return 'documentation'
        
        # Data/product page
        if any(term in url_lower for term in ['data', 'product', 'dataset', 'download']):
            return 'data_product'
        
        if any(term in content_lower for term in ['download', 'dataset', 'data product']):
            return 'data_product'
        
        # News/announcement page
        if any(term in url_lower for term in ['news', 'announcement', 'press']):
            return 'news'
        
        # Home page
        if url_lower.endswith('.gov.in/') or url_lower.endswith('.gov.in'):
            return 'homepage'
        
        # Contact page
        if any(term in url_lower for term in ['contact', 'about']):
            return 'contact'
        
        return 'general'
    
    def _extract_links(self, html: str, base_url: str) -> List[str]:
        """Extract relevant internal links from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        base_domain = urlparse(base_url).netloc
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(base_url, href)
            
            # Only include links from the same domain
            if urlparse(full_url).netloc == base_domain:
                # Skip certain file types and fragments
                if not any(full_url.lower().endswith(ext) for ext in ['.pdf', '.jpg', '.png', '.gif', '.zip']):
                    if '#' not in full_url:  # Skip anchor links
                        links.append(full_url)
        
        return list(set(links))[:20]  # Limit and deduplicate
    
    def scrape_specific_content(self, url: str, selectors: Dict[str, str]) -> Dict[str, Any]:
        """Scrape specific content using CSS selectors"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            extracted_data = {}
            
            for field_name, selector in selectors.items():
                elements = soup.select(selector)
                if elements:
                    if len(elements) == 1:
                        extracted_data[field_name] = elements[0].get_text().strip()
                    else:
                        extracted_data[field_name] = [el.get_text().strip() for el in elements]
                else:
                    extracted_data[field_name] = None
            
            return extracted_data
            
        except Exception as e:
            logger.error(f"Error scraping specific content from {url}: {str(e)}")
            return {}
    
    def get_robots_txt(self, base_url: str) -> Dict[str, Any]:
        """Check robots.txt for crawling guidelines"""
        try:
            robots_url = urljoin(base_url, '/robots.txt')
            response = self.session.get(robots_url, timeout=5)
            
            if response.status_code == 200:
                return {
                    'exists': True,
                    'content': response.text,
                    'crawl_delay': self._extract_crawl_delay(response.text)
                }
            else:
                return {'exists': False, 'content': '', 'crawl_delay': 1}
                
        except Exception as e:
            logger.warning(f"Could not fetch robots.txt: {str(e)}")
            return {'exists': False, 'content': '', 'crawl_delay': 1}
    
    def _extract_crawl_delay(self, robots_content: str) -> int:
        """Extract crawl delay from robots.txt"""
        for line in robots_content.split('\n'):
            if line.lower().startswith('crawl-delay:'):
                try:
                    delay = int(line.split(':')[1].strip())
                    return max(delay, 1)  # Minimum 1 second
                except ValueError:
                    pass
        return 1  # Default delay