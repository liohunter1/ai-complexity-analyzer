"""
Token management for LLM API calls with cost tracking.
"""

from typing import Optional
import tiktoken
import logging

logger = logging.getLogger(__name__)


class TokenManager:
    """
    Manages token counting and cost estimation for LLM API calls.
    Implements Single Responsibility Principle.
    """
    
    # Token limits per model
    MODEL_LIMITS = {
        "gpt-4-turbo-preview": 128000,
        "gpt-4": 8192,
        "gpt-3.5-turbo": 16385,
        "claude-3-opus-20240229": 200000,
        "claude-3-sonnet-20240229": 200000,
    }
    
    # Cost per 1K tokens (USD)
    MODEL_COSTS = {
        "gpt-4-turbo-preview": {"input": 0.01, "output": 0.03},
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
        "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
    }
    
    def __init__(self, model: str = "gpt-4-turbo-preview"):
        """Initialize token manager for specific model."""
        self.model = model
        self.encoding = self._get_encoding(model)
        self.total_input_tokens = 0
        self.total_output_tokens = 0
    
    def _get_encoding(self, model: str) -> tiktoken.Encoding:
        """Get appropriate encoding for model."""
        if "gpt" in model:
            try:
                return tiktoken.encoding_for_model(model)
            except KeyError:
                return tiktoken.get_encoding("cl100k_base")
        else:
            # Anthropic uses similar tokenization to GPT-4
            return tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.encoding.encode(text))
    
    def truncate_to_limit(
        self,
        text: str,
        max_tokens: Optional[int] = None,
        buffer: int = 500
    ) -> str:
        """
        Truncate text to fit within token limit.
        
        Args:
            text: Input text
            max_tokens: Maximum tokens (defaults to model limit)
            buffer: Safety buffer for system prompts
            
        Returns:
            Truncated text
        """
        max_tokens = max_tokens or self.MODEL_LIMITS.get(self.model, 8000)
        max_tokens -= buffer
        
        tokens = self.encoding.encode(text)
        
        if len(tokens) <= max_tokens:
            return text
        
        truncated_tokens = tokens[:max_tokens]
        return self.encoding.decode(truncated_tokens)
    
    def estimate_cost(
        self,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """
        Estimate cost for API call.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Estimated cost in USD
        """
        costs = self.MODEL_COSTS.get(self.model)
        
        if not costs:
            logger.warning(f"No cost data for model {self.model}")
            return 0.0
        
        input_cost = (input_tokens / 1000) * costs["input"]
        output_cost = (output_tokens / 1000) * costs["output"]
        
        return input_cost + output_cost
    
    def track_usage(self, input_tokens: int, output_tokens: int):
        """Track token usage across multiple calls."""
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
    
    def get_total_cost(self) -> float:
        """Get total cost for all tracked usage."""
        return self.estimate_cost(
            self.total_input_tokens,
            self.total_output_tokens
        )
    
    def reset(self):
        """Reset usage tracking."""
        self.total_input_tokens = 0
        self.total_output_tokens = 0
