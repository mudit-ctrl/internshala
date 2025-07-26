# Webscrapper

## Overview

This project contains two advanced web scrapers written in Python:

1. **Earth911Scraper** (`main.py`): Scrapes electronics recycling locations and accepted materials from [Earth911](https://search.earth911.com/), providing structured data for recycling centers.
2. **BestBuyStoreLocatorScraper** (`bonus.py`): Uses Selenium to scrape Best Buy store locations, addresses, hours, and more from the [Best Buy Store Locator](https://www.bestbuy.com/site/store-locator).

Both scrapers output data in CSV and JSON formats for easy analysis and integration.

---

## Features

### Earth911Scraper (`main.py`)
- Scrapes all paginated search results for electronics recycling in a given area.
- Extracts business name, last update date, address, and a detailed list of accepted materials.
- Outputs data to `earth911_electronics_recycling.csv` and `earth911_electronics_recycling.json`.
- Robust error handling and polite scraping (with delays).

### BestBuyStoreLocatorScraper (`bonus.py`)
- Automates Chrome browser with Selenium to search for Best Buy stores by ZIP code.
- Extracts store name, address, hours, distance, phone, and details link.
- Outputs data to `bestbuy_stores.csv` and `bestbuy_stores.json`.
- Optionally takes a screenshot of the results page.

---

## Requirements

- Python 3.7+
- [BeautifulSoup4](https://pypi.org/project/beautifulsoup4/)
- [requests](https://pypi.org/project/requests/)
- [Selenium](https://pypi.org/project/selenium/) (for `bonus.py`)
- Chrome browser and [ChromeDriver](https://chromedriver.chromium.org/) (for `bonus.py`)

Install dependencies:
```bash
pip install beautifulsoup4 requests selenium
```

---

## Usage

### 1. Earth911Scraper (`main.py`)

**Run the scraper:**
```bash
python main.py
```

- The script will scrape all electronics recycling locations for a default search (NYC area, ZIP 10001).
- Outputs:
  - `earth911_electronics_recycling.csv`: Tabular data with columns: Business_Name, last_update_date, street_address, materials_accepted
  - `earth911_electronics_recycling.json`: List of objects with the same fields, materials as a list

**Sample CSV row:**
```
Business_Name,last_update_date,street_address,materials_accepted
New York City Bulk Item Curbside Program,2016-2-23,"New York, NY 10001","Air Conditioners; Barbeque Grills; ..."
```

**Sample JSON object:**
```
{
  "Business_Name": "New York City Bulk Item Curbside Program",
  "last_update_date": "2016-2-23",
  "street_address": "New York, NY 10001",
  "materials_accepted": ["Air Conditioners", "Barbeque Grills", ...]
}
```

---

### 2. BestBuyStoreLocatorScraper (`bonus.py`)

**Run the scraper:**
```bash
python bonus.py
```

- By default, scrapes Best Buy stores for ZIP code 10001.
- Outputs:
  - `bestbuy_stores.csv`: Tabular data with columns: store_number, store_name, address, hours, distance, phone, store_details_link
  - `bestbuy_stores.json`: List of objects with the same fields
  - `bestbuy_page.png`: Screenshot of the results page (optional)

**Sample CSV row:**
```
store_number,store_name,address,hours,distance,phone,store_details_link
1,Chelsea (23rd and 6th),"60 W 23rd St, New York,NY10010",Open until 9 pm,0.5miles away,,https://stores.bestbuy.com/482
```

**Sample JSON object:**
```
{
  "store_number": 1,
  "store_name": "Chelsea (23rd and 6th)",
  "address": "60 W 23rd St, New York,NY10010",
  "hours": "Open until 9 pm",
  "distance": "0.5miles away",
  "phone": "",
  "store_details_link": "https://stores.bestbuy.com/482"
}
```

---

## Project Structure

```
.
├── main.py                        # Earth911Scraper
├── bonus.py                       # BestBuyStoreLocatorScraper
├── earth911_electronics_recycling.csv / .json
├── bestbuy_stores.csv / .json
├── venv/                          # (optional) Python virtual environment
```

---

## Notes
- For `bonus.py`, ensure ChromeDriver is installed and matches your Chrome version.
- Both scripts can be modified to change the search area or ZIP code.
- Data is saved in both CSV and JSON for flexibility.

---

## License
This project is provided for educational and research purposes. Please respect the terms of use of the target websites. 