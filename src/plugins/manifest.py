"""
Plugin Manifest Schema

Defines the structure and validation for plugin.yaml files.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path
import yaml


@dataclass
class PluginManifest:
    """
    Schema for plugin.yaml manifest files.
    
    Example:
        name: "sponsor-x"
        type: "sponsor"
        version: "1.0.0"
        entry: "sponsor_x.py"
        description: "Integration with Sponsor X's AI platform"
        author: "Your Name"
        config:
          api_key:
            required: true
            env: "SPONSOR_X_API_KEY"
            description: "API key for Sponsor X"
          endpoint:
            required: false
            env: "SPONSOR_X_ENDPOINT"
            default: "https://api.sponsor-x.com"
    """
    
    name: str
    type: str  # "llm", "analysis", "export", "sponsor", "compute", "data"
    version: str = "1.0.0"
    entry: str = ""
    description: str = ""
    author: str = ""
    config: Optional[Dict[str, Dict[str, Any]]] = None
    
    def __post_init__(self):
        if self.config is None:
            self.config = {}
    
    @classmethod
    def from_file(cls, path: Path) -> "PluginManifest":
        """
        Load manifest from a YAML file.
        
        Args:
            path: Path to plugin.yaml
            
        Returns:
            PluginManifest instance
        """
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        
        return cls(
            name=data.get("name", ""),
            type=data.get("type", "sponsor"),
            version=data.get("version", "1.0.0"),
            entry=data.get("entry", ""),
            description=data.get("description", ""),
            author=data.get("author", ""),
            config=data.get("config", {}),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert manifest to dictionary."""
        return {
            "name": self.name,
            "type": self.type,
            "version": self.version,
            "entry": self.entry,
            "description": self.description,
            "author": self.author,
            "config": self.config,
        }
    
    def save(self, path: Path) -> None:
        """
        Save manifest to a YAML file.
        
        Args:
            path: Path to save plugin.yaml
        """
        with open(path, "w") as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, sort_keys=False)


def validate_manifest(manifest: PluginManifest) -> Dict[str, Any]:
    """
    Validate a plugin manifest.
    
    Args:
        manifest: Manifest to validate
        
    Returns:
        Dictionary with 'valid' boolean and 'errors' list
    """
    errors = []
    
    # Required fields
    if not manifest.name:
        errors.append("Missing required field: name")
    
    if not manifest.type:
        errors.append("Missing required field: type")
    
    # Validate type
    valid_types = ["llm", "analysis", "export", "sponsor", "compute", "data"]
    if manifest.type and manifest.type not in valid_types:
        errors.append(f"Invalid type '{manifest.type}'. Must be one of: {', '.join(valid_types)}")
    
    # Validate entry point if specified
    if manifest.entry:
        if not manifest.entry.endswith(".py"):
            errors.append(f"Entry point must be a Python file (.py): {manifest.entry}")
    
    # Validate config schema
    if manifest.config:
        for key, schema in manifest.config.items():
            if not isinstance(schema, dict):
                errors.append(f"Config '{key}' must be a dictionary")
                continue
            
            # Check for required fields in schema
            if "required" in schema and not isinstance(schema["required"], bool):
                errors.append(f"Config '{key}.required' must be a boolean")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }


def create_manifest_template(
    name: str,
    plugin_type: str = "sponsor",
    description: str = "",
    author: str = "",
    config_keys: Optional[List[str]] = None,
) -> PluginManifest:
    """
    Create a manifest template for a new plugin.
    
    Args:
        name: Plugin name
        plugin_type: Type of plugin
        description: Plugin description
        author: Author name
        config_keys: List of configuration keys to include
        
    Returns:
        PluginManifest with template values
    """
    config = {}
    
    if config_keys:
        for key in config_keys:
            config[key] = {
                "required": True,
                "env": f"{name.upper()}_{key.upper()}",
                "description": f"{key} for {name}",
            }
    
    return PluginManifest(
        name=name,
        type=plugin_type,
        version="1.0.0",
        entry=f"{name}.py",
        description=description,
        author=author,
        config=config,
    )
