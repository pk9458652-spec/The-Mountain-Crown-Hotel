from playwright.sync_api import sync_playwright
import time
import os

def screenshot(page, html_file, output_file, width=1200, height=800):
    filepath = "file:///" + os.path.abspath(html_file).replace("\\", "/")
    print(f"Loading: {filepath}")
    page.set_viewport_size({"width": width, "height": height})
    page.goto(filepath)
    time.sleep(2)
    # Target large capture
    page.screenshot(path=output_file, full_page=True)
    print(f"Saved: {output_file}")

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Use a higher scale factor for print quality
        context = browser.new_context(device_scale_factor=3) 
        page = context.new_page()

        # 1. Diagrams (High Resolution)
        screenshot(page, "dfd.html",       "dfd_screen.jpg",       1400, 600)
        screenshot(page, "er_diagram.html","er_screen.jpg",        1200, 800)
        screenshot(page, "flowchart.html", "flowchart_screen.jpg", 1000, 1200)

        # 2. Website Screenshots
        page.set_viewport_size({"width": 1440, "height": 900})
        page.goto("http://127.0.0.1:5000")
        time.sleep(4)
        page.screenshot(path="home_screen.jpg")
        print("Saved: home_screen.jpg")

        # Rooms
        page.evaluate("window.scrollTo(0, 800)")
        time.sleep(1)
        page.screenshot(path="rooms_screen.jpg")
        print("Saved: rooms_screen.jpg")

        # Gallery
        page.evaluate("window.scrollTo(0, 1600)")
        time.sleep(1)
        page.screenshot(path="gallery_screen.jpg")
        print("Saved: gallery_screen.jpg")

        # 3. Admin Landing (Real Dashboard)
        page.goto("http://127.0.0.1:5000/admin.html")
        time.sleep(2)
        print("Logging into admin...")
        page.fill("#admin-pass", "admin123")
        page.click("button:has-text('Access Dashboard')")
        time.sleep(3) # Wait for bookings to load
        page.screenshot(path="admin_screen.jpg", full_page=True)
        print("Saved: admin_screen.jpg (Real Dashboard)")

        browser.close()

if __name__ == '__main__':
    main()

