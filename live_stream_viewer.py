import asyncio
import random
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time
from datetime import datetime

class LiveStreamViewer:
    def __init__(self, viewer_id=1):
        self.driver = None
        self.viewer_id = viewer_id
        self.is_watching = False
        
    async def setup_browser(self):
        """Initialize the driverless browser with stealth settings"""
        options = webdriver.ChromeOptions()
        
        # Create user data directory for this viewer (use absolute path for Windows)
        current_dir = os.path.abspath(os.getcwd())
        user_data_dir = os.path.join(current_dir, "chrome_profiles", f"viewer_{self.viewer_id}")
        
        # Convert to Windows-friendly path
        user_data_dir = os.path.normpath(user_data_dir)
        
        success = self.create_user_data_dir(user_data_dir)
        if not success:
            # Fallback: use temp directory
            import tempfile
            user_data_dir = os.path.join(tempfile.gettempdir(), f"youtube_viewer_{self.viewer_id}")
            await self.log(f"Using fallback temp directory: {user_data_dir}")
            self.create_user_data_dir(user_data_dir)
        
        # Safe stealth settings
        options.add_argument("--no-first-run")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions-except")
        options.add_argument("--disable-plugins-discovery")
        
        # Cloud hosting compatibility fixes
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu-sandbox")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disable-gpu")
        options.add_argument("--headless")  # Required for cloud hosting
        
        # Randomize window size for each viewer (more variety)
        width = random.randint(1024, 1920)
        height = random.randint(768, 1080)
        options.add_argument(f"--window-size={width},{height}")
        
        # Different user agents for better differentiation
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        
        selected_ua = random.choice(user_agents)
        options.add_argument(f"--user-agent={selected_ua}")
        
        # Use different user data directories for each viewer (CRITICAL for separate sessions!)
        options.add_argument(f"--user-data-dir={user_data_dir}")
        
        # Random viewport and device settings
        if random.random() < 0.3:  # 30% chance of mobile simulation
            options.add_argument("--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1")
            width = random.randint(375, 414)
            height = random.randint(667, 896)
            options.add_argument(f"--window-size={width},{height}")
        
        await self.log(f"Using profile directory: {user_data_dir}")
        
        self.driver = await webdriver.Chrome(options=options)
        
        # Set random timezone and language
        await self.driver.execute_cdp_cmd('Emulation.setTimezoneOverride', {
            'timezoneId': random.choice(['America/New_York', 'America/Los_Angeles', 'Europe/London', 'Europe/Paris', 'Asia/Tokyo'])
        })
        
        await self.log(f"Browser setup complete - UA: {selected_ua[:50]}...")
    
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
        
    async def human_delay(self, min_seconds=1, max_seconds=3):
        """Add human-like random delays"""
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)
        
    async def log(self, message):
        """Log with viewer ID and timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] Viewer {self.viewer_id}: {message}")
        
    async def is_stream_live(self):
        """Check if the stream is currently live"""
        try:
            # Check for live indicators
            live_indicators = await self.driver.execute_script("""
                return {
                    liveBadge: !!document.querySelector('.ytp-live-badge'),
                    liveText: document.body.innerText.includes('LIVE'),
                    streamEnded: document.body.innerText.includes('stream has ended') || 
                                document.body.innerText.includes('This live stream has ended'),
                    videoExists: !!document.querySelector('video')
                };
            """)
            
            if live_indicators.get('streamEnded'):
                await self.log("Stream has ended")
                return False
                
            return live_indicators.get('liveBadge') or live_indicators.get('liveText')
            
        except Exception as e:
            await self.log(f"Error checking stream status: {e}")
            return False
    
    async def handle_youtube_overlays(self):
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
                        button = await self.driver.find_element(By.XPATH, selector)
                    else:
                        button = await self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    await button.click()
                    await self.log("Accepted cookies")
                    await self.human_delay(1, 2)
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
                    button = await self.driver.find_element(By.CSS_SELECTOR, selector)
                    await button.click()
                    await self.log("Passed age verification")
                    await self.human_delay(1, 2)
                    break
                except:
                    continue
                    
        except Exception as e:
            await self.log(f"Error handling overlays: {e}")
    
    async def simulate_viewer_behavior(self):
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
                # Scroll in chat area
                await self.driver.execute_script("window.scrollBy(0, 100);")
                await self.log("Scrolled chat")
                
            elif action == 'scroll_video':
                # Scroll page slightly
                scroll_amount = random.randint(50, 200)
                await self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                await self.log("Scrolled page")
                
            elif action == 'pause_resume':
                if random.random() < 0.1:  # 10% chance
                    try:
                        video = await self.driver.find_element(By.CSS_SELECTOR, "video")
                        await video.click()  # Pause
                        await self.human_delay(2, 5)
                        await video.click()  # Resume
                        await self.log("Paused and resumed")
                    except:
                        pass
                        
            elif action == 'volume_adjust':
                if random.random() < 0.05:  # 5% chance
                    volume = random.uniform(0.3, 1.0)
                    await self.driver.execute_script(f"document.querySelector('video').volume = {volume};")
                    await self.log(f"Adjusted volume to {volume:.2f}")
                    
            elif action == 'fullscreen_toggle':
                if random.random() < 0.02:  # 2% chance
                    try:
                        fullscreen_btn = await self.driver.find_element(By.CSS_SELECTOR, ".ytp-fullscreen-button")
                        await fullscreen_btn.click()
                        await self.human_delay(3, 8)
                        await fullscreen_btn.click()  # Exit fullscreen
                        await self.log("Toggled fullscreen")
                    except:
                        pass
                        
        except Exception as e:
            await self.log(f"Error in behavior simulation: {e}")
    
    async def verify_connection(self):
        """Verify that this viewer is properly connected and counted"""
        try:
            # Get current viewer count from the page
            viewer_count = await self.driver.execute_script("""
                // Try multiple selectors for viewer count
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
                
                // Check if we can find any viewer count indicator
                const bodyText = document.body.innerText;
                const watchingMatch = bodyText.match(/(\\d+)\\s*watching/i);
                if (watchingMatch) {
                    return watchingMatch[0];
                }
                
                return 'Not found';
            """)
            
            # Check if video is actually playing
            video_status = await self.driver.execute_script("""
                const video = document.querySelector('video');
                if (!video) return 'No video element';
                
                return {
                    playing: !video.paused && !video.ended,
                    currentTime: video.currentTime,
                    duration: video.duration,
                    readyState: video.readyState
                };
            """)
            
            await self.log(f"Connection verified - Viewer count: {viewer_count}, Video status: {video_status}")
            return True
            
        except Exception as e:
            await self.log(f"Error verifying connection: {e}")
            return False
    
    async def watch_live_stream(self, stream_url, max_duration_minutes=None):
        """Watch a live stream with realistic behavior"""
        await self.log(f"Starting to watch live stream: {stream_url}")
        
        try:
            # Navigate to stream
            await self.driver.get(stream_url)
            await self.human_delay(8, 12)  # Longer initial wait
            
            # Handle overlays
            await self.handle_youtube_overlays()
            
            # Check if stream is live
            if not await self.is_stream_live():
                await self.log("❌ Stream is not live or not found")
                return False
            
            await self.log("✅ Stream is live! Starting to watch...")
            
            # Start the video if needed
            try:
                video = await self.driver.find_element(By.CSS_SELECTOR, "video")
                await video.click()
                await self.human_delay(3, 5)
                
                # Ensure video is playing
                await self.driver.execute_script("""
                    const video = document.querySelector('video');
                    if (video && video.paused) {
                        video.play();
                    }
                """)
            except Exception as e:
                await self.log(f"Error starting video: {e}")
            
            # Wait a bit more for YouTube to register the viewer
            await self.human_delay(10, 15)
            
            # Verify connection
            await self.verify_connection()
            
            self.is_watching = True
            start_time = time.time()
            max_duration_seconds = max_duration_minutes * 60 if max_duration_minutes else float('inf')
            
            # Main watching loop
            loop_count = 0
            while self.is_watching:
                loop_count += 1
                
                # Check if stream is still live
                if not await self.is_stream_live():
                    await self.log("Stream ended, stopping viewer")
                    break
                
                # Check max duration
                if time.time() - start_time > max_duration_seconds:
                    await self.log(f"Reached max duration of {max_duration_minutes} minutes")
                    break
                
                # Verify connection every 10 loops (roughly every 10-20 minutes)
                if loop_count % 10 == 0:
                    await self.verify_connection()
                
                # Simulate viewer behavior
                await self.simulate_viewer_behavior()
                
                # Wait before next action (60-180 seconds for more realistic behavior)
                wait_time = random.uniform(60, 180)
                await asyncio.sleep(wait_time)
            
            await self.log("✅ Finished watching stream")
            return True
            
        except Exception as e:
            await self.log(f"❌ Error watching stream: {e}")
            return False
        finally:
            self.is_watching = False
    
    async def stop_watching(self):
        """Stop watching the stream"""
        self.is_watching = False
        await self.log("Stopping stream viewer")
    
    async def close(self):
        """Close the browser"""
        if self.driver:
            await self.driver.quit()
            await self.log("Browser closed")

# Multi-viewer manager
class MultiViewerManager:
    def __init__(self):
        self.viewers = []
        
    async def create_viewers(self, count, stream_url, max_duration_minutes=None):
        """Create multiple viewers for a stream"""
        print(f"🚀 Creating {count} viewers for stream: {stream_url}")
        print(f"⏰ Viewers will start with 0-60 second delays for better distribution")
        
        tasks = []
        for i in range(1, count + 1):
            viewer = LiveStreamViewer(viewer_id=i)
            self.viewers.append(viewer)
            
            # Stagger the start times more (0-60 seconds)
            start_delay = random.uniform(0, 60)
            
            task = asyncio.create_task(
                self.start_viewer_with_delay(viewer, stream_url, start_delay, max_duration_minutes)
            )
            tasks.append(task)
        
        # Start a monitoring task
        monitor_task = asyncio.create_task(self.monitor_viewers())
        
        # Wait for all viewers to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Stop monitoring
        monitor_task.cancel()
        
        # Report results
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
        
    async def start_viewer_with_delay(self, viewer, stream_url, delay, max_duration_minutes):
        """Start a viewer with initial delay"""
        await asyncio.sleep(delay)
        
        try:
            await viewer.setup_browser()
            await viewer.watch_live_stream(stream_url, max_duration_minutes)
        except Exception as e:
            await viewer.log(f"Viewer failed: {e}")
        finally:
            await viewer.close()
    
    async def stop_all_viewers(self):
        """Stop all viewers"""
        print("Stopping all viewers...")
        for viewer in self.viewers:
            await viewer.stop_watching()

async def main():
    # Configuration
    STREAM_URL = "https://www.youtube.com/watch?v=QmgZJmzL-0U"  # Replace with your stream URL
    VIEWER_COUNT = 5  # Number of concurrent viewers (start small, then increase)
    MAX_DURATION_MINUTES = 60  # Maximum watch time per viewer (None for unlimited)
    
    manager = MultiViewerManager()
    
    try:
        await manager.create_viewers(VIEWER_COUNT, STREAM_URL, MAX_DURATION_MINUTES)
        print(f"🎉 All {VIEWER_COUNT} viewers completed!")
        
    except KeyboardInterrupt:
        print("\n⏹️ Stopping all viewers...")
        await manager.stop_all_viewers()
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
