import threading
import queue
import time
from playwright.sync_api import sync_playwright

class BrowserWorker(threading.Thread):
    def __init__(self, headless=True):
        super().__init__(daemon=True)
        self.cmd_queue = queue.Queue()
        self.running = True
        self.headless = headless
        self.page = None
        self.browser = None
        self.p = None

    def run(self):
        self.p = sync_playwright().start()
        self.browser = self.p.chromium.launch(channel="msedge", headless=self.headless)
        self.page = self.browser.new_page()
        while self.running:
            item = self.cmd_queue.get()
            if item is None:
                break
            cmd, args, res_q = item
            try:
                if cmd == "goto":
                    self.page.goto(args["url"], timeout=15000)
                    res_q.put(("ok", self.page.title()))
                elif cmd == "search_yt":
                    # YouTube search input selector
                    selector = 'input[name="search_query"], input#search'
                    self.page.wait_for_selector(selector, timeout=8000)
                    self.page.fill(selector, args["query"])
                    self.page.press(selector, "Enter")
                    self.page.wait_for_selector('a#video-title', timeout=10000)
                    res_q.put(("ok", f"searched {args['query']}"))
                elif cmd == "play_first":
                    first_link = self.page.wait_for_selector('a#video-title', timeout=10000)
                    if first_link:
                        first_link.click()
                        res_q.put(("ok", "clicked first video"))
                    else:
                        res_q.put(("error", "no video found"))
                elif cmd == "pause_resume":
                    # Press k to pause/resume
                    self.page.keyboard.press("k")
                    res_q.put(("ok", "toggled pause/resume"))
                elif cmd == "close":
                    if self.page and not self.page.is_closed():
                        self.page.close()
                    res_q.put(("ok", "closed page"))
            except Exception as e:
                res_q.put(("error", str(e)))

    def execute(self, cmd, **kwargs):
        res_q = queue.Queue()
        self.cmd_queue.put((cmd, kwargs, res_q))
        return res_q.get(timeout=25)

    def shutdown(self):
        self.running = False
        self.cmd_queue.put(None)
        if self.browser:
            try:
                self.browser.close()
            except Exception:
                pass
        if self.p:
            try:
                self.p.stop()
            except Exception:
                pass

if __name__ == "__main__":
    w = BrowserWorker(headless=True)
    w.start()
    time.sleep(1)
    status, title = w.execute("goto", url="https://www.youtube.com")
    print("Goto status:", status, "Title:", title)
    status, search_res = w.execute("search_yt", query="Kesariya")
    print("Search status:", status, "Res:", search_res)
    status, play_res = w.execute("play_first")
    print("Play status:", status, "Res:", play_res)
    time.sleep(2)
    status, close_res = w.execute("close")
    print("Close status:", status, "Res:", close_res)
    w.shutdown()
    print("Done!")
