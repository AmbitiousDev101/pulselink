import asyncio
import logging

from kafka_consumer import run_consumer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    """Entry point for the worker service."""
    logger.info("Starting PulseLink Worker Service")

    while True:
        try:
            await run_consumer()
        except Exception as e:
            logger.error(f"Consumer crashed: {e}. Restarting in 5s...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
