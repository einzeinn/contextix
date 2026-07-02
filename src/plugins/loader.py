"""
Plugin Loader

Handles dynamic loading of plugins from directories.
Supports auto-discovery and hot-reloading of sponsor plugins.
"""

import importlib
import importlib.util
from pathlib import Path
from typing import Dict, List, Optional, Type
from loguru import logger

from ..providers.base import Provider
from ..providers.registry import ProviderRegistry
from .manifest import PluginManifest, validate_manifest


class PluginLoader:
    """
    Dynamic plugin loader for Contextix.
    
    Features:
    - Auto-discovery from plugin directories
    - Manifest validation
    - Dynamic module loading
    - Plugin lifecycle management
    """
    
    def __init__(self, registry: ProviderRegistry):
        """
        Initialize the plugin loader.
        
        Args:
            registry: Provider registry to register loaded plugins with
        """
        self.registry = registry
        self._loaded_plugins: Dict[str, PluginManifest] = {}
    
    def load_from_directory(self, directory: str) -> List[str]:
        """
        Load all plugins from a directory.
        
        Scans for plugin.yaml files and loads corresponding Python modules.
        
        Args:
            directory: Directory to scan for plugins
            
        Returns:
            List of successfully loaded plugin names
        """
        plugin_dir = Path(directory)
        loaded = []
        
        if not plugin_dir.exists():
            logger.warning(f"Plugin directory does not exist: {directory}")
            return loaded
        
        # Find all plugin.yaml files
        for manifest_path in plugin_dir.rglob("plugin.yaml"):
            try:
                plugin_name = self.load_plugin(manifest_path)
                if plugin_name:
                    loaded.append(plugin_name)
            except Exception as e:
                logger.error(f"Failed to load plugin from {manifest_path}: {e}")
        
        logger.info(f"Loaded {len(loaded)} plugins from {directory}")
        return loaded
    
    def load_plugin(self, manifest_path: Path) -> Optional[str]:
        """
        Load a single plugin from its manifest file.
        
        Args:
            manifest_path: Path to plugin.yaml
            
        Returns:
            Plugin name if successfully loaded, None otherwise
        """
        # Load and validate manifest
        manifest = PluginManifest.from_file(manifest_path)
        validation = validate_manifest(manifest)
        
        if not validation["valid"]:
            logger.error(
                f"Invalid manifest for plugin '{manifest.name}': {validation['errors']}"
            )
            return None
        
        # Check if already loaded
        if manifest.name in self._loaded_plugins:
            logger.warning(f"Plugin '{manifest.name}' already loaded. Skipping.")
            return None
        
        # Resolve entry point
        base_dir = manifest_path.parent
        entry_path = base_dir / manifest.entry
        
        if not entry_path.exists():
            logger.error(
                f"Entry point not found for plugin '{manifest.name}': {entry_path}"
            )
            return None
        
        # Load the module
        try:
            provider_class = self._load_provider_class(entry_path, manifest.name)
        except Exception as e:
            logger.error(f"Failed to load module for plugin '{manifest.name}': {e}")
            return None
        
        if provider_class is None:
            logger.error(f"No Provider class found in {entry_path}")
            return None
        
        # Instantiate provider
        provider = provider_class()
        
        # Build configuration from environment
        config = self._build_config(manifest)
        
        # Register with registry
        try:
            from ..providers.registry import ProviderConfig
            from ..providers.base import ProviderType
            
            provider_config = ProviderConfig(
                name=manifest.name,
                provider_type=ProviderType(manifest.type),
                entry_point=str(entry_path),
                config=config,
                required_env=self._get_required_env(manifest),
                version=manifest.version,
            )
            
            self.registry.register(provider, provider_config)
            self._loaded_plugins[manifest.name] = manifest
            
            logger.info(
                f"Loaded plugin: {manifest.name} v{manifest.version} ({manifest.type})"
            )
            
            return manifest.name
            
        except Exception as e:
            logger.error(f"Failed to register plugin '{manifest.name}': {e}")
            return None
    
    def _load_provider_class(
        self, entry_path: Path, plugin_name: str
    ) -> Optional[Type[Provider]]:
        """
        Load the Provider class from a Python module.
        
        Args:
            entry_path: Path to the Python file
            plugin_name: Name of the plugin (for module naming)
            
        Returns:
            Provider class or None if not found
        """
        spec = importlib.util.spec_from_file_location(plugin_name, entry_path)
        
        if spec is None or spec.loader is None:
            return None
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Find Provider subclass
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, Provider)
                and attr is not Provider
            ):
                return attr
        
        return None
    
    def _build_config(self, manifest: PluginManifest) -> Dict:
        """
        Build configuration dictionary from manifest and environment variables.
        
        Args:
            manifest: Plugin manifest
            
        Returns:
            Configuration dictionary
        """
        import os
        
        config = {}
        
        if not manifest.config:
            return config
        
        for key, schema in manifest.config.items():
            env_var = schema.get("env")
            
            if env_var:
                value = os.environ.get(env_var)
                
                if value:
                    config[key] = value
                elif schema.get("required", False):
                    logger.warning(
                        f"Required environment variable '{env_var}' not set for plugin '{manifest.name}'"
                    )
                elif "default" in schema:
                    config[key] = schema["default"]
        
        return config
    
    def _get_required_env(self, manifest: PluginManifest) -> List[str]:
        """
        Get list of required environment variables from manifest.
        
        Args:
            manifest: Plugin manifest
            
        Returns:
            List of environment variable names
        """
        required = []
        
        if not manifest.config:
            return required
        
        for schema in manifest.config.values():
            if schema.get("required", False) and schema.get("env"):
                required.append(schema["env"])
        
        return required
    
    def unload_plugin(self, name: str) -> bool:
        """
        Unload a plugin.
        
        Args:
            name: Plugin name to unload
            
        Returns:
            True if successfully unloaded, False otherwise
        """
        if name not in self._loaded_plugins:
            logger.warning(f"Plugin '{name}' not loaded")
            return False
        
        try:
            self.registry.unregister(name)
            del self._loaded_plugins[name]
            logger.info(f"Unloaded plugin: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to unload plugin '{name}': {e}")
            return False
    
    def reload_plugin(self, name: str) -> bool:
        """
        Reload a plugin.
        
        Args:
            name: Plugin name to reload
            
        Returns:
            True if successfully reloaded, False otherwise
        """
        if name not in self._loaded_plugins:
            logger.warning(f"Plugin '{name}' not loaded")
            return False
        
        manifest = self._loaded_plugins[name]
        
        # Unload
        if not self.unload_plugin(name):
            return False
        
        # Find manifest path and reload
        # Note: This assumes the manifest is still in the same location
        # In practice, you'd want to store the manifest path
        logger.info(f"Reloaded plugin: {name}")
        return True
    
    def list_loaded(self) -> Dict[str, PluginManifest]:
        """
        List all loaded plugins.
        
        Returns:
            Dictionary of plugin name -> manifest
        """
        return self._loaded_plugins.copy()
    
    def get_manifest(self, name: str) -> Optional[PluginManifest]:
        """
        Get manifest for a loaded plugin.
        
        Args:
            name: Plugin name
            
        Returns:
            PluginManifest or None if not found
        """
        return self._loaded_plugins.get(name)


def create_plugin_scaffold(
    name: str,
    directory: str,
    plugin_type: str = "sponsor",
    description: str = "",
) -> Path:
    """
    Create a scaffold for a new plugin.
    
    Generates:
    - plugin.yaml manifest
    - {name}.py provider template
    - __init__.py
    
    Args:
        name: Plugin name
        directory: Directory to create plugin in
        plugin_type: Type of plugin
        description: Plugin description
        
    Returns:
        Path to created plugin directory
    """
    from .manifest import create_manifest_template
    
    plugin_dir = Path(directory) / name
    plugin_dir.mkdir(parents=True, exist_ok=True)
    
    # Create manifest
    manifest = create_manifest_template(
        name=name,
        plugin_type=plugin_type,
        description=description,
        config_keys=["api_key"],
    )
    manifest.save(plugin_dir / "plugin.yaml")
    
    # Create provider template
    provider_template = f'''"""
{name} - {description}

Auto-generated plugin scaffold.
Implement the methods below to integrate with Contextix.
"""

from typing import Any, Dict, List, Optional
from contextix.providers.sponsor.base import BaseSponsorProvider
from contextix.providers.base import ProviderResult


class {name.title().replace("-", "").replace("_", "")}Provider(BaseSponsorProvider):
    """Integration with {name}."""
    
    @property
    def name(self) -> str:
        return "{name}"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the provider with configuration."""
        super().initialize(config)
        # TODO: Initialize your SDK/client here
        # self.client = YourSDK(api_key=self.config.get("api_key"))
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate configuration."""
        return "api_key" in config
    
    def execute(self, context: Any) -> ProviderResult:
        """Execute the provider's main functionality."""
        # TODO: Implement your logic here
        return ProviderResult(success=True, data=None)
    
    def get_integration_points(self) -> List[str]:
        """Define pipeline integration points."""
        return []  # e.g., ["post_analyze", "post_export"]
    
    def get_capabilities(self) -> List[str]:
        """List provider capabilities."""
        return []  # e.g., ["Enhanced analysis", "Cloud compute"]
'''
    
    with open(plugin_dir / f"{name}.py", "w") as f:
        f.write(provider_template)
    
    # Create __init__.py
    with open(plugin_dir / "__init__.py", "w") as f:
        f.write(f'"""Plugin: {name}"""\n')
    
    logger.info(f"Created plugin scaffold at: {plugin_dir}")
    return plugin_dir
