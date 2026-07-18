from contextlib import asynccontextmanager
import logging

from backend.core.dependencies import get_database
from backend.core.startup_validator import validate_startup

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
        
        # Run startup validation
        logger.info("Running startup validation...")
        report = await validate_startup()
        logger.info(f"Startup validation complete: {report['summary']['status'].upper()}")
        
        # Check for critical failures
        if report["summary"]["failed"] > 0:
            logger.warning(f"Startup warnings: {report['summary']['warnings']} checks with warnings")
        
        logger.info("✓ Backend ready for requests")
        
    except Exception as e:
        logger.error(f"✗ Startup failed: {e}")
        raise
    
    try:
        yield
    finally:
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

