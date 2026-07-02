"""
Provider Registry

Handles discovery, registration, and management of providers.
Supports auto-discovery of sponsor plugins from plugin.yaml manifests.
"""

import os
import importlib
import importlib.util
from pathlib import Path
from typing import Any, Dict, List, Optional, Type
import yaml
from loguru import logger

from .base import Provider, ProviderType, ProviderConfig


class ProviderRegistry:
    """
    Central registry for all Contextix providers.
    
    Features:
    - Manual provider registration
    - Auto-discovery from plugin directories
    - Provider lookup by name/type
    - Configuration validation
    - Lifecycle management
    """
    
    def __init__(self):
        self._providers: Dict[str, Provider] = {}
        self._configs: Dict[str, ProviderConfig] = {}
        self._hooks: Dict[str, List[str]] = {
            "pre_parse": [],
            "post_analyze": [],
            "pre_export": [],
            "post_export": [],
        }
    
    def register(self, provider: Provider, config: Optional[ProviderConfig] = None) -> None:
        """
        Register a provider with the registry.
        
        Args:
            provider: Provider instance to register
            config: Optional configuration for the provider
        """
        name = provider.name
        
        if name in self._providers:
            logger.warning(f"Provider '{name}' already registered. Overwriting.")
        
        self._providers[name] = provider
        
        if config:
            self._configs[name] = config
            if provider.validate_config(config.config):
                provider.initialize(config.config)
            else:
                logger.error(f"Invalid configuration for provider '{name}'")
                raise ValueError(f"Invalid configuration for provider '{name}'")
        
        logger.info(f"Registered provider: {name} ({provider.provider_type.value})")
    
    def unregister(self, name: str) -> None:
        """
        Unregister a provider.
        
        Args:
            name: Name of the provider to unregister
        """
        if name in self._providers:
            provider = self._providers[name]
            provider.cleanup()
            del self._providers[name]
            
            if name in self._configs:
                del self._configs[name]
            
            # Remove from hooks
            for hook_list in self._hooks.values():
                if name in hook_list:
                    hook_list.remove(name)
            
            logger.info(f"Unregistered provider: {name}")
    
    def get(self, name: str) -> Optional[Provider]:
        """
        Get a provider by name.
        
        Args:
            name: Provider name
            
        Returns:
            Provider instance or None if not found
        """
        return self._providers.get(name)
    
    def get_by_type(self, provider_type: ProviderType) -> List[Provider]:
        """
        Get all providers of a specific type.
        
        Args:
            provider_type: Type of providers to retrieve
            
        Returns:
            List of providers matching the type
        """
        return [
            p for p in self._providers.values()
            if p.provider_type == provider_type
        ]
    
    def list_all(self) -> Dict[str, Provider]:
        """
        List all registered providers.
        
        Returns:
            Dictionary of provider name -> Provider instance
        """
        return self._providers.copy()
    
    def discover(self, directory: str) -> None:
        """
        Auto-discover and load providers from a directory.
        
        Scans for plugin.yaml files and loads corresponding Python modules.
        
        Args:
            directory: Directory to scan for plugins
        """
        plugin_dir = Path(directory)
        
        if not plugin_dir.exists():
            logger.warning(f"Plugin directory does not exist: {directory}")
            return
        
        # Find all plugin.yaml files
        for manifest_path in plugin_dir.rglob("plugin.yaml"):
            try:
                self._load_plugin_from_manifest(manifest_path)
            except Exception as e:
                logger.error(f"Failed to load plugin from {manifest_path}: {e}")
    
    def _load_plugin_from_manifest(self, manifest_path: Path) -> None:
        """
        Load a plugin from its manifest file.
        
        Args:
            manifest_path: Path to plugin.yaml
        """
        with open(manifest_path, "r") as f:
            manifest = yaml.safe_load(f)
        
        name = manifest.get("name")
        entry = manifest.get("entry")
        provider_type = manifest.get("type", "sponsor")
        config_schema = manifest.get("config", {})
        
        if not name or not entry:
            logger.warning(f"Invalid manifest at {manifest_path}: missing name or entry")
            return
        
        # Resolve entry point path
        base_dir = manifest_path.parent
        entry_path = base_dir / entry
        
        if not entry_path.exists():
            logger.error(f"Entry point not found: {entry_path}")
            return
        
        # Load the module dynamically
        spec = importlib.util.spec_from_file_location(name, entry_path)
        if spec is None or spec.loader is None:
            logger.error(f"Failed to load module spec for {name}")
            return
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Find the provider class in the module
        provider_class = None
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and 
                issubclass(attr, Provider) and 
                attr is not Provider):
                provider_class = attr
                break
        
        if provider_class is None:
            logger.error(f"No Provider class found in {entry_path}")
            return
        
        # Instantiate and register
        provider = provider_class()
        
        # Build config from environment variables
        config = {}
        for key, schema in config_schema.items():
            env_var = schema.get("env")
            if env_var:
                value = os.environ.get(env_var)
                if value:
                    config[key] = value
                elif schema.get("required", False):
                    logger.error(f"Required environment variable {env_var} not set for {name}")
                    return
        
        provider_config = ProviderConfig(
            name=name,
            provider_type=ProviderType(provider_type),
            entry_point=str(entry_path),
            config=config,
            required_env=[s.get("env") for s in config_schema.values() if s.get("env")],
            version=manifest.get("version", "1.0.0"),
        )
        
        self.register(provider, provider_config)
        
        # Register hooks if sponsor provider
        if provider_type == "sponsor" and hasattr(provider, "get_integration_points"):
            hooks = provider.get_integration_points()
            for hook in hooks:
                if hook in self._hooks:
                    self._hooks[hook].append(name)
    
    def get_hooks(self, stage: str) -> List[Provider]:
        """
        Get providers registered for a specific pipeline hook.
        
        Args:
            stage: Hook stage (pre_parse, post_analyze, pre_export, post_export)
            
        Returns:
            List of providers registered for this hook
        """
        if stage not in self._hooks:
            return []
        
        return [
            self._providers[name]
            for name in self._hooks[stage]
            if name in self._providers
        ]
    
    def execute_hooks(self, stage: str, context: Any) -> List[Any]:
        """
        Execute all providers registered for a specific hook.
        
        Args:
            stage: Hook stage
            context: Context to pass to providers
            
        Returns:
            List of results from each provider
        """
        results = []
        providers = self.get_hooks(stage)
        
        for provider in providers:
            try:
                hook_method = getattr(provider, stage, None)
                if hook_method:
                    result = hook_method(context)
                    results.append(result)
            except Exception as e:
                logger.error(f"Hook {stage} failed for provider {provider.name}: {e}")
        
        return results
    
    def validate_all(self) -> Dict[str, bool]:
        """
        Validate configuration for all registered providers.
        
        Returns:
            Dictionary of provider name -> validation result
        """
        results = {}
        
        for name, provider in self._providers.items():
            if name in self._configs:
                results[name] = provider.validate_config(self._configs[name].config)
            else:
                results[name] = True
        
        return results
    
    def cleanup_all(self) -> None:
        """Cleanup all registered providers."""
        for provider in self._providers.values():
            try:
                provider.cleanup()
            except Exception as e:
                logger.error(f"Cleanup failed for provider {provider.name}: {e}")
        
        self._providers.clear()
        self._configs.clear()
        for hook_list in self._hooks.values():
            hook_list.clear()


# Global registry instance
_global_registry: Optional[ProviderRegistry] = None


def get_registry() -> ProviderRegistry:
    """Get the global provider registry instance."""
    global _global_registry
    if _global_registry is None:
        _global_registry = ProviderRegistry()
    return _global_registry
