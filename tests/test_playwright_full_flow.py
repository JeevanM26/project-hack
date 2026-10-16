from playwright.sync_api import sync_playwright
import time

def test_full_youtube_flow():
    p = sync_playwright().start()
    b = p.chromium.launch(channel="msedge", headless=True)
    page = b.new_page()

    # 1. Open YouTube
    page.goto("https://www.youtube.com", timeout=15000)
    print("1. Opened YouTube")

    # 2. Search
    search_sel = 'input[name="search_query"], input#search'
    page.wait_for_selector(search_sel, timeout=10000)
    page.fill(search_sel, "Kesariya")
    page.press(search_sel, "Enter")
    print("2. Searched Kesariya")

    # 3. Play first video
    page.wait_for_selector('a#video-title', timeout=10000)
    first_vid = page.query_selector('a#video-title')
    assert first_vid is not None
    first_vid.click()
    print("3. Clicked first video")
    time.sleep(2)

    # 4. Pause
    page.keyboard.press("k")
    print("4. Toggled pause")

    # 5. Close
    b.close()
    p.stop()
    print("5. Closed cleanly!")

if __name__ == "__main__":
    test_full_youtube_flow()
