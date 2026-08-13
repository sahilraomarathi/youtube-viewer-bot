import asyncio
import random
import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

class LiveStreamViewer:
    def __init__(self, viewer_id=1):
        self.driver = None
        self.viewer_id = viewer_id
        self.is_watching = False

    def setup_browser(self):
        """Initialize the Chrome browser with stealth settings (synchronous)"""
        options = Options()

        # Create user data directory for this viewer
        current_dir = os.path.abspath(os.getcwd())
        user_data_dir = os.path.join(current_dir, "chrome_profiles", f"viewer_{self.viewer_id}")
        user_data_dir = os.path.normpath(user_data_dir)

        success = self.create_user_data_dir(user_data_dir)
        if not success:
            import tempfile
            user_data_dir = os.path.join(tempfile.gettempdir(), f"youtube_viewer_{self.viewer_id}")
            self.log(f"Using fallback temp directory: {user_data_dir}")
            self.create_user_data_dir(user_data_dir)

        # Stealth settings
        options.add_argument("--no-first-run")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions-except")
        options.add_argument("--disable-plugins-discovery")

        # Cloud hosting compatibility
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu-sandbox")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disable-gpu")
        options.add_argument("--headless=new")  # Use new headless mode

        # Random window size
        width = random.randint(1024, 1920)
        height = random.randint(768, 1080)
        options.add_argument(f"--window-size={width},{height}")

        # Random user agent
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        selected_ua = random.choice(user_agents)
        options.add_argument(f"--user-agent={selected_ua}")

        # Separate profile per viewer
        options.add_argument(f"--user-data-dir={user_data_dir}")

        # Mobile simulation (30% chance)
        if random.random() < 0.3:
            options.add_argument("--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1")
            width = random.randint(375, 414)
            height = random.randint(667, 896)
            options.add_argument(f"--window-size={width},{height}")

        self.log(f"Using profile directory: {user_data_dir}")

        # Create driver with ChromeDriverManager
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)

        # Set timezone via CDP (synchronous)
        self.driver.execute_cdp_cmd('Emulation.setTimezoneOverride', {
            'timezoneId': random.choice(['America/New_York', 'America/Los_Angeles', 'Europe/London', 'Europe/Paris', 'Asia/Tokyo'])
        })

        self.log(f"Browser setup complete - UA: {selected_ua[:50]}...")

    def create_user_data_dir(self, user_data_dir):
        """Create user data directory if it doesn't exist"""
        try:
            if not os.path.exists(user_data_dir):
                os.makedirs(user_data_dir, exist_ok=True)
                print(f"📁 Created profile directory: {user_data_dir}")
            else:
                print(f"📁 Using existing profile: {user_data_dir}")

            # Test write permissions
            test_file = os.path.join(user_data_dir, "test_write.tmp")
            try:
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
                print(f"✅ Write permissions confirmed for: {user_data_dir}")
                return True
            except Exception as e:
                print(f"❌ No write permissions for {user_data_dir}: {e}")
                return False
        except Exception as e:
            print(f"⚠️ Warning: Could not create profile directory {user_data_dir}: {e}")
            return False

    def human_delay(self, min_seconds=1, max_seconds=3):
        """Synchronous human-like delay"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)

    def log(self, message):
        """Log with viewer ID and timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] Viewer {self.viewer_id}: {message}")

    def is_stream_live(self):
        """Check if the stream is currently live"""
        try:
            live_indicators = self.driver.execute_script("""
                return {
                    liveBadge: !!document.querySelector('.ytp-live-badge'),
                    liveText: document.body.innerText.includes('LIVE'),
                    streamEnded: document.body.innerText.includes('stream has ended') || 
                                document.body.innerText.includes('This live stream has ended'),
                    videoExists: !!document.querySelector('video')
                };
            """)

            if live_indicators.get('streamEnded'):
                self.log("Stream has ended")
                return False

            return live_indicators.get('liveBadge') or live_indicators.get('liveText')

        except Exception as e:
            self.log(f"Error checking stream status: {e}")
            return False

    def handle_youtube_overlays(self):
        """Handle common YouTube overlays"""
        try:
            # Cookie consent
            cookie_selectors = [
                "//button[contains(text(), 'Accept all')]",
                "//button[contains(text(), 'I agree')]",
                "[aria-label*='Accept']"
            ]

            for selector in cookie_selectors:
                try:
                    if selector.startswith("//"):
                        button = self.driver.find_element(By.XPATH, selector)
                    else:
                        button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    button.click()
                    self.log("Accepted cookies")
                    self.human_delay(1, 2)
                    break
                except:
                    continue

            # Age verification
            age_selectors = [
                "button[aria-label*='Continue']",
                "#confirm-button"
            ]

            for selector in age_selectors:
                try:
                    button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    button.click()
                    self.log("Passed age verification")
                    self.human_delay(1, 2)
                    break
                except:
                    continue

        except Exception as e:
            self.log(f"Error handling overlays: {e}")

    def simulate_viewer_behavior(self):
        """Simulate realistic viewer behavior during stream"""
        behaviors = [
            'scroll_chat',
            'scroll_video',
            'pause_resume',
            'volume_adjust',
            'fullscreen_toggle',
            'nothing'
        ]

        action = random.choice(behaviors)

        try:
            if action == 'scroll_chat':
                self.driver.execute_script("window.scrollBy(0, 100);")
                self.log("Scrolled chat")

            elif action == 'scroll_video':
                scroll_amount = random.randint(50, 200)
                self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                self.log("Scrolled page")

            elif action == 'pause_resume':
                if random.random() < 0.1:
                    try:
                        video = self.driver.find_element(By.CSS_SELECTOR, "video")
                        video.click()  # Pause
                        self.human_delay(2, 5)
                        video.click()  # Resume
                        self.log("Paused and resumed")
                    except:
                        pass

            elif action == 'volume_adjust':
                if random.random() < 0.05:
                    volume = random.uniform(0.3, 1.0)
                    self.driver.execute_script(f"document.querySelector('video').volume = {volume};")
                    self.log(f"Adjusted volume to {volume:.2f}")

            elif action == 'fullscreen_toggle':
                if random.random() < 0.02:
                    try:
                        fullscreen_btn = self.driver.find_element(By.CSS_SELECTOR, ".ytp-fullscreen-button")
                        fullscreen_btn.click()
                        self.human_delay(3, 8)
                        fullscreen_btn.click()
                        self.log("Toggled fullscreen")
                    except:
                        pass

        except Exception as e:
            self.log(f"Error in behavior simulation: {e}")

    def verify_connection(self):
        """Verify that this viewer is properly connected and counted"""
        try:
            viewer_count = self.driver.execute_script("""
                const selectors = [
                    '.view-count',
                    '.style-scope.ytd-video-view-count-renderer',
                    '[class*="view-count"]',
                    '.ytp-title-channel'
                ];
                for (let selector of selectors) {
                    const element = document.querySelector(selector);
                    if (element && element.textContent.includes('watching')) {
                        return element.textContent;
                    }
                }
                const bodyText = document.body.innerText;
                const watchingMatch = bodyText.match(/(\\d+)\\s*watching/i);
                if (watchingMatch) {
                    return watchingMatch[0];
                }
                return 'Not found';
            """)

            video_status = self.driver.execute_script("""
                const video = document.querySelector('video');
                if (!video) return 'No video element';
                return {
                    playing: !video.paused && !video.ended,
                    currentTime: video.currentTime,
                    duration: video.duration,
                    readyState: video.readyState
                };
            """)

            self.log(f"Connection verified - Viewer count: {viewer_count}, Video status: {video_status}")
            return True

        except Exception as e:
            self.log(f"Error verifying connection: {e}")
            return False

    def watch_live_stream(self, stream_url, max_duration_minutes=None):
        """Watch a live stream with realistic behavior (synchronous)"""
        self.log(f"Starting to watch live stream: {stream_url}")

        try:
            self.driver.get(stream_url)
            self.human_delay(8, 12)

            self.handle_youtube_overlays()

            if not self.is_stream_live():
                self.log("❌ Stream is not live or not found")
                return False

            self.log("✅ Stream is live! Starting to watch...")

            try:
                video = self.driver.find_element(By.CSS_SELECTOR, "video")
                video.click()
                self.human_delay(3, 5)

                self.driver.execute_script("""
                    const video = document.querySelector('video');
                    if (video && video.paused) {
                        video.play();
                    }
                """)
            except Exception as e:
                self.log(f"Error starting video: {e}")

            self.human_delay(10, 15)
            self.verify_connection()

            self.is_watching = True
            start_time = time.time()
            max_duration_seconds = max_duration_minutes * 60 if max_duration_minutes else float('inf')

            loop_count = 0
            while self.is_watching:
                loop_count += 1

                if not self.is_stream_live():
                    self.log("Stream ended, stopping viewer")
                    break

                if time.time() - start_time > max_duration_seconds:
                    self.log(f"Reached max duration of {max_duration_minutes} minutes")
                    break

                if loop_count % 10 == 0:
                    self.verify_connection()

                self.simulate_viewer_behavior()

                wait_time = random.uniform(60, 180)
                time.sleep(wait_time)  # Blocking, but we run in a thread

            self.log("✅ Finished watching stream")
            return True

        except Exception as e:
            self.log(f"❌ Error watching stream: {e}")
            return False
        finally:
            self.is_watching = False

    def stop_watching(self):
        """Stop watching the stream"""
        self.is_watching = False
        self.log("Stopping stream viewer")

    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            self.log("Browser closed")

# Multi-viewer manager (async, uses threads for each viewer)
class MultiViewerManager:
    def __init__(self):
        self.viewers = []

    async def start_viewer_with_delay(self, viewer, stream_url, delay, max_duration_minutes):
        """Start a viewer with initial delay, run its watch in a thread"""
        await asyncio.sleep(delay)
        try:
            # Run the synchronous watch in a thread to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,  # default executor (ThreadPoolExecutor)
                self._run_viewer,
                viewer,
                stream_url,
                max_duration_minutes
            )
            return result
        except Exception as e:
            viewer.log(f"Viewer failed: {e}")
            return False
        finally:
            await asyncio.to_thread(viewer.close)

    def _run_viewer(self, viewer, stream_url, max_duration_minutes):
        """Wrapper to set up and watch (runs in a thread)"""
        try:
            viewer.setup_browser()
            return viewer.watch_live_stream(stream_url, max_duration_minutes)
        except Exception as e:
            viewer.log(f"Error in viewer thread: {e}")
            return False

    async def create_viewers(self, count, stream_url, max_duration_minutes=None):
        """Create multiple viewers concurrently"""
        print(f"🚀 Creating {count} viewers for stream: {stream_url}")
        print(f"⏰ Viewers will start with 0-60 second delays for better distribution")

        tasks = []
        for i in range(1, count + 1):
            viewer = LiveStreamViewer(viewer_id=i)
            self.viewers.append(viewer)

            start_delay = random.uniform(0, 60)
            task = asyncio.create_task(
                self.start_viewer_with_delay(viewer, stream_url, start_delay, max_duration_minutes)
            )
            tasks.append(task)

        # Monitor viewers periodically (async)
        monitor_task = asyncio.create_task(self.monitor_viewers())

        results = await asyncio.gather(*tasks, return_exceptions=True)
        monitor_task.cancel()

        successful = sum(1 for r in results if r is True)
        failed = len(results) - successful
        print(f"📊 Final Results: {successful} successful, {failed} failed viewers")

    async def monitor_viewers(self):
        """Monitor active viewers and report status"""
        try:
            while True:
                await asyncio.sleep(120)  # Check every 2 minutes
                active_count = sum(1 for viewer in self.viewers if viewer.is_watching)
                print(f"📈 Status Update: {active_count}/{len(self.viewers)} viewers currently active")
        except asyncio.CancelledError:
            pass

    async def stop_all_viewers(self):
        """Stop all viewers"""
        print("Stopping all viewers...")
        for viewer in self.viewers:
            await asyncio.to_thread(viewer.stop_watching)

async def main():
    # Configuration - override with environment variables if needed
    STREAM_URL = os.getenv("STREAM_URL", "https://www.youtube.com/watch?v=QmgZJmzL-0U")
    VIEWER_COUNT = int(os.getenv("VIEWER_COUNT", "3"))
    MAX_DURATION_MINUTES = int(os.getenv("MAX_DURATION_MINUTES", "0") or 0)  # 0 = unlimited

    manager = MultiViewerManager()

    try:
        await manager.create_viewers(VIEWER_COUNT, STREAM_URL, MAX_DURATION_MINUTES if MAX_DURATION_MINUTES > 0 else None)
        print(f"🎉 All {VIEWER_COUNT} viewers completed!")

    except KeyboardInterrupt:
        print("\n⏹️ Stopping all viewers...")
        await manager.stop_all_viewers()
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
