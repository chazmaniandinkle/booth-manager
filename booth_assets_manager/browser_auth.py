import os
import json
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright
from .settings import settings

class BrowserAuth:
    """
    Browser-based authentication for Booth using Playwright.
    Opens a browser window for the user to log in, then captures the cookies.
    """
    def __init__(self):
        self.cookies_path = os.path.join(os.path.dirname(settings.config_path), "booth_cookies.json")
        self.auth_timeout = 300  # 5 minutes to log in
    
    async def interactive_login(self):
        """
        Open a browser window and let the user log in to Booth.
        Returns True if login was successful and cookies were saved.
        """
        async with async_playwright() as p:
            # Launch the browser (not headless so user can see and interact with it)
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Go to Booth login page
            await page.goto("https://booth.pm/users/sign_in")
            
            print("\n=== Booth Authentication ===")
            print("A browser window has opened. Please log in to your Booth account.")
            print("This window will close automatically after successful login.")
            print("You have 5 minutes to complete the login process.\n")
            
            # Wait for login to complete by checking either:
            # 1. Navigation to dashboard after login
            # 2. Presence of user-specific elements
            
            try:
                # Wait for either login success or timeout
                login_success = False
                
                for _ in range(self.auth_timeout):
                    # Check if we're on a page that indicates successful login
                    current_url = page.url
                    if "/users/sign_in" not in current_url and "/sign_up" not in current_url:
                        # Additional check - look for user account elements
                        user_menu = await page.query_selector(".user-dropdown-menu")
                        if user_menu:
                            login_success = True
                            break
                    
                    # Wait a second before checking again
                    await asyncio.sleep(1)
                
                if not login_success:
                    print("Login timed out or was unsuccessful.")
                    await browser.close()
                    return False
                
                # Successfully logged in, get cookies
                cookies = await context.cookies()
                
                # Save cookies to file
                os.makedirs(os.path.dirname(self.cookies_path), exist_ok=True)
                with open(self.cookies_path, 'w', encoding='utf-8') as f:
                    json.dump(cookies, f, indent=2)
                
                # Save auth info in settings
                settings.set("auth_cookies_file", self.cookies_path)
                settings.set("last_login", datetime.utcnow().isoformat())
                settings.save()
                
                print("\nLogin successful! Cookies saved for future sessions.")
                await browser.close()
                return True
                
            except Exception as e:
                print(f"Error during login process: {e}")
                await browser.close()
                return False
    
    def is_authenticated(self):
        """Check if we have valid authentication cookies."""
        if not os.path.exists(self.cookies_path):
            return False
        
        try:
            # Load cookies
            with open(self.cookies_path, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            
            # Check for required Booth cookies
            booth_cookies = [c for c in cookies if 'booth.pm' in c.get('domain', '')]
            session_cookies = [c for c in booth_cookies if c.get('name') == '_plaza_session']
            
            return len(session_cookies) > 0
            
        except Exception as e:
            print(f"Error checking authentication: {e}")
            return False
    
    async def verify_auth_status(self):
        """
        Verify if the saved cookies still provide authentication.
        Returns True if authenticated, False otherwise.
        """
        if not self.is_authenticated():
            return False
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                
                # Load cookies
                with open(self.cookies_path, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
                
                await context.add_cookies(cookies)
                page = await context.new_page()
                
                # Visit account settings - redirects to login if not authenticated
                await page.goto('https://booth.pm/settings')
                
                # Check if we're still on the settings page (authenticated)
                is_auth = '/users/sign_in' not in page.url
                
                await browser.close()
                return is_auth
                
        except Exception as e:
            print(f"Error verifying authentication: {e}")
            return False

# Helper function to run the async login process
def interactive_login():
    """Run the interactive login process and return True if successful."""
    auth = BrowserAuth()
    return asyncio.run(auth.interactive_login())

# Helper function to check authentication status
def check_auth_status():
    """Check if the current saved auth is valid."""
    auth = BrowserAuth()
    return asyncio.run(auth.verify_auth_status())
