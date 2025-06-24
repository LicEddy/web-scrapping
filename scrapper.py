"""
Selenium-based scraper for JavaScript-heavy sites.
Optimized for freshproduce.com based on actual HTML structure.
FIXED VERSION - handles both 'genericpage' and 'resourcedetailpage' articles
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
import pandas as pd
import time

def setup_driver():
    """Setup Chrome driver with appropriate options"""
    chrome_options = Options()
    
    # Uncomment the next line if you want headless mode (no browser window)
    # chrome_options.add_argument("--headless")
    
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Add user agent
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def scrape_category_with_selenium(driver, category):
    """
    Scrape articles from a category page using Selenium.
    Optimized for freshproduce.com HTML structure.
    FIXED: Now handles both 'genericpage' and 'resourcedetailpage' tiles
    
    Args:
        driver: Selenium WebDriver instance
        category (str): Category name
    
    Returns:
        list: List of article data dictionaries
    """
    url = f"https://www.freshproduce.com/resources/{category}/?filteredCategories=Article"
    print(f"Loading page: {url}")
    
    driver.get(url)
    time.sleep(3)
    
    # Check page stats to understand pagination
    try:
        stats_elem = driver.find_element(By.CSS_SELECTOR, "div.search-stats p")
        stats_text = stats_elem.text
        print(f"Page stats: {stats_text}")
        
        # Parse results info
        if "of" in stats_text and "results" in stats_text:
            parts = stats_text.replace("Showing", "").replace("results", "").strip()
            if "-" in parts and "of" in parts:
                range_part = parts.split("of")[0].strip()
                total_part = parts.split("of")[1].strip()
                
                if "-" in range_part:
                    shown_end = int(range_part.split("-")[1].strip())
                else:
                    shown_end = int(range_part.strip())
                    
                total_results = int(total_part.strip())
                
                print(f"Showing up to {shown_end} of {total_results} total results")
                
                # Only try Load More if there are more results to load
                if total_results > shown_end:
                    print("More results available, will try Load More button")
                    load_more_needed = True
                else:
                    print("All results already visible, no Load More needed")
                    load_more_needed = False
            else:
                load_more_needed = True  # Default to trying if we can't parse
        else:
            load_more_needed = True  # Default to trying if no stats found
            
    except Exception as e:
        print(f"Could not parse page stats: {e}")
        load_more_needed = True  # Default to trying
    
    # Try to click Load More buttons if needed
    if load_more_needed:
        load_more_attempts = 0
        max_load_more_attempts = 10  # Reduced from 30
        
        while load_more_attempts < max_load_more_attempts:
            try:
                # Try to find the "Load More" button
                load_more_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, 
                        "//button[contains(., 'Load More') or contains(., 'Load more') or contains(., 'LOAD MORE')]"
                    ))
                )
                
                # Scroll to the button and click it
                driver.execute_script("arguments[0].scrollIntoView(true);", load_more_button)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", load_more_button)
                print(f"Clicked 'Load More' button (attempt {load_more_attempts + 1})")
                time.sleep(3)  # Wait for content to load
                load_more_attempts += 1
                
            except Exception as e:
                print(f"No more 'Load More' buttons found: {e}")
                break
    
    # Scroll through page for any lazy loading
    print("Scrolling through page...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    scroll_attempts = 0
    max_scroll_attempts = 3  # Reduced scrolling
    
    while scroll_attempts < max_scroll_attempts:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            scroll_attempts += 1
        else:
            scroll_attempts = 0
        
        last_height = new_height
        
        if scroll_attempts >= 2:
            break
    
    # Save page source for debugging
    try:
        with open(f"{category}_page_debug.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"Saved debug HTML to {category}_page_debug.html")
    except Exception as e:
        print(f"Could not save debug HTML: {e}")
    
    # Now extract articles using the optimized selectors
    try:
        # Wait for and find the main results container
        container = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.result-panel"))
        )
        print("Found main results container")
        
        # FIXED: Use a more inclusive selector that catches both genericpage and resourcedetailpage
        article_elements = container.find_elements(By.CSS_SELECTOR, "div.tile")
        
        # Filter to only include tiles that have the structure we want
        valid_articles = []
        for element in article_elements:
            class_list = element.get_attribute("class")
            print(f"Found tile with classes: {class_list}")
            
            # Check if it's either genericpage or resourcedetailpage
            if "genericpage" in class_list or "resourcedetailpage" in class_list:
                valid_articles.append(element)
                print(f"  ✓ Valid article tile")
            else:
                print(f"  ✗ Skipping tile (not an article)")
        
        article_elements = valid_articles
        print(f"Found {len(article_elements)} valid article elements")
        
        unique_articles = {}
        
        for i, article in enumerate(article_elements, 1):
            try:
                article_data = {}
                
                # Extract title using specific selector
                try:
                    title_elem = article.find_element(By.CSS_SELECTOR, "p.title")
                    title = title_elem.text.strip()
                    if not title:
                        raise Exception("Empty title")
                    article_data['Title'] = title
                    print(f"Title {i}: {title}")
                except Exception as e:
                    print(f"Could not find title for article {i}: {e}")
                    continue
                
                # Extract URL using specific selector
                try:
                    link_elem = article.find_element(By.CSS_SELECTOR, "div.cta-area a.score-button")
                    url = link_elem.get_attribute('href')
                    if not url or "freshproduce.com" not in url:
                        raise Exception("Invalid URL")
                    article_data['URL'] = url
                    print(f"URL {i}: {url}")
                except Exception as e:
                    print(f"Could not find URL for article {i}: {e}")
                    continue
                
                # Extract category from eyebrow
                try:
                    category_elem = article.find_element(By.CSS_SELECTOR, "p.eyebrow")
                    article_data['Category'] = category_elem.text.strip()
                    print(f"Category {i}: {article_data['Category']}")
                except Exception as e:
                    # Fallback to the category parameter
                    article_data['Category'] = category.replace('-', ' ').title()
                    print(f"Using fallback category for article {i}: {article_data['Category']}")
                
                # Extract description
                try:
                    desc_elem = article.find_element(By.CSS_SELECTOR, "p.description")
                    article_data['Description'] = desc_elem.text.strip()
                except Exception as e:
                    article_data['Description'] = ""
                    print(f"No description found for article {i}")
                
                # Extract image info (bonus)
                try:
                    img_elem = article.find_element(By.CSS_SELECTOR, "div.image-wrapper img")
                    article_data['ImageURL'] = img_elem.get_attribute('src')
                    article_data['ImageAlt'] = img_elem.get_attribute('alt')
                except Exception as e:
                    article_data['ImageURL'] = ""
                    article_data['ImageAlt'] = ""
                
                # Only add article if we have essential data (title and URL)
                if article_data.get('Title') and article_data.get('URL'):
                    # Skip duplicates
                    if url in unique_articles:
                        print(f"Skipping duplicate: {url}")
                        continue
                    
                    unique_articles[url] = article_data
                    print(f"✓ Successfully extracted article {i}: {article_data['Title']}")
                else:
                    print(f"✗ Skipping article {i} - missing essential data")
                
            except Exception as e:
                print(f"Error processing article {i}: {e}")
                continue
        
        articles_list = list(unique_articles.values())
        print(f"\nSuccessfully extracted {len(articles_list)} unique articles from {category}")
        
        # Get full content for each article
        for i, article in enumerate(articles_list, 1):
            try:
                print(f"Getting full content {i}/{len(articles_list)}: {article['Title']}")
                article['FullArticleText'] = scrape_full_article_with_selenium(driver, article['URL'])
                
                # Save progress after each article
                df_temp = pd.DataFrame(articles_list[:i])
                if not df_temp.empty:
                    df_temp.to_csv(f'{category}_temp_progress.csv', index=False)
                
            except Exception as e:
                print(f"Error getting full content for {article.get('URL', 'unknown')}: {e}")
                article['FullArticleText'] = ""
        
        return articles_list
        
    except TimeoutException:
        print("Timed out waiting for page to load")
        return []
    except Exception as e:
        print(f"Error in scrape_category_with_selenium: {e}")
        import traceback
        traceback.print_exc()
        return []

def scrape_full_article_with_selenium(driver, article_url):
    """
    Extract full article content using Selenium.
    
    Args:
        driver: Selenium WebDriver instance
        article_url (str): URL of the article
    
    Returns:
        str: Full article text
    """
    try:
        print(f"Loading article: {article_url}")
        driver.get(article_url)
        
        # Wait for article content to load
        wait = WebDriverWait(driver, 15)
        
        # Try different selectors for article content (in order of preference)
        content_selectors = [
            "main article",  # Most semantic
            "article .content",
            "main .content",
            ".article-content",
            ".post-content", 
            ".entry-content",
            "main",
            ".main-content",
            "article"
        ]
        
        content = ""
        
        for selector in content_selectors:
            try:
                # Wait for element to be present
                content_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                content = content_element.text.strip()
                
                # Only use if we got substantial content
                if len(content) > 100:  # Arbitrary threshold
                    print(f"Found content using selector: {selector} ({len(content)} chars)")
                    break
                else:
                    content = ""  # Reset if content too short
                    
            except Exception as e:
                continue
        
        # Final fallback: get body text if nothing else worked
        if not content:
            try:
                body = driver.find_element(By.TAG_NAME, "body")
                content = body.text.strip()
                print(f"Using fallback body text ({len(content)} chars)")
            except:
                content = "Could not extract article content"
                print(f"Could not extract any content")
        
        return content
        
    except Exception as e:
        print(f"Error getting article content from {article_url}: {e}")
        return f"Error extracting content: {str(e)}"

def main_selenium_scraper():
    """Main function using optimized Selenium scraper"""
    categories = ['global-trade', 'technology', 'food-safety']
    all_articles = []
    
    # Setup driver
    print("Setting up Chrome driver...")
    driver = setup_driver()
    
    try:
        # Scrape each category
        for category in categories:
            print(f"\n{'='*60}")
            print(f"SCRAPING CATEGORY: {category.upper()}")
            print(f"{'='*60}")
            
            articles = scrape_category_with_selenium(driver, category)
            all_articles.extend(articles)
            
            print(f"Completed {category}: {len(articles)} articles")
            time.sleep(2)  # Be respectful between categories
        
        print(f"\nSCRAPING COMPLETE!")
        print(f"Total articles found: {len(all_articles)}")
        
        if all_articles:
            # Create DataFrame with proper column order
            df = pd.DataFrame(all_articles)
            
            # Ensure we have all expected columns
            expected_columns = ['Title', 'URL', 'Category', 'Description', 'ImageURL', 'ImageAlt', 'FullArticleText']
            for col in expected_columns:
                if col not in df.columns:
                    df[col] = ""
            
            # Reorder columns
            df = df[expected_columns]
            
            # Clean data before saving
            print("🧹 Cleaning data...")
            for col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = df[col].astype(str)  # Convert to string
                    df[col] = df[col].str.replace('"', '""')  # Escape quotes
                    df[col] = df[col].str.replace('\n', ' ')  # Replace newlines
                    df[col] = df[col].str.replace('\r', ' ')  # Replace carriage returns
                    df[col] = df[col].str.strip()  # Remove leading/trailing whitespace
            
            # Save to CSV
            filename = 'scraped_freshproduce_data.csv'
            df.to_csv(filename, 
                     index=False, 
                     encoding='utf-8',
                     quoting=1,  # QUOTE_ALL
                     quotechar='"',
                     escapechar='\\')
            
            print(f"Saved {len(all_articles)} articles to {filename}")
            
            # Print summary
            print(f"\nSUMMARY:")
            print(f"   • Total articles: {len(all_articles)}")
            print(f"   • Categories: {', '.join(categories)}")
            print(f"   • File: {filename}")
            
            # Show category breakdown
            category_counts = df['Category'].value_counts()
            print(f"\nBREAKDOWN BY CATEGORY:")
            for cat, count in category_counts.items():
                print(f"   • {cat}: {count} articles")
                
        else:
            print("No articles found!")
        
    except Exception as e:
        print(f"Error in main scraper: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Always close the driver
        print("Closing browser...")
        driver.quit()
        print("Done!")

if __name__ == "__main__":
    main_selenium_scraper()