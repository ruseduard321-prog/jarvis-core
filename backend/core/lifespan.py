from contextlib import asynccontextmanager
import logging

from backend.core.dependencies import get_agent_service, get_database

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app):
    """Application lifespan manager."""
    # ============================================================
    # STARTUP
    # ============================================================
    try:
        logger.info("Starting backend services...")

        # Connect database
        database = get_database()
        await database.connect()
        logger.info("✓ Database connected")

        # Seed core business agents for runtime selection.
        try:
            agent_service = get_agent_service()
            seeded_agents = await agent_service.seed_core_business_agents(owner_user_id="system")
            logger.info(f"✓ Seeded {len(seeded_agents)} core business agents")
        except Exception as seed_error:
            logger.warning(f"⚠ Agent seed skipped: {seed_error}")
        logger.info("✓ Backend ready for requests")

    except Exception as e:
        logger.error(f"✗ Startup failed: {e}")
        raise

    yield

    # ============================================================
    # SHUTDOWN
    # ============================================================
    logger.info("Shutting down backend services...")
    try:
        database = get_database()
        await database.disconnect()
        logger.info("✓ Database disconnected")
    except Exception as e:
        logger.error(f"Error during database shutdown: {e}")
    logger.info("✓ Backend shutdown complete")

