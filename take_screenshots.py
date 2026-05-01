from playwright.sync_api import sync_playwright
import time

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        
        # 1. Home Page screenshot
        page.goto('http://127.0.0.1:5000')
        print("Waiting for Home page to load...")
        time.sleep(3)
        page.screenshot(path='home_screen.jpg')
        print("Captured Home page.")
        
        # 2. Add Booking modal/view if possible. Or just Admin Page.
        page.goto('http://127.0.0.1:5000/admin.html')
        print("Waiting for Admin page to load...")
        time.sleep(3)
        page.screenshot(path='admin_screen.jpg')
        print("Captured Admin page.")
        
        browser.close()

if __name__ == '__main__':
    main()
