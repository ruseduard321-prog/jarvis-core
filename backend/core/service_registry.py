from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import Any, Callable, Type, TypeVar

T = TypeVar("T")


class ServiceNotRegisteredError(RuntimeError):
    """Raised when a requested service has not been registered."""


@dataclass
class _ServiceRegistration:
    factory: Callable[[], Any]
    instance: Any | None = None


class ServiceRegistry:
    """Central registry for lazy singleton services."""

    def __init__(self) -> None:
        self._registrations: dict[Type[Any], _ServiceRegistration] = {}
        self._lock = Lock()

    def register_singleton(self, service_type: Type[T], factory: Callable[[], T]) -> None:
        """Register a lazily created singleton service."""
        self._registrations[service_type] = _ServiceRegistration(factory=factory)

    def register_instance(self, service_type: Type[T], instance: T) -> None:
        """Register an existing singleton instance."""
        self._registrations[service_type] = _ServiceRegistration(factory=lambda: instance, instance=instance)

    def override_singleton(self, service_type: Type[T], factory: Callable[[], T]) -> None:
        """Replace the service factory for a registered service."""
        self.register_singleton(service_type, factory)

    def get(self, service_type: Type[T]) -> T:
        """Resolve a service instance from the registry."""
        registration = self._registrations.get(service_type)
        if registration is None:
            raise ServiceNotRegisteredError(f"Service not registered: {service_type.__name__}")

        if registration.instance is None:
            with self._lock:
                if registration.instance is None:
                    registration.instance = registration.factory()
        return registration.instance  # type: ignore[return-value]


service_registry = ServiceRegistry()
