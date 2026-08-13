#!/usr/bin/env python3
import asyncio
import os
import sys
import signal
import logging
from datetime import datetime
from live_stream_viewer import MultiViewerManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('viewer_bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class PersistentViewerBot:
    def __init__(self):
        self.is_running = False
        self.restart_count = 0

        # Read from environment variables (Railway)
        self.STREAM_URL = os.getenv('STREAM_URL')
        if not self.STREAM_URL:
            logging.error("❌ STREAM_URL environment variable not set!")
            sys.exit(1)

        self.VIEWER_COUNT = int(os.getenv('VIEWER_COUNT', '3'))
        self.MAX_DURATION_MINUTES = int(os.getenv('MAX_DURATION_MINUTES', '0') or 0)
        self.RESTART_INTERVAL_HOURS = int(os.getenv('RESTART_INTERVAL_HOURS', '6'))

        # If MAX_DURATION is 0 or None, treat as unlimited (None)
        self.max_duration = self.MAX_DURATION_MINUTES if self.MAX_DURATION_MINUTES > 0 else None

        logging.info("🤖 YouTube Live Viewer Bot configured:")
        logging.info(f"  Stream URL: {self.STREAM_URL}")
        logging.info(f"  Viewer Count: {self.VIEWER_COUNT}")
        logging.info(f"  Max Duration: {self.max_duration if self.max_duration else 'Unlimited'} minutes")
        logging.info(f"  Restart Interval: {self.RESTART_INTERVAL_HOURS} hours")

    async def run_session(self):
        """Run one session of live viewers"""
        self.restart_count += 1
        logging.info(f"🚀 Starting session #{self.restart_count}")

        manager = MultiViewerManager()
        # Calculate session duration in minutes (restart interval)
        session_minutes = self.RESTART_INTERVAL_HOURS * 60
        # If max_duration is set and smaller, use that
        if self.max_duration and self.max_duration < session_minutes:
            session_minutes = self.max_duration

        await manager.create_viewers(
            count=self.VIEWER_COUNT,
            stream_url=self.STREAM_URL,
            max_duration_minutes=session_minutes if session_minutes > 0 else None
        )

        logging.info(f"✅ Session #{self.restart_count} completed")

    async def start(self):
        """Main loop with automatic restarts"""
        self.is_running = True
        logging.info("🌟 Bot started. Will run continuously with restarts.")

        while self.is_running:
            try:
                await self.run_session()
                if self.is_running:
                    logging.info(f"⏳ Waiting 60 seconds before next session...")
                    await asyncio.sleep(60)  # pause between sessions
            except Exception as e:
                logging.error(f"❌ Session crashed: {e}")
                if self.is_running:
                    logging.info("⏳ Waiting 5 minutes before retry...")
                    await asyncio.sleep(300)  # wait 5 min on error

        logging.info("🛑 Bot stopped.")

    async def stop(self):
        """Graceful shutdown"""
        self.is_running = False
        logging.info("⏹️ Shutting down...")

# Global bot instance for signal handling
bot = None

def signal_handler(signum, frame):
    if bot:
        logging.info(f"📡 Received signal {signum}, shutting down...")
        asyncio.create_task(bot.stop())

async def main():
    global bot
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    bot = PersistentViewerBot()
    await bot.start()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
