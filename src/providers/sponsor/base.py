"""
Base Sponsor Provider

Template for creating sponsor integrations.
When hackathon sponsors are announced, duplicate this file and customize.

Usage:
    1. Copy this file to src/providers/sponsor/sponsor_name.py
    2. Create plugin.yaml in the same directory
    3. Implement the abstract methods
    4. The registry will auto-discover and load the plugin
"""

from typing import Any, Dict, List, Optional
from ..base import SponsorProvider, ProviderType, ProviderResult
from loguru import logger


class BaseSponsorProvider(SponsorProvider):
    """
    Base implementation for sponsor providers.
    
    Provides common functionality and a template for sponsor integrations.
    
    Example integration flow:
    
    1. Initialize: Load API keys, SDK clients
    2. Pre-parse: Inject sponsor data sources if needed
    3. Post-analyze: Enrich analysis with sponsor-specific insights
    4. Pre-export: Format data for sponsor platform requirements
    5. Post-export: Submit results to sponsor platform
    
    To create a new sponsor integration:
    
    ```python
    class MySponsorProvider(BaseSponsorProvider):
        name = "my-sponsor"
        version = "1.0.0"
        
        def initialize(self, config: Dict[str, Any]) -> None:
            self.api_key = config.get("api_key")
            self.client = SponsorSDK(self.api_key)
        
        def execute(self, context: Any) -> ProviderResult:
            result = self.client.analyze(context.data)
            return ProviderResult(success=True, data=result)
        
        def get_integration_points(self) -> List[str]:
            return ["post_analyze", "post_export"]
    ```
    """
    
    @property
    def name(self) -> str:
        """Override this in subclass."""
        return "base-sponsor"
    
    @property
    def version(self) -> str:
        """Override this in subclass."""
        return "1.0.0"
    
    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.SPONSOR
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize the sponsor provider.
        
        Override this to:
        - Load API keys from config
        - Initialize SDK clients
        - Set up connections
        
        Args:
            config: Configuration dictionary (typically from environment variables)
        """
        logger.info(f"Initializing sponsor provider: {self.name}")
        self.config = config
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate that required configuration is present.
        
        Override this to add sponsor-specific validation.
        
        Args:
            config: Configuration to validate
            
        Returns:
            True if valid, False otherwise
        """
        return True
    
    def execute(self, context: Any) -> ProviderResult:
        """
        Execute the sponsor provider's main functionality.
        
        Override this to implement sponsor-specific logic.
        
        Args:
            context: Pipeline context or input data
            
        Returns:
            ProviderResult with execution outcome
        """
        logger.info(f"Executing sponsor provider: {self.name}")
        return ProviderResult(
            success=True,
            data=None,
            metadata={"provider": self.name, "version": self.version}
        )
    
    def get_integration_points(self) -> List[str]:
        """
        Define which pipeline stages this provider hooks into.
        
        Override this to specify integration points.
        
        Returns:
            List of stage names: 'pre_parse', 'post_analyze', 'pre_export', 'post_export'
        """
        return []
    
    def get_capabilities(self) -> List[str]:
        """
        List capabilities this sponsor provider offers.
        
        Override this to describe what the provider can do.
        
        Returns:
            List of capability descriptions
        """
        return []
    
    def cleanup(self) -> None:
        """
        Cleanup resources.
        
        Override this to close connections, release resources.
        """
        logger.info(f"Cleaning up sponsor provider: {self.name}")


# ============================================================================
# EXAMPLE SPONSOR INTEGRATION TEMPLATE
# ============================================================================
#
# When sponsors are announced, copy the template below and customize:
#
# ```python
# from .base import BaseSponsorProvider
# from ..base import ProviderResult
#
# class ExampleSponsorProvider(BaseSponsorProvider):
#     """
#     Integration with Example Sponsor's AI Platform.
#     
#     Capabilities:
#     - Enhanced code analysis using Example Sponsor's models
#     - Automatic submission to Example Sponsor's showcase platform
#     """
#     
#     @property
#     def name(self) -> str:
#         return "example-sponsor"
#     
#     @property
#     def version(self) -> str:
#         return "1.0.0"
#     
#     def initialize(self, config: Dict[str, Any]) -> None:
#         super().initialize(config)
#         # Initialize sponsor SDK
#         # self.client = ExampleSponsorSDK(api_key=self.config.get("api_key"))
#     
#     def validate_config(self, config: Dict[str, Any]) -> bool:
#         return "api_key" in config
#     
#     def execute(self, context: Any) -> ProviderResult:
#         # Use sponsor's API to analyze or enrich data
#         # result = self.client.analyze(context.data)
#         # return ProviderResult(success=True, data=result)
#         return ProviderResult(success=True, data=None)
#     
#     def get_integration_points(self) -> List[str]:
#         return ["post_analyze", "post_export"]
#     
#     def post_analyze(self, context: Any, analysis_result: Any) -> Optional[Any]:
#         # Enrich analysis with sponsor-specific insights
#         # enhanced = self.client.enhance(analysis_result)
#         # return enhanced
#         return None
#     
#     def post_export(self, context: Any, export_result: Any) -> Optional[Any]:
#         # Submit to sponsor's showcase platform
#         # self.client.submit(export_result)
#         return None
#     
#     def get_capabilities(self) -> List[str]:
#         return [
#             "Enhanced code analysis",
#             "Automatic showcase submission",
#             "Cloud compute credits"
#         ]
# ```
#
# And create plugin.yaml in the same directory:
#
# ```yaml
# name: "example-sponsor"
# type: "sponsor"
# version: "1.0.0"
# entry: "example_sponsor.py"
# config:
#   api_key:
#     required: true
#     env: "EXAMPLE_SPONSOR_API_KEY"
#     description: "API key for Example Sponsor's platform"
# ```
