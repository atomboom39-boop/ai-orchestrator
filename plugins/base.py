"""Base plugin class for AI services."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class PluginMetadata:
    """Metadata for a plugin."""
    id: str
    name: str
    version: str
    author: str
    description: str
    service_type: str  # text, image, video, 3d, audio
    capabilities: list = field(default_factory=list)
    config_schema: dict = field(default_factory=dict)  # JSON schema for config
    dependencies: list = field(default_factory=list)  # Other plugin IDs


class Plugin(ABC):
    """Base class that all plugins must extend."""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self._initialized = False

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        pass

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the plugin. Return True if successful."""
        pass

    @abstractmethod
    async def generate(self, **kwargs) -> Dict[str, Any]:
        """Generate output from this plugin."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the plugin is healthy."""
        pass

    async def cleanup(self):
        """Cleanup resources when plugin is unloaded."""
        pass

    def validate_config(self, schema: dict = None) -> bool:
        """Validate plugin config against schema."""
        schema = schema or self.metadata.config_schema
        if not schema:
            return True
        # Basic validation - check required fields exist
        required = schema.get("required", [])
        for field in required:
            if field not in self.config:
                return False
        return True

    @property
    def is_initialized(self) -> bool:
        return self._initialized
