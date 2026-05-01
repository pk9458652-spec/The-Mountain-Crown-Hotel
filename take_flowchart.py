from playwright.sync_api import sync_playwright
import time
import os

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 800, "height": 900})
        
        filepath = "file:///" + os.path.abspath("flowchart.html").replace("\\", "/")
        print("Loading flowchart:", filepath)
        page.goto(filepath)
        
        print("Waiting for flowchart to render...")
        time.sleep(3) # Wait for CDN script and mermaid rendering
        
        page.screenshot(path='flowchart_screen.jpg', full_page=True)
        print("Captured Flowchart.")
        
        browser.close()

if __name__ == '__main__':
    main()
