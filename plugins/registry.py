"""Plugin registry - manages loading, discovery, and lifecycle of plugins."""

import importlib
import os
from pathlib import Path
from typing import Dict, List, Optional, Type
from .base import Plugin, PluginMetadata


class PluginRegistry:
    """Central registry for all AI service plugins."""

    def __init__(self):
        self._plugins: Dict[str, Plugin] = {}
        self._plugin_classes: Dict[str, Type[Plugin]] = {}
        self._load_order: List[str] = []

    def register(self, plugin_class: Type[Plugin], config: dict = None) -> Plugin:
        """Register a plugin class."""
        # Create instance to get metadata
        instance = plugin_class(config)
        meta = instance.metadata

        if meta.id in self._plugins:
            raise ValueError(f"Plugin '{meta.id}' already registered")

        self._plugins[meta.id] = instance
        self._plugin_classes[meta.id] = plugin_class
        self._load_order.append(meta.id)

        return instance

    async def initialize_all(self) -> Dict[str, bool]:
        """Initialize all registered plugins."""
        results = {}
        for plugin_id in self._load_order:
            plugin = self._plugins[plugin_id]
            try:
                ok = await plugin.initialize()
                plugin._initialized = ok
                results[plugin_id] = ok
            except Exception as e:
                results[plugin_id] = False
                print(f"  Failed to initialize {plugin_id}: {e}")
        return results

    def get(self, plugin_id: str) -> Optional[Plugin]:
        """Get a plugin by ID."""
        return self._plugins.get(plugin_id)

    def get_by_type(self, service_type: str) -> List[Plugin]:
        """Get all plugins of a given type."""
        return [
            p for p in self._plugins.values()
            if p.metadata.service_type == service_type and p.is_initialized
        ]

    def list_plugins(self) -> List[dict]:
        """List all registered plugins with their metadata."""
        return [
            {
                "id": p.metadata.id,
                "name": p.metadata.name,
                "version": p.metadata.version,
                "author": p.metadata.author,
                "description": p.metadata.description,
                "service_type": p.metadata.service_type,
                "capabilities": p.metadata.capabilities,
                "initialized": p.is_initialized,
            }
            for p in self._plugins.values()
        ]

    def list_by_type(self) -> Dict[str, List[dict]]:
        """List plugins grouped by type."""
        result = {}
        for p in self._plugins.values():
            t = p.metadata.service_type
            if t not in result:
                result[t] = []
            result[t].append({
                "id": p.metadata.id,
                "name": p.metadata.name,
                "version": p.metadata.version,
            })
        return result

    async def cleanup_all(self):
        """Cleanup all plugins."""
        for plugin_id in reversed(self._load_order):
            plugin = self._plugins[plugin_id]
            try:
                await plugin.cleanup()
            except Exception:
                pass

    def unload(self, plugin_id: str):
        """Unload a plugin."""
        if plugin_id in self._plugins:
            del self._plugins[plugin_id]
            del self._plugin_classes[plugin_id]
            self._load_order.remove(plugin_id)

    def load_from_directory(self, directory: str):
        """Auto-discover and load plugins from a directory."""
        plugin_dir = Path(directory)
        if not plugin_dir.exists():
            return

        for py_file in plugin_dir.glob("*.py"):
            if py_file.name.startswith("_"):
                continue
            try:
                # Dynamic import
                module_name = f"plugins.custom.{py_file.stem}"
                spec = importlib.util.spec_from_file_location(module_name, py_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Find Plugin subclasses
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and
                        issubclass(attr, Plugin) and
                        attr is not Plugin):
                        self.register(attr)
            except Exception as e:
                print(f"Failed to load plugin {py_file.name}: {e}")


# Global registry instance
plugin_registry = PluginRegistry()
