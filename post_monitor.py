import os
import time
import json
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from dotenv import load_dotenv
from plyer import notification

class SupersetPostMonitor:
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv('.env')
        
        self.username = os.getenv('SUPERSET_USERNAME')
        self.password = os.getenv('SUPERSET_PASSWORD')
        self.login_url = os.getenv('LOGIN_URL')
        self.dashboard_url = os.getenv('DASHBOARD_URL')
        self.check_interval = int(os.getenv('CHECK_INTERVAL', 300))  # Default 5 minutes
        
        # Debug: Print loaded environment variables (hide password)
        print("🔧 Environment variables loaded:")
        print(f"   SUPERSET_USERNAME: {self.username}")
        print(f"   SUPERSET_PASSWORD: {'*' * len(self.password) if self.password else 'None'}")
        print(f"   LOGIN_URL: {self.login_url}")
        print(f"   DASHBOARD_URL: {self.dashboard_url}")
        print(f"   CHECK_INTERVAL: {self.check_interval}")
        
        if not self.username or not self.password:
            print("❌ ERROR: Username or password not found in .env file!")
            print("Please check your .env file contains SUPERSET_USERNAME and SUPERSET_PASSWORD")
        
        self.driver = None
        self.known_posts = {}  # Changed to dict to store full post data
        self.load_known_posts()
    
    def setup_driver(self, headless=True):
        """Setup Chrome WebDriver with options"""
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument('--headless')  # Run in background
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return self.driver
    
    def login(self):
        """Login to the Superset platform"""
        try:
            print(f"🔐 Attempting login to {self.login_url}")
            self.driver.get(self.login_url)
            
            # Wait for login form and fill credentials
            # Try different possible selectors for email/username field
            username_field = None
            selectors = [
                (By.NAME, "email"),
                (By.NAME, "username"), 
                (By.ID, "email"),
                (By.ID, "username"),
                (By.XPATH, "//input[@type='email']"),
                (By.XPATH, "//input[@placeholder*='email' or @placeholder*='Email']")
            ]
            
            for selector_type, selector_value in selectors:
                try:
                    username_field = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((selector_type, selector_value))
                    )
                    break
                except:
                    continue
            
            if not username_field:
                raise Exception("Could not find username/email field")
            
            # Find password field
            password_field = None
            password_selectors = [
                (By.NAME, "password"),
                (By.ID, "password"),
                (By.XPATH, "//input[@type='password']")
            ]
            
            for selector_type, selector_value in password_selectors:
                try:
                    password_field = self.driver.find_element(selector_type, selector_value)
                    break
                except:
                    continue
            
            if not password_field:
                raise Exception("Could not find password field")
            
            # Clear fields and enter credentials
            username_field.clear()
            username_field.send_keys(self.username)
            
            password_field.clear()
            password_field.send_keys(self.password)
            
            # Submit login form - try different methods
            try:
                # Try finding submit button
                login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
                login_button.click()
            except:
                try:
                    # Try finding login button by text
                    login_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Log') or contains(text(), 'Sign')]")
                    login_button.click()
                except:
                    # Try pressing Enter on password field
                    password_field.send_keys(Keys.RETURN)
            
            # Wait for successful login - check if we're redirected to dashboard
            try:
                WebDriverWait(self.driver, 15).until(
                    lambda driver: self.dashboard_url in driver.current_url or "dashboard" in driver.current_url.lower()
                )
                print(f"✅ Successfully logged in and redirected to: {self.driver.current_url}")
            except:
                # If redirect doesn't happen automatically, try navigating manually
                print(f"⚠️ Auto-redirect failed. Current URL: {self.driver.current_url}")
                print("🔄 Manually navigating to dashboard...")
                self.driver.get(self.dashboard_url)
                time.sleep(5)
                
                # Check if we're now on the dashboard
                if self.dashboard_url not in self.driver.current_url:
                    print(f"❌ Failed to reach dashboard. Current URL: {self.driver.current_url}")
                    return False
            
            print(f"✅ Successfully logged in at {datetime.now()}")
            return True
            
        except Exception as e:
            print(f"❌ Login failed: {str(e)}")
            print(f"Current URL: {self.driver.current_url}")
            return False
    
    def scroll_to_load_all_posts(self):
        """Scroll the specific posts container to load all posts"""
        print("📜 Scrolling posts container to load all posts...")
        
        try:
            # Find the specific scrollable container
            container_selectors = [
                'div.flex-grow.overflow-scroll.sm\\:mb-0',  # Exact selector with escaped colon
                'div[class*="flex-grow"][class*="overflow-scroll"]',  # Partial match
                'div.overflow-scroll',  # Fallback to any overflow-scroll div
                '[class*="overflow-scroll"]'  # Most generic fallback
            ]
            
            scroll_container = None
            for selector in container_selectors:
                try:
                    scroll_container = self.driver.find_element(By.CSS_SELECTOR, selector)
                    print(f"✅ Found scroll container with selector: {selector}")
                    break
                except:
                    continue
            
            if not scroll_container:
                print("⚠️ Scroll container not found, falling back to page scroll")
                self.scroll_page_fallback()
                return
            
            # Get initial scroll height of the container
            last_height = self.driver.execute_script("return arguments[0].scrollHeight", scroll_container)
            scroll_attempts = 0
            max_attempts = 15  # Increased attempts for container scrolling
            
            print(f"📏 Initial container scroll height: {last_height}")
            
            while scroll_attempts < max_attempts:
                # Scroll the container to bottom
                self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scroll_container)
                
                # Wait for new content to load
                time.sleep(2)
                
                # Get new scroll height of the container
                new_height = self.driver.execute_script("return arguments[0].scrollHeight", scroll_container)
                
                if new_height == last_height:
                    print(f"✅ Reached end of container after {scroll_attempts + 1} scroll attempts")
                    break
                
                last_height = new_height
                scroll_attempts += 1
                print(f"📜 Scroll attempt {scroll_attempts + 1}, container height: {new_height}")
            
            # Scroll container back to top for better visibility
            self.driver.execute_script("arguments[0].scrollTop = 0", scroll_container)
            time.sleep(1)
            
            print(f"✅ Container scrolling completed after {scroll_attempts + 1} attempts")
            
        except Exception as e:
            print(f"⚠️ Error scrolling container: {str(e)}")
            print("🔄 Falling back to page scrolling...")
            self.scroll_page_fallback()
    
    def scroll_page_fallback(self):
        """Fallback method to scroll the entire page if container scrolling fails"""
        print("📜 Using page scroll fallback...")
        
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_attempts = 10
        
        while scroll_attempts < max_attempts:
            # Scroll down to bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Wait for new content to load
            time.sleep(3)
            
            # Calculate new scroll height and compare with last scroll height
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            
            if new_height == last_height:
                print(f"✅ Reached end of page after {scroll_attempts + 1} scroll attempts")
                break
            
            last_height = new_height
            scroll_attempts += 1
            print(f"📜 Scroll attempt {scroll_attempts + 1}, page height: {new_height}")
        
        # Scroll back to top for better visibility
        self.driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)

    def get_posts(self):
        """Extract posts from the Superset platform using feedHeader structure"""
        try:
            # Navigate to dashboard if not already there
            if self.dashboard_url not in self.driver.current_url:
                print(f"🔄 Navigating to dashboard: {self.dashboard_url}")
                self.driver.get(self.dashboard_url)
                time.sleep(5)
            
            print(f"📍 Current URL: {self.driver.current_url}")
            
            # Wait for page to load and content to appear
            print("⏳ Waiting for page content to load...")
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Wait a bit more for dynamic content to load
            time.sleep(5)
            print("✅ Page loaded, now loading all posts...")
            
            # Scroll to load all posts
            self.scroll_to_load_all_posts()
            
            current_posts = []
            
            # Look specifically for feedHeader divs
            try:
                feed_headers = self.driver.find_elements(By.CLASS_NAME, "feedHeader")
                print(f"📋 Found {len(feed_headers)} feedHeader elements")
                
                for i, header in enumerate(feed_headers):
                    try:
                        # Extract post title from the p tag with specific classes
                        title_element = header.find_element(By.CSS_SELECTOR, "p.text-base.font-bold.text-dark")
                        post_title = title_element.text.strip()
                        
                        # Extract author and time from the flex div
                        flex_div = header.find_element(By.CSS_SELECTOR, "div.flex.mt-1.flex-wrap")
                        spans = flex_div.find_elements(By.CSS_SELECTOR, "span.text-gray-500.text-xs")
                        
                        author = ""
                        post_time = ""
                        
                        if len(spans) >= 2:
                            author = spans[0].text.strip()
                            post_time = spans[1].text.strip()
                        elif len(spans) == 1:
                            # Sometimes author might be missing, so the single span is the time
                            post_time = spans[0].text.strip()
                        
                        # Extract detailed post content from prose div
                        post_details = ""
                        post_links = []
                        
                        try:
                            # Look for the prose div in the parent container or nearby elements
                            parent_container = header.find_element(By.XPATH, "../..")  # Go up two levels to find the full post container
                            
                            # Try to find the prose div
                            prose_selectors = [
                                'div.prose',
                                'div[class*="prose"]',
                                'div p.text-sm.text-gray-600',
                                'div[class*="text-gray-600"]'
                            ]
                            
                            prose_element = None
                            for selector in prose_selectors:
                                try:
                                    prose_element = parent_container.find_element(By.CSS_SELECTOR, selector)
                                    break
                                except:
                                    continue
                            
                            if prose_element:
                                # Extract the full text content
                                post_details = prose_element.text.strip()
                                
                                # Extract all links from the prose content
                                try:
                                    link_elements = prose_element.find_elements(By.TAG_NAME, "a")
                                    for link_elem in link_elements:
                                        href = link_elem.get_attribute("href")
                                        text = link_elem.text.strip()
                                        if href:
                                            post_links.append({
                                                'url': href,
                                                'text': text
                                            })
                                except:
                                    pass
                                
                                print(f"📄 Extracted details for post {i+1} ({len(post_details)} characters)")
                            else:
                                print(f"⚠️ No prose content found for post {i+1}")
                                
                        except Exception as detail_error:
                            print(f"⚠️ Error extracting details for post {i+1}: {str(detail_error)}")
                        
                        # Try to find a main link in the parent container
                        main_link = self.driver.current_url
                        try:
                            # Look for a link in the parent or nearby elements
                            parent = header.find_element(By.XPATH, "..")
                            link_element = parent.find_element(By.TAG_NAME, "a")
                            main_link = link_element.get_attribute("href")
                        except:
                            pass
                        
                        # Create unique ID based on title and time
                        post_id = hash(f"{post_title}{post_time}")
                        
                        post_data = {
                            'title': post_title,
                            'author': author,
                            'time': post_time,
                            'details': post_details,
                            'links': post_links,
                            'main_link': main_link,
                            'id': post_id,
                            'found_at': datetime.now().isoformat()
                        }
                        
                        current_posts.append(post_data)
                        print(f"✅ Parsed post {i+1}: {post_title[:50]}... ({len(post_details)} chars details)")
                        
                    except Exception as e:
                        print(f"⚠️ Error parsing feedHeader {i}: {str(e)}")
                        continue
                
                if len(current_posts) > 0:
                    print(f"📊 Successfully extracted {len(current_posts)} posts from feedHeader elements")
                    return current_posts
                    
            except Exception as e:
                print(f"⚠️ Error finding feedHeader elements: {str(e)}")
            
            # Fallback: if feedHeader approach fails, try generic selectors
            print("🔄 Trying fallback selectors...")
            fallback_selectors = [
                "div[class*='feed']",
                "div[class*='post']",
                "div[class*='card']",
                "article"
            ]
            
            for selector in fallback_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements and len(elements) > 0:
                        print(f"📋 Found {len(elements)} elements with fallback selector: {selector}")
                        
                        for i, element in enumerate(elements):
                            try:
                                element_text = element.text.strip()
                                if not element_text or len(element_text) < 10:
                                    continue
                                
                                # Try to find a link
                                link = self.driver.current_url
                                try:
                                    link_element = element.find_element(By.TAG_NAME, "a")
                                    link = link_element.get_attribute("href")
                                except:
                                    pass
                                
                                # Create basic post data
                                post_id = hash(element_text[:100])
                                title_lines = element_text.split('\n')
                                title = title_lines[0][:100] if title_lines else element_text[:50]
                                
                                post_data = {
                                    'title': title,
                                    'author': 'Unknown',
                                    'time': 'Unknown',
                                    'content': element_text,
                                    'link': link,
                                    'id': post_id,
                                    'found_at': datetime.now().isoformat()
                                }
                                current_posts.append(post_data)
                                
                            except Exception as e:
                                print(f"⚠️ Error parsing fallback element {i}: {str(e)}")
                                continue
                        
                        if len(current_posts) > 0:
                            break
                            
                except Exception as e:
                    continue
            
            # If still no posts found, save page source for debugging
            if len(current_posts) == 0:
                print("⚠️ No posts found with any selector. Saving page source for debugging...")
                with open('page_source_debug.html', 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                print("💾 Saved page source to page_source_debug.html for inspection")
            
            print(f"📊 Total posts found: {len(current_posts)}")
            return current_posts
            
        except Exception as e:
            print(f"❌ Error getting posts: {str(e)}")
            return []
    
    def check_new_posts(self):
        """Check for new posts by comparing titles with stored posts"""
        current_posts = self.get_posts()
        new_posts = []
        
        print(f"🔍 Comparing {len(current_posts)} current posts with {len(self.known_posts)} known posts...")
        
        for post in current_posts:
            post_title = post['title'].strip()
            
            # Check if this title already exists in known posts
            title_exists = post_title in self.known_posts
            
            if not title_exists:
                new_posts.append(post)
                # Store the full post data with title as key
                self.known_posts[post_title] = {
                    'title': post_title,
                    'author': post.get('author', ''),
                    'time': post.get('time', ''),
                    'details': post.get('details', ''),
                    'links': post.get('links', []),
                    'main_link': post.get('main_link', ''),
                    'first_seen': datetime.now().isoformat()
                }
                print(f"🆕 NEW POST DETECTED: {post_title}")
            else:
                print(f"✅ Known post: {post_title[:50]}...")
        
        if new_posts:
            print(f"\n🎉 FOUND {len(new_posts)} NEW POSTS! 🎉")
            print("=" * 60)
            for i, post in enumerate(new_posts, 1):
                print(f"{i}. {post['title']}")
            print("=" * 60)
            
            self.notify_new_posts(new_posts)
            self.save_known_posts()
        else:
            print("ℹ️ No new posts found this time")
        
        return new_posts
    
    def notify_new_posts(self, new_posts):
        """Send notifications for new posts"""
        print(f"\n🔔 {len(new_posts)} new post(s) found!")
        
        # Send desktop notification
        try:
            print("📱 Attempting to send desktop notification...")
            if len(new_posts) == 1:
                post = new_posts[0]
                message = f"{post['title'][:60]}..."
                if post.get('author'):
                    message += f"\nBy: {post['author']}"
                if post.get('time'):
                    message += f" • {post['time']}"
                
                notification.notify(
                    title="New Superset Post!",
                    message=message,
                    timeout=10
                )
                print("✅ Desktop notification sent successfully!")
            else:
                notification.notify(
                    title="New Superset Posts!",
                    message=f"{len(new_posts)} new posts found. Check the log for details.",
                    timeout=10
                )
                print("✅ Desktop notification sent successfully!")
        except Exception as e:
            print(f"⚠️ Desktop notification failed: {str(e)}")
            print("💡 You may need to install notification dependencies or check system permissions")
        
        for post in new_posts:
            print(f"📝 Title: {post['title']}")
            if post.get('author'):
                print(f"👤 Author: {post['author']}")
            if post.get('time'):
                print(f"⏰ Posted: {post['time']}")
            if post.get('details'):
                print(f"📄 Details: {post['details'][:200]}{'...' if len(post['details']) > 200 else ''}")
            if post.get('links'):
                print(f"🔗 Links found: {len(post['links'])}")
                for i, link in enumerate(post['links'][:3], 1):  # Show first 3 links
                    print(f"   {i}. {link['text']}: {link['url']}")
                if len(post['links']) > 3:
                    print(f"   ... and {len(post['links']) - 3} more links")
            print(f"📅 Found at: {post['found_at']}")
            if post.get('main_link'):
                print(f"🔗 Main Link: {post['main_link']}")
            print("-" * 50)
        
        # Log to file
        self.log_new_posts(new_posts)
    
    def log_new_posts(self, new_posts):
        """Log new posts to file with detailed information"""
        with open('new_posts.log', 'a', encoding='utf-8') as f:
            for post in new_posts:
                f.write(f"\n{'='*80}\n")
                f.write(f"NEW POST FOUND: {datetime.now()}\n")
                f.write(f"{'='*80}\n")
                f.write(f"Title: {post['title']}\n")
                
                if post.get('author'):
                    f.write(f"Author: {post['author']}\n")
                if post.get('time'):
                    f.write(f"Posted: {post['time']}\n")
                
                if post.get('details'):
                    f.write(f"\nDetails:\n{post['details']}\n")
                
                if post.get('links'):
                    f.write(f"\nLinks found ({len(post['links'])}):\n")
                    for i, link in enumerate(post['links'], 1):
                        f.write(f"  {i}. {link['text']}: {link['url']}\n")
                
                if post.get('main_link'):
                    f.write(f"\nMain Link: {post['main_link']}\n")
                
                f.write(f"Found at: {post['found_at']}\n")
                f.write(f"{'='*80}\n\n")
    
    def load_known_posts(self):
        """Load previously seen posts from file"""
        try:
            with open('known_posts.json', 'r', encoding='utf-8') as f:
                self.known_posts = json.load(f)
                if not isinstance(self.known_posts, dict):
                    # Handle old format (set/list) by converting to dict
                    self.known_posts = {}
        except FileNotFoundError:
            self.known_posts = {}
        except json.JSONDecodeError:
            print("⚠️ Error reading known_posts.json, starting fresh")
            self.known_posts = {}
    
    def save_known_posts(self):
        """Save known posts to file"""
        try:
            with open('known_posts.json', 'w', encoding='utf-8') as f:
                json.dump(self.known_posts, f, indent=2, ensure_ascii=False)
            print(f"💾 Saved {len(self.known_posts)} known posts to file")
        except Exception as e:
            print(f"⚠️ Error saving known posts: {str(e)}")
    
    def show_statistics(self):
        """Show statistics about stored posts"""
        print(f"\n📊 Post Statistics:")
        print(f"   Total known posts: {len(self.known_posts)}")
        
        if len(self.known_posts) > 0:
            # Count posts with details and links
            posts_with_details = sum(1 for data in self.known_posts.values() if data.get('details'))
            posts_with_links = sum(1 for data in self.known_posts.values() if data.get('links'))
            total_links = sum(len(data.get('links', [])) for data in self.known_posts.values())
            
            print(f"   Posts with details: {posts_with_details}")
            print(f"   Posts with links: {posts_with_links}")
            print(f"   Total links found: {total_links}")
            
            # Show most recent posts - sort by actual post time, not discovery time
            def parse_time_ago(time_str):
                """Convert '2 hours ago', '3 days ago' etc. to a sortable number"""
                if not time_str or time_str == 'Unknown':
                    return float('inf')  # Put unknown times at the end
                
                time_str = time_str.lower().strip()
                
                # Extract number and unit
                parts = time_str.split()
                if len(parts) < 2:
                    return float('inf')
                
                try:
                    number = int(parts[0])
                    unit = parts[1]
                    
                    # Convert to minutes for comparison
                    if 'minute' in unit:
                        return number
                    elif 'hour' in unit:
                        return number * 60
                    elif 'day' in unit:
                        return number * 60 * 24
                    elif 'week' in unit:
                        return number * 60 * 24 * 7
                    elif 'month' in unit:
                        return number * 60 * 24 * 30
                    else:
                        return float('inf')
                except:
                    return float('inf')
            
            # Sort by actual post time (most recent first = smallest time_ago value)
            recent_posts = sorted(
                self.known_posts.items(), 
                key=lambda x: parse_time_ago(x[1].get('time', '')),
                reverse=False  # False because smaller time_ago means more recent
            )[:3]
            
            print(f"   Most recent posts:")
            for i, (title, data) in enumerate(recent_posts, 1):
                author = data.get('author', 'Unknown')
                time_posted = data.get('time', 'Unknown')
                details_length = len(data.get('details', ''))
                links_count = len(data.get('links', []))
                first_seen = data.get('first_seen', 'Unknown')
                
                print(f"     {i}. {title[:50]}...")
                print(f"        By: {author} • {time_posted}")
                print(f"        First seen: {first_seen}")
                if details_length > 0:
                    print(f"        Details: {details_length} characters")
                if links_count > 0:
                    print(f"        Links: {links_count} found")
        print()
    
    def run_once(self, headless=True):
        """Run a single check"""
        if not self.setup_driver(headless=headless):
            return False
        
        try:
            if self.login():
                new_posts = self.check_new_posts()
                print(f"✅ Check completed at {datetime.now()}")
                return len(new_posts) > 0
            else:
                return False
        finally:
            if self.driver:
                self.driver.quit()
    
    def run_continuous(self):
        """Run continuous monitoring"""
        print(f"🚀 Starting Superset Post Monitor")
        print(f"⏰ Checking every {self.check_interval} seconds")
        
        while True:
            try:
                self.run_once()
                self.show_statistics()
                print(f"💤 Sleeping for {self.check_interval} seconds...")
                time.sleep(self.check_interval)
            except KeyboardInterrupt:
                print("\n👋 Monitoring stopped by user")
                break
            except Exception as e:
                print(f"❌ Error in monitoring loop: {str(e)}")
                time.sleep(60)  # Wait 1 minute before retrying

if __name__ == "__main__":
    monitor = SupersetPostMonitor()
    
    # Run once for testing
    print("🧪 Running single check...")
    monitor.run_once()
    
    # Uncomment below to run continuous monitoring
    # monitor.run_continuous()