from __future__ import annotations

import logging
from typing import Callable, Coroutine
from dataclasses import dataclass
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class StartupCheck:
    """Result of a startup check."""
    
    name: str
    status: str  # "passed", "warning", "failed"
    message: str
    timestamp: datetime


class StartupValidator:
    """Validates backend startup and dependencies."""
    
    def __init__(self):
        """Initialize startup validator."""
        self.checks: list[StartupCheck] = []
        self.critical_failures: list[str] = []
    
    async def validate_all(self) -> bool:
        """Run all startup validations."""
        try:
            await self._validate_config()
            await self._validate_providers()
            await self._validate_services()
            await self._validate_storage()
            
            return len(self.critical_failures) == 0
        except Exception as e:
            logger.error(f"Startup validation failed: {e}")
            return False
    
    async def _validate_config(self) -> None:
        """Validate configuration."""
        try:
            from backend.core.config import settings
            from backend.core.config_validation import validate_settings
            
            # Validate settings
            validate_settings()
            
            self.checks.append(StartupCheck(
                name="Configuration",
                status="passed",
                message="Configuration loaded and validated",
                timestamp=datetime.utcnow(),
            ))
            logger.info("✓ Configuration validated")
            
        except Exception as e:
            self.checks.append(StartupCheck(
                name="Configuration",
                status="failed",
                message=f"Configuration validation failed: {e}",
                timestamp=datetime.utcnow(),
            ))
            self.critical_failures.append("Configuration")
            logger.error(f"✗ Configuration validation failed: {e}")
    
    async def _validate_providers(self) -> None:
        """Validate external providers (LLM, Embedding, Database)."""
        from backend.core.dependencies import (
            get_llm_provider,
            get_embedding_provider,
            get_database,
        )
        
        # Validate LLM Provider
        try:
            llm_provider = get_llm_provider()
            await llm_provider.health()
            
            self.checks.append(StartupCheck(
                name=f"LLM Provider ({llm_provider.name})",
                status="passed",
                message=f"LLM provider {llm_provider.name} is healthy",
                timestamp=datetime.utcnow(),
            ))
            logger.info(f"✓ LLM Provider ({llm_provider.name}) validated")
        except Exception as e:
            self.checks.append(StartupCheck(
                name="LLM Provider",
                status="warning",
                message=f"LLM provider health check failed: {e}",
                timestamp=datetime.utcnow(),
            ))
            logger.warning(f"⚠ LLM Provider validation warning: {e}")
        
        # Validate Embedding Provider
        try:
            embedding_provider = get_embedding_provider()
            await embedding_provider.health()
            
            self.checks.append(StartupCheck(
                name=f"Embedding Provider ({embedding_provider.__class__.__name__})",
                status="passed",
                message="Embedding provider is healthy",
                timestamp=datetime.utcnow(),
            ))
            logger.info("✓ Embedding Provider validated")
        except Exception as e:
            self.checks.append(StartupCheck(
                name="Embedding Provider",
                status="warning",
                message=f"Embedding provider health check failed: {e}",
                timestamp=datetime.utcnow(),
            ))
            logger.warning(f"⚠ Embedding Provider validation warning: {e}")
        
        # Validate Database Provider
        try:
            database = get_database()
            await database.health_check()
            
            self.checks.append(StartupCheck(
                name="Database Provider",
                status="passed",
                message="Database provider is healthy",
                timestamp=datetime.utcnow(),
            ))
            logger.info("✓ Database Provider validated")
        except Exception as e:
            self.checks.append(StartupCheck(
                name="Database Provider",
                status="warning",
                message=f"Database provider health check failed: {e}",
                timestamp=datetime.utcnow(),
            ))
            logger.warning(f"⚠ Database Provider validation warning: {e}")
    
    async def _validate_services(self) -> None:
        """Validate core services."""
        from backend.core.dependencies import (
            get_event_bus_service,
            get_memory_service,
            get_vector_service,
            get_embedding_provider_registry,
            get_llm_provider_registry,
            get_tool_registry,
            get_agent_registry,
        )
        
        services_to_check = [
            ("Event Bus Service", get_event_bus_service),
            ("Memory Service", get_memory_service),
            ("Vector Service", get_vector_service),
            ("Tool Registry", get_tool_registry),
            ("Agent Registry", get_agent_registry),
        ]
        
        for service_name, getter in services_to_check:
            try:
                service = getter()
                
                self.checks.append(StartupCheck(
                    name=service_name,
                    status="passed",
                    message=f"{service_name} initialized",
                    timestamp=datetime.utcnow(),
                ))
                logger.info(f"✓ {service_name} validated")
            except Exception as e:
                self.checks.append(StartupCheck(
                    name=service_name,
                    status="warning",
                    message=f"{service_name} initialization warning: {e}",
                    timestamp=datetime.utcnow(),
                ))
                logger.warning(f"⚠ {service_name} validation warning: {e}")
    
    async def _validate_storage(self) -> None:
        """Validate storage backends."""
        from backend.core.dependencies import (
            get_memory_store,
            get_vector_store,
            get_knowledge_repository,
            get_conversation_store,
        )
        
        stores_to_check = [
            ("Memory Store", get_memory_store),
            ("Vector Store", get_vector_store),
            ("Knowledge Repository", get_knowledge_repository),
            ("Conversation Store", get_conversation_store),
        ]
        
        for store_name, getter in stores_to_check:
            try:
                store = getter()
                
                self.checks.append(StartupCheck(
                    name=store_name,
                    status="passed",
                    message=f"{store_name} available",
                    timestamp=datetime.utcnow(),
                ))
                logger.info(f"✓ {store_name} validated")
            except Exception as e:
                self.checks.append(StartupCheck(
                    name=store_name,
                    status="warning",
                    message=f"{store_name} validation warning: {e}",
                    timestamp=datetime.utcnow(),
                ))
                logger.warning(f"⚠ {store_name} validation warning: {e}")
    
    def get_report(self) -> dict:
        """Get startup validation report."""
        total = len(self.checks)
        passed = sum(1 for c in self.checks if c.status == "passed")
        warnings = sum(1 for c in self.checks if c.status == "warning")
        failed = sum(1 for c in self.checks if c.status == "failed")
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "total": total,
                "passed": passed,
                "warnings": warnings,
                "failed": failed,
                "status": "ready" if len(self.critical_failures) == 0 else "not_ready",
            },
            "checks": [
                {
                    "name": c.name,
                    "status": c.status,
                    "message": c.message,
                    "timestamp": c.timestamp.isoformat(),
                }
                for c in self.checks
            ],
            "critical_failures": self.critical_failures,
        }


# Global startup validator instance
_startup_validator: StartupValidator | None = None


def get_startup_validator() -> StartupValidator:
    """Get the global startup validator instance."""
    global _startup_validator
    if _startup_validator is None:
        _startup_validator = StartupValidator()
    return _startup_validator


async def validate_startup() -> dict:
    """Run all startup validations."""
    validator = get_startup_validator()
    ready = await validator.validate_all()
    
    report = validator.get_report()
    if ready:
        logger.info("✓ Backend startup validation: ALL CHECKS PASSED")
    else:
        logger.error("✗ Backend startup validation: CRITICAL FAILURES")
        for failure in report["critical_failures"]:
            logger.error(f"  - {failure}")
    
    return report
