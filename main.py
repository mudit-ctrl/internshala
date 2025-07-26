import requests
from bs4 import BeautifulSoup
import time
import csv
import json
from urllib.parse import urljoin, urlparse
import re
from datetime import datetime

class Earth911Scraper:
    def __init__(self):
        self.base_url = "https://search.earth911.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.scraped_data = []
    
    def get_page_content(self, url, retries=3, delay=1):
        """Fetch page content with retry logic"""
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                print(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < retries - 1:
                    time.sleep(delay * (attempt + 1))
                else:
                    print(f"Failed to fetch {url} after {retries} attempts")
                    return None
    
    def extract_main_page_links(self, main_url):
        """Extract all href links from the main search results page"""
        print(f"Fetching main page: {main_url}")
        content = self.get_page_content(main_url)
        
        if not content:
            return []
        
        soup = BeautifulSoup(content, 'html.parser')
        links = []
        
        # Find all result items (both odd and even, programs and locations)
        result_items = soup.find_all('li', class_=re.compile(r'result-item\s+(program|location)\s+(odd|even)'))
        
        for item in result_items:
            # Find the main title link
            title_link = item.find('h2', class_='title')
            if title_link:
                link_tag = title_link.find('a')
                if link_tag and link_tag.get('href'):
                    full_url = urljoin(self.base_url, link_tag.get('href'))
                    links.append(full_url)
        
        print(f"Found {len(links)} links on this page")
        return links
    
    def get_all_search_pages(self, base_url):
        """Get links from all paginated search result pages"""
        all_links = []
        current_page = 1
        
        while True:
            print(f"\n--- Processing search results page {current_page} ---")
            
            # Construct URL for current page
            if current_page == 1:
                page_url = base_url
            else:
                separator = '&' if '?' in base_url else '?'
                page_url = f"{base_url}{separator}page={current_page}"
            
            # Get content for current page
            content = self.get_page_content(page_url)
            if not content:
                print(f"Failed to get content for page {current_page}")
                break
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract links from current page
            page_links = self.extract_main_page_links(page_url)
            
            if not page_links:
                print(f"No links found on page {current_page}, stopping pagination")
                break
            
            all_links.extend(page_links)
            
            # Check if there's a next page
            pager = soup.find('div', class_='pager')
            next_link = None
            
            if pager:
                next_link = pager.find('a', class_='next')
                
            if not next_link:
                print(f"No next page found, pagination complete")
                break
            
            current_page += 1
            
            # Add a small delay between page requests
            time.sleep(1)
        
        print(f"\nTotal links found across all pages: {len(all_links)}")
        return all_links
    
    def parse_date(self, date_text):
        """Parse date from text like 'Updated May 15, 2013' to '2013-5-15' format"""
        if not date_text:
            return ""
        
        # Remove 'Updated' prefix and clean text
        cleaned_date = re.sub(r'^Updated\s*', '', date_text.strip())
        
        # Common date patterns
        patterns = [
            r'(\w+)\s+(\d{1,2}),?\s+(\d{4})',  # May 15, 2013 or May 15 2013
            r'(\d{1,2})/(\d{1,2})/(\d{4})',    # 5/15/2013
            r'(\d{4})-(\d{1,2})-(\d{1,2})',    # 2013-5-15
            r'(\d{1,2})-(\d{1,2})-(\d{4})',    # 5-15-2013
        ]
        
        months = {
            'january': 1, 'jan': 1, 'february': 2, 'feb': 2, 'march': 3, 'mar': 3,
            'april': 4, 'apr': 4, 'may': 5, 'june': 6, 'jun': 6,
            'july': 7, 'jul': 7, 'august': 8, 'aug': 8, 'september': 9, 'sep': 9,
            'october': 10, 'oct': 10, 'november': 11, 'nov': 11, 'december': 12, 'dec': 12
        }
        
        for pattern in patterns:
            match = re.search(pattern, cleaned_date, re.IGNORECASE)
            if match:
                groups = match.groups()
                
                if len(groups) == 3:
                    if pattern == patterns[0]:  # Month name pattern
                        month_name, day, year = groups
                        month = months.get(month_name.lower())
                        if month:
                            return f"{year}-{month}-{day}"
                    elif pattern == patterns[1]:  # MM/DD/YYYY
                        month, day, year = groups
                        return f"{year}-{month}-{day}"
                    elif pattern == patterns[2]:  # YYYY-MM-DD (already correct)
                        return cleaned_date
                    elif pattern == patterns[3]:  # MM-DD-YYYY
                        month, day, year = groups
                        return f"{year}-{month}-{day}"
        
        return cleaned_date  # Return as-is if no pattern matches
    
    def clean_text(self, text):
        """Clean and normalize text"""
        if not text:
            return ""
        # Remove special characters and normalize whitespace
        cleaned = re.sub(r'\s+', ' ', text.strip())
        # Remove weird unicode characters
        cleaned = re.sub(r'[^\x20-\x7E]', '', cleaned)
        return cleaned
    
    def format_full_address(self, street_address, city_state_zip):
        """Combine street address with city, state, zip for full address"""
        parts = []
        if street_address:
            parts.append(street_address)
        if city_state_zip:
            parts.append(city_state_zip)
        return ', '.join(parts)
    
    def extract_materials_from_table(self, soup):
        """Extract materials from the materials table"""
        materials = []
        
        # Look for materials table
        materials_table = soup.find('table', class_='materials-accepted')
        if materials_table:
            rows = materials_table.find_all('tr')
            for row in rows:
                if 'label' not in row.get('class', []):  # Skip header row
                    material_cell = row.find('td', class_='material-name')
                    if material_cell:
                        material_span = material_cell.find('span')
                        if material_span:
                            material_text = self.clean_text(material_span.get_text())
                            if material_text:
                                materials.append(material_text)
        
        # Also look for materials in the main listing format (from search results)
        if not materials:
            materials_section = soup.find('p', class_='result-materials')
            if materials_section:
                material_spans = materials_section.find_all('span', class_=['matched material no-link', 'material no-link'])
                for span in material_spans:
                    material_text = self.clean_text(span.get_text())
                    if material_text and material_text != "Materials accepted:":
                        materials.append(material_text)
        
        return materials
    
    def extract_detail_page_data(self, url):
        """Extract data from individual detail page"""
        print(f"Scraping: {url}")
        content = self.get_page_content(url)
        
        if not content:
            return None
        
        soup = BeautifulSoup(content, 'html.parser')
        data = {
            'Business_Name': '',
            'last_update_date': '',
            'street_address': '',
            'materials_accepted': []
        }
        
        # Extract business name and last update date from h1
        back_to_header = soup.find('h1', class_='back-to')
        if back_to_header:
            # Business name is the first text node
            business_name_text = back_to_header.contents[0] if back_to_header.contents else ""
            data['Business_Name'] = self.clean_text(str(business_name_text))
            
            # Last update date from span
            last_verified = back_to_header.find('span', class_='last-verified')
            if last_verified:
                raw_date = self.clean_text(last_verified.get_text())
                data['last_update_date'] = self.parse_date(raw_date)
        
        # If no back-to header, try to get name from title
        if not data['Business_Name']:
            title_h2 = soup.find('h2', class_='title')
            if title_h2:
                title_link = title_h2.find('a')
                if title_link:
                    data['Business_Name'] = self.clean_text(title_link.get_text())
        
        # Extract contact information from masthead for full address
        street_address = ""
        city_state_zip = ""
        
        masthead = soup.find('div', class_='masthead')
        if masthead:
            contact_div = masthead.find('div', class_='contact')
            if contact_div:
                # Address lines
                addr_lines = contact_div.find_all('p', class_='addr')
                address_parts = []
                for addr_p in addr_lines:
                    addr_text = self.clean_text(addr_p.get_text())
                    if addr_text:
                        address_parts.append(addr_text)
                
                if len(address_parts) >= 2:
                    street_address = address_parts[0]
                    city_state_zip = address_parts[1]
                elif len(address_parts) == 1:
                    # Assume it's city, state, zip if no street address
                    city_state_zip = address_parts[0]
        
        # Format full address
        data['street_address'] = self.format_full_address(street_address, city_state_zip)
        
        # Extract materials accepted
        data['materials_accepted'] = self.extract_materials_from_table(soup)
        
        return data
    
    def scrape_all_pages(self, main_url, delay_between_requests=2):
        """Scrape all pages from the main URL and all pagination pages"""
        print("=== Starting Earth911 Electronics Recycling Scraper ===")
        
        # Get all links from all paginated search result pages
        all_links = self.get_all_search_pages(main_url)
        
        if not all_links:
            print("No links found to scrape!")
            return []
        
        print(f"\n=== Starting to scrape {len(all_links)} detail pages ===")
        
        for i, link in enumerate(all_links, 1):
            print(f"Progress: {i}/{len(all_links)} - {(i/len(all_links)*100):.1f}%")
            
            data = self.extract_detail_page_data(link)
            if data:
                self.scraped_data.append(data)
                print(f"  ✓ Successfully scraped: {data['Business_Name']}")
            else:
                print(f"  ✗ Failed to scrape: {link}")
            
            # Be respectful with delays
            if i < len(all_links):  # Don't delay after the last request
                time.sleep(delay_between_requests)
        
        print(f"\n=== Scraping completed! ===")
        print(f"Successfully collected {len(self.scraped_data)} records out of {len(all_links)} attempted.")
        return self.scraped_data
    
    def save_to_csv(self, filename='earth911_electronics_recycling.csv'):
        """Save scraped data to CSV file with only required columns"""
        if not self.scraped_data:
            print("No data to save")
            return
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Business_Name', 'last_update_date', 'street_address', 'materials_accepted']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for row in self.scraped_data:
                # Convert materials list to semicolon-separated string
                row_copy = row.copy()
                if isinstance(row['materials_accepted'], list):
                    row_copy['materials_accepted'] = '; '.join(row['materials_accepted'])
                else:
                    row_copy['materials_accepted'] = str(row['materials_accepted'])
                writer.writerow(row_copy)
        
        print(f"Data saved to {filename}")
    
    def save_to_json(self, filename='earth911_electronics_recycling.json'):
        """Save scraped data to JSON file with only required fields"""
        if not self.scraped_data:
            print("No data to save")
            return
        
        # Create clean data with only required fields
        clean_data = []
        for item in self.scraped_data:
            clean_item = {
                'Business_Name': item['Business_Name'],
                'last_update_date': item['last_update_date'],
                'street_address': item['street_address'],
                'materials_accepted': item['materials_accepted']
            }
            clean_data.append(clean_item)
        
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(clean_data, jsonfile, indent=2, ensure_ascii=False)
        
        print(f"Data saved to {filename}")

# Usage example
if __name__ == "__main__":
    scraper = Earth911Scraper()
    
    # Your main URL
    main_url = "https://search.earth911.com/?what=Electronics&where=10001&list_filter=all&max_distance=100&family_id=&latitude=&longitude=&country=&province=&city=&sponsor="
    
    # Scrape ALL pages and ALL links (this will take a while!)
    data = scraper.scrape_all_pages(main_url, delay_between_requests=2)
    
    # Save results
    scraper.save_to_csv()
    scraper.save_to_json()
    
    # Print detailed summary
    print(f"\n=== FINAL SUMMARY ===")
    print(f"Total records scraped: {len(data)}")
    
    if data:
        print(f"\nSample record:")
        for key, value in data[0].items():
            if key == 'materials_accepted' and isinstance(value, list):
                print(f"  {key}: {len(value)} materials - {value[:3]}{'...' if len(value) > 3 else ''}")
            else:
                print(f"  {key}: {str(value)[:100]}{'...' if len(str(value)) > 100 else ''}")
        
        # Print business types summary
        business_names = [item['Business_Name'] for item in data if item['Business_Name']]
        print(f"\nBusiness names found: {len(business_names)}")
        for i, name in enumerate(business_names[:10], 1):
            print(f"  {i}. {name}")
        if len(business_names) > 10:
            print(f"  ... and {len(business_names) - 10} more")
    
    print(f"\nFiles saved:")
    print(f"  - earth911_electronics_recycling.csv")
    print(f"  - earth911_electronics_recycling.json")