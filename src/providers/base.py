"""
Base Provider Interface

All providers (LLM, Analysis, Export, Sponsor) must implement this interface.
This enables the plugin architecture for easy integration with sponsor tools.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional
from dataclasses import dataclass


class ProviderType(str, Enum):
    """Types of providers supported by Contextix."""
    LLM = "llm"
    ANALYSIS = "analysis"
    EXPORT = "export"
    SPONSOR = "sponsor"
    COMPUTE = "compute"
    DATA = "data"


@dataclass
class ProviderConfig:
    """Configuration for a provider."""
    name: str
    provider_type: ProviderType
    entry_point: str
    config: Dict[str, Any]
    required_env: List[str]
    version: str = "1.0.0"


@dataclass
class ProviderResult:
    """Result from provider execution."""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class Provider(ABC):
    """
    Abstract base class for all Contextix providers.
    
    Every provider (LLM, Analysis, Export, Sponsor) must implement this interface.
    This enables the plugin architecture where sponsor tools can be easily integrated
    with minimal code changes.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Provider version."""
        pass
    
    @property
    @abstractmethod
    def provider_type(self) -> ProviderType:
        """Type of provider."""
        pass
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize the provider with configuration.
        
        Args:
            config: Provider-specific configuration dictionary
        """
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate provider configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            True if configuration is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def execute(self, context: Any) -> ProviderResult:
        """
        Execute the provider's main functionality.
        
        Args:
            context: Pipeline context or relevant input data
            
        Returns:
            ProviderResult with execution outcome
        """
        pass
    
    def get_capabilities(self) -> List[str]:
        """
        Get list of capabilities this provider supports.
        
        Returns:
            List of capability names
        """
        return []
    
    def cleanup(self) -> None:
        """Cleanup resources. Called when provider is no longer needed."""
        pass


class LLMProvider(Provider):
    """Base class for LLM providers (OpenAI, Anthropic, etc.)."""
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from prompt."""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the model."""
        pass


class AnalysisProvider(Provider):
    """Base class for analysis providers."""
    
    @abstractmethod
    def analyze(self, data: Any) -> Dict[str, Any]:
        """
        Analyze input data and return structured analysis.
        
        Args:
            data: Data to analyze (repository, documents, etc.)
            
        Returns:
            Structured analysis results
        """
        pass


class ExportProvider(Provider):
    """Base class for export providers."""
    
    @abstractmethod
    def export(self, data: Any, output_path: str, **kwargs) -> str:
        """
        Export data to specified format.
        
        Args:
            data: Data to export
            output_path: Where to write the export
            
        Returns:
            Path to exported file
        """
        pass


class SponsorProvider(Provider):
    """
    Base class for sponsor providers.
    
    Sponsor providers integrate third-party tools and services from hackathon sponsors.
    This interface allows easy integration when sponsor details are announced.
    
    Example usage:
        class MySponsorIntegration(SponsorProvider):
            def initialize(self, config):
                self.api_key = config.get('api_key')
                self.client = SponsorSDK(self.api_key)
            
            def execute(self, context):
                result = self.client.analyze(context.data)
                return ProviderResult(success=True, data=result)
    """
    
    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.SPONSOR
    
    @abstractmethod
    def get_integration_points(self) -> List[str]:
        """
        Get list of pipeline stages where this provider can hook in.
        
        Returns:
            List of stage names: 'pre_parse', 'post_analyze', 'pre_export', 'post_export'
        """
        pass
    
    def pre_parse(self, context: Any) -> Optional[Any]:
        """Hook called before parsing stage."""
        return None
    
    def post_analyze(self, context: Any, analysis_result: Any) -> Optional[Any]:
        """Hook called after analysis stage."""
        return None
    
    def pre_export(self, context: Any, memory: Any) -> Optional[Any]:
        """Hook called before export stage."""
        return None
    
    def post_export(self, context: Any, export_result: Any) -> Optional[Any]:
        """Hook called after export stage."""
        return None


class ComputeProvider(Provider):
    """Base class for compute providers (GPU, TPU, cloud compute)."""
    
    @abstractmethod
    def get_compute_info(self) -> Dict[str, Any]:
        """Get information about available compute resources."""
        pass
    
    @abstractmethod
    def submit_job(self, job_config: Dict[str, Any]) -> str:
        """Submit a compute job and return job ID."""
        pass


class DataProvider(Provider):
    """Base class for data providers (databases, data lakes, etc.)."""
    
    @abstractmethod
    def connect(self) -> None:
        """Establish connection to data source."""
        pass
    
    @abstractmethod
    def query(self, query: str, **kwargs) -> Any:
        """Execute a query against the data source."""
        pass
