"""LLM integration with deterministic offline fallback."""
import os
from typing import Optional, List, Dict, Any


class LLMClient:
    """Hybrid LLM helper for semantic refinement with zero-dependency offline fallback."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.is_enabled = bool(self.api_key)

    def refine_codification(self, ambiguity_text: str, context: str) -> Optional[str]:
        """Optionally enhances rule codification if LLM API key is present."""
        if not self.is_enabled:
            return None

        # When API key is available, can query LiteLLM / Gemini
        try:
            import litellm
            response = litellm.completion(
                model="gemini/gemini-1.5-flash" if "GEMINI_API_KEY" in os.environ else "gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a compiler engineer converting financial compliance SOPs into deterministic boolean expressions."
                    },
                    {
                        "role": "user",
                        "content": f"Convert this ambiguous SOP phrase into a strict python/boolean expression: '{ambiguity_text}'. Context: '{context}'"
                    }
                ],
                temperature=0.0,
                max_tokens=60
            )
            return response.choices[0].message.content.strip()
        except Exception:
            # Fallback gracefully to heuristic mode without throwing
            return None
