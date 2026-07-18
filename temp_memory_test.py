from backend.core.dependencies import get_memory_service
service = get_memory_service()
print(type(service))
print(service.__class__.__name__)