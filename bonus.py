from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import time
import csv
import json
import re

class BestBuyStoreLocatorScraper:
    def __init__(self, headless=True):
        """Initialize the scraper with Chrome WebDriver"""
        self.base_url = "https://www.bestbuy.com/site/store-locator"
        self.driver = None
        self.scraped_data = []
        self.setup_driver(headless)
    
    def setup_driver(self, headless=True):
        """Setup Chrome WebDriver with appropriate options"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            print("Chrome WebDriver initialized successfully")
        except Exception as e:
            print(f"Failed to initialize Chrome WebDriver: {e}")
            print("Please make sure ChromeDriver is installed and in your PATH")
            raise
    
    def search_stores_by_zipcode(self, zipcode="10001"):
        """Navigate to Best Buy store locator and search by zip code"""
        try:
            print(f"Navigating to {self.base_url}")
            self.driver.get(self.base_url)
            
            # Wait for the page to load
            time.sleep(3)
            
            # Find the zip code input field (try multiple selectors)
            zip_input = None
            selectors = [
                "input[placeholder*='ZIP']",
                "input[placeholder*='City']", 
                "input[aria-label*='Enter city']",
                ".zip-code-input",
                "input[data-cy='ZipCodeInputComponent']",
                "input[type='text'][placeholder]"
            ]
            
            for selector in selectors:
                try:
                    zip_input = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    print(f"Found input field using selector: {selector}")
                    break
                except:
                    continue
            
            if not zip_input:
                print("Could not find zip code input field. Available inputs:")
                inputs = self.driver.find_elements(By.TAG_NAME, "input")
                for i, inp in enumerate(inputs):
                    print(f"  Input {i}: placeholder='{inp.get_attribute('placeholder')}', id='{inp.get_attribute('id')}', class='{inp.get_attribute('class')}'")
                raise Exception("Zip code input field not found")
            
            # Clear and enter the zip code
            print(f"Entering zip code: {zipcode}")
            zip_input.clear()
            zip_input.send_keys(zipcode)
            time.sleep(1)
            
            # Try to find and click submit button or press Enter
            try:
                submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit'], .search-button, button:contains('Search')")
                submit_button.click()
                print("Clicked submit button")
            except:
                print("Submit button not found, pressing Enter")
                zip_input.send_keys(Keys.RETURN)
            
            # Wait for results to load
            print("Waiting for store results to load...")
            time.sleep(5)
            
            return True
            
        except Exception as e:
            print(f"Error during search: {e}")
            print("Current page title:", self.driver.title)
            print("Current URL:", self.driver.current_url)
            return False
    
    def extract_store_data(self):
        """Extract store information from the results page"""
        try:
            # Get page source and parse with BeautifulSoup
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            stores = []
            
            # Method 1: Look for location card containers
            store_containers = soup.find_all('li', {'data-cy': 'LocationCardListItemComponent'})
            
            if not store_containers:
                # Method 2: Look for store elements with different patterns
                store_containers = soup.find_all('div', class_=re.compile(r'location-card|store-card'))
            
            if not store_containers:
                # Method 3: Look for any elements containing store data
                store_containers = soup.find_all('div', string=re.compile(r'miles away|Store Details'))
                store_containers = [container.find_parent('div') for container in store_containers if container.find_parent('div')]
            
            print(f"Found {len(store_containers)} potential store containers")
            
            for i, container in enumerate(store_containers):
                try:
                    store_data = self.parse_store_container(container, i+1)
                    if store_data and store_data['store_name']:  # Only add if we got valid data
                        stores.append(store_data)
                        print(f"  ✓ Extracted: {store_data['store_name']}")
                    
                except Exception as e:
                    print(f"  ✗ Error parsing store {i+1}: {e}")
                    continue
            
            # If no stores found with primary method, try alternative extraction
            if not stores:
                stores = self.extract_stores_alternative_method(soup)
            
            self.scraped_data = stores
            return stores
            
        except Exception as e:
            print(f"Error extracting store data: {e}")
            return []
    
    def parse_store_container(self, container, store_number):
        """Parse individual store container to extract data"""
        store_data = {
            'store_number': store_number,
            'store_name': '',
            'address': '',
            'hours': '',
            'distance': '',
            'phone': '',
            'store_details_link': ''
        }
        
        # Extract store name
        name_selectors = [
            'h2 button[data-cy="store-heading"]',
            'h2.location-card-title button',
            '.location-card-title button',
            'h2 button',
            '.store-name',
            'h2',
            'h3'
        ]
        
        for selector in name_selectors:
            name_elem = container.select_one(selector)
            if name_elem:
                store_data['store_name'] = name_elem.get_text(strip=True)
                break
        
        # Extract address
        address_selectors = [
            'span[data-cy="AddressComponent"]',
            '.loc-address',
            '.store-address',
            '.address'
        ]
        
        for selector in address_selectors:
            addr_elem = container.select_one(selector)
            if addr_elem:
                # Get all text within address element
                address_parts = []
                for span in addr_elem.find_all('span'):
                    text = span.get_text(strip=True)
                    if text:
                        address_parts.append(text)
                
                if address_parts:
                    store_data['address'] = ', '.join(address_parts)
                else:
                    store_data['address'] = addr_elem.get_text(strip=True)
                break
        
        # Extract hours
        hours_selectors = [
            'span[data-cy="BusinessHoursComponent"]',
            '.hours',
            '.store-hours',
            '.business-hours'
        ]
        
        for selector in hours_selectors:
            hours_elem = container.select_one(selector)
            if hours_elem:
                store_data['hours'] = hours_elem.get_text(strip=True)
                break
        
        # Extract distance
        distance_selectors = [
            'p[data-cy="LocationDistance"]',
            '.location-distance p',
            '.distance'
        ]
        
        for selector in distance_selectors:
            dist_elem = container.select_one(selector)
            if dist_elem:
                store_data['distance'] = dist_elem.get_text(strip=True)
                break
        
        # Extract store details link
        details_selectors = [
            'a[data-cy="DetailsComponent"]',
            'a.details',
            'a[href*="stores.bestbuy.com"]'
        ]
        
        for selector in details_selectors:
            details_elem = container.select_one(selector)
            if details_elem:
                store_data['store_details_link'] = details_elem.get('href', '')
                break
        
        # Extract phone from JSON data if available
        script_tags = container.find_all('script')
        for script in script_tags:
            script_text = script.get_text()
            if 'phone' in script_text:
                phone_match = re.search(r'"phone":"([^"]+)"', script_text)
                if phone_match:
                    store_data['phone'] = phone_match.group(1)
                    break
        
        return store_data
    
    def extract_stores_alternative_method(self, soup):
        """Alternative method to extract store data if primary method fails"""
        print("Trying alternative extraction method...")
        stores = []
        
        # Look for any text patterns that indicate stores
        store_patterns = [
            re.compile(r'Chelsea \([^)]+\)'),
            re.compile(r'\d+\.\d+ miles away'),
            re.compile(r'Open until \d+ [ap]m'),
            re.compile(r'\d+ W \d+\w+ St')
        ]
        
        # Search for elements containing these patterns
        potential_stores = set()
        for pattern in store_patterns:
            elements = soup.find_all(string=pattern)
            for elem in elements:
                parent = elem.parent
                while parent and parent.name != 'li':
                    parent = parent.parent
                if parent:
                    potential_stores.add(parent)
        
        # Try to extract data from found elements
        for i, store_elem in enumerate(potential_stores):
            try:
                store_data = {
                    'store_number': i + 1,
                    'store_name': '',
                    'address': '',
                    'hours': '',
                    'distance': '',
                    'phone': '',
                    'store_details_link': ''
                }
                
                # Extract any available text
                text = store_elem.get_text()
                
                # Try to parse store name (usually in parentheses)
                name_match = re.search(r'([A-Za-z\s]+\([^)]+\))', text)
                if name_match:
                    store_data['store_name'] = name_match.group(1).strip()
                
                # Try to parse address
                addr_match = re.search(r'(\d+\s+[NSEW]?\s*\d*\w*\s+St[^,]*)', text)
                if addr_match:
                    store_data['address'] = addr_match.group(1).strip()
                
                # Try to parse hours
                hours_match = re.search(r'(Open until \d+ [ap]m)', text)
                if hours_match:
                    store_data['hours'] = hours_match.group(1).strip()
                
                # Try to parse distance
                dist_match = re.search(r'(\d+\.\d+ miles away)', text)
                if dist_match:
                    store_data['distance'] = dist_match.group(1).strip()
                
                if store_data['store_name'] or store_data['address']:
                    stores.append(store_data)
                    
            except Exception as e:
                print(f"Error in alternative extraction for store {i}: {e}")
                continue
        
        return stores
    
    def save_to_csv(self, filename='bestbuy_stores.csv'):
        """Save scraped data to CSV file"""
        if not self.scraped_data:
            print("No data to save")
            return
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['store_number', 'store_name', 'address', 'hours', 'distance', 'phone', 'store_details_link']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for store in self.scraped_data:
                writer.writerow(store)
        
        print(f"Data saved to {filename}")
    
    def save_to_json(self, filename='bestbuy_stores.json'):
        """Save scraped data to JSON file"""
        if not self.scraped_data:
            print("No data to save")
            return
        
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(self.scraped_data, jsonfile, indent=2, ensure_ascii=False)
        
        print(f"Data saved to {filename}")
    
    def take_screenshot(self, filename='bestbuy_page.png'):
        """Take a screenshot for debugging"""
        try:
            self.driver.save_screenshot(filename)
            print(f"Screenshot saved as {filename}")
        except Exception as e:
            print(f"Failed to take screenshot: {e}")
    
    def close(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            print("WebDriver closed")
    
    def scrape_stores(self, zipcode="10001", take_screenshot=False):
        """Main method to scrape Best Buy stores"""
        try:
            print("=== Best Buy Store Locator Scraper ===")
            
            # Search for stores
            if self.search_stores_by_zipcode(zipcode):
                
                # Take screenshot if requested
                if take_screenshot:
                    self.take_screenshot()
                
                # Extract store data
                stores = self.extract_store_data()
                
                if stores:
                    print(f"\n=== Successfully extracted {len(stores)} stores ===")
                    
                    # Display results
                    for i, store in enumerate(stores, 1):
                        print(f"\nStore {i}:")
                        print(f"  Name: {store['store_name']}")
                        print(f"  Address: {store['address']}")
                        print(f"  Hours: {store['hours']}")
                        print(f"  Distance: {store['distance']}")
                        if store['phone']:
                            print(f"  Phone: {store['phone']}")
                    
                    # Save data
                    self.save_to_csv()
                    self.save_to_json()
                    
                    return stores
                else:
                    print("No store data extracted")
                    return []
            else:
                print("Failed to search for stores")
                return []
                
        except Exception as e:
            print(f"Error during scraping: {e}")
            return []
        finally:
            self.close()

# Usage example
if __name__ == "__main__":
    # Initialize scraper (set headless=False to see the browser)
    scraper = BestBuyStoreLocatorScraper(headless=False)
    
    try:
        # Scrape stores for zip code 10001
        stores = scraper.scrape_stores(zipcode="10001", take_screenshot=True)
        
        print(f"\n=== FINAL SUMMARY ===")
        print(f"Total stores found: {len(stores)}")
        print(f"Files saved:")
        print(f"  - bestbuy_stores.csv")
        print(f"  - bestbuy_stores.json")
        print(f"  - bestbuy_page.png (screenshot)")
        
    except Exception as e:
        print(f"Script failed: {e}")
    
    finally:
        # Ensure driver is closed
        scraper.close()