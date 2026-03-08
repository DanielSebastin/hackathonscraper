from playwright.sync_api import sync_playwright
import json
import os
import time
import re

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
os.makedirs(DATA_DIR, exist_ok=True)
RAW_DATA_PATH = os.path.join(DATA_DIR, 'raw_events.json')

def scrape_knowafest():
    print("Firing up the Multi-Tab Playwright Scraper...")
    events_data = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False) 
        context = browser.new_context()
        page = context.new_page()
        
        max_pages = 3 

        for current_page in range(1, max_pages + 1):
            print(f"\n--- Scanning Page {current_page} ---")
            
            table_url = f"https://www.knowafest.com/explore/category/Hackathon?page={current_page}"
            if current_page == 1:
                table_url = "https://www.knowafest.com/explore/category/Hackathon"
                
            page.goto(table_url, timeout=60000)
            page.wait_for_selector("table tr", timeout=15000)
            time.sleep(2) 

            row_count = page.locator("table tr").count()
            print(f"Found {row_count} rows. Starting the Tab-Switching sequence...")

            for i in range(1, row_count): 
                try:
                    row = page.locator("table tr").nth(i)
                    cols = row.locator("td")
                    
                    if cols.count() < 4:
                        continue
                        
                    start_date = cols.nth(0).inner_text().strip()
                    fest_name_raw = cols.nth(1).inner_text().strip()
                    fest_name = fest_name_raw.split('\n')[0].strip()
                    fest_type = cols.nth(2).inner_text().strip()
                    location = cols.nth(3).inner_text().strip()
                    
                    event_data = {
                        "date": start_date,
                        "title": fest_name,
                        "type": fest_type,
                        "location": location,
                        "registration_url": None, 
                        "description": "" # This will hold the massive details payload
                    }
                    
                    print(f"  -> Clicking into: {fest_name[:30]}...")
                    
                    try:
                        with context.expect_page(timeout=10000) as new_page_info:
                            cols.nth(1).click() 
                            
                        new_page = new_page_info.value
                        new_page.wait_for_load_state("domcontentloaded")
                        time.sleep(1)
                        
                        # 1. Hunt the Registration Link
                        reg_btn = new_page.locator("a", has_text=re.compile(r"Register|Website", re.IGNORECASE)).first
                        if reg_btn.count() > 0:
                            href = reg_btn.get_attribute("href")
                            if href and href != "#" and "javascript" not in href:
                                event_data["registration_url"] = href
                                print(f"     [+] Reg Link: {href}")

                        # 2. THE DETAIL EXTRACTOR (Dates, Fees, About, etc.)
                        # Grab all headings, paragraphs, and list items
                        raw_texts = new_page.locator("h2, h3, h4, h5, p, li").all_inner_texts()
                        
                        clean_texts = []
                        # Junk words we want to ignore from the sidebar/navbar
                        junk_filters = [
                            "India’s Largest", "Login", "Create Event", "Register now", 
                            "View Event", "Website", "Poster", "Location ->", "Map", 
                            "Email ->", "Join WhatsApp", "Group", "Event Type:", "Start Date :"
                        ]

                        for t in raw_texts:
                            clean_t = t.strip()
                            if len(clean_t) > 3 and not any(junk in clean_t for junk in junk_filters):
                                # Avoid duplicating lines
                                if clean_t not in clean_texts:
                                    clean_texts.append(clean_t)

                        # Join everything with double newlines so it looks like a clean document
                        full_text = "\n\n".join(clean_texts)
                        
                        if len(full_text) > 50:
                            event_data["description"] = full_text
                            print("     [+] Extracted Event Details, Dates, and Fees.")
                        else:
                            event_data["description"] = f"{fest_name} is a {fest_type} event happening on {start_date} at {location}."
                        
                        new_page.close()
                        time.sleep(0.5)
                        
                    except Exception as click_err:
                        print(f"     [!] Row didn't open properly. Saving basic info.")
                        event_data["description"] = f"{fest_name} is a {fest_type} event happening on {start_date} at {location}."

                    if fest_name and not any(e["title"] == fest_name for e in events_data):
                        events_data.append(event_data)
                        
                except Exception as e:
                    continue 

        browser.close()

    with open(RAW_DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(events_data, f, indent=4)
    
    print(f"\nBoom! Master Database built. Saved {len(events_data)} total events to {RAW_DATA_PATH}")

if __name__ == "__main__":
    scrape_knowafest()