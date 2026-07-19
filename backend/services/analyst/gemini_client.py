"""
NetElixIQ AI — Gemini API Client
Adapted from consultantOS/consultantos pattern.
Provides a clean interface to Google Gemini for marketing AI insights.
"""
import logging
import time
from typing import Any, Dict, Generator, List, Optional
from backend.config import settings

logger = logging.getLogger(__name__)


class GeminiClient:
    """
    Thin wrapper around Google Generative AI (Gemini).
    Handles retries, error logging, and streaming.
    Falls back to a mock response if API key is not configured.
    """

    MAX_RETRIES = 3
    RETRY_DELAY = 2.0  # seconds

    def __init__(self):
        self._client = None
        self._available = self._initialize()

    def _initialize(self) -> bool:
        """Initialize Gemini client if API key is available."""
        if not settings.gemini_api_key or settings.gemini_api_key in (
            "test-key-placeholder", "your-gemini-api-key-here", ""
        ):
            logger.warning(
                "GEMINI_API_KEY not configured. AI features will return demo responses. "
                "Set GEMINI_API_KEY in .env for full functionality."
            )
            return False

        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.gemini_api_key)
            self._client = genai.GenerativeModel(
                model_name=settings.gemini_model,
                system_instruction=None,  # Set per-call
            )
            logger.info(f"Gemini client initialized | model={settings.gemini_model}")
            return True
        except ImportError:
            logger.warning("google-generativeai not installed. Install with: pip install google-generativeai")
            return False
        except Exception as e:
            logger.error(f"Gemini initialization failed: {e}")
            return False

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = None,
        max_tokens: int = None,
    ) -> str:
        """
        Generate a response from Gemini.

        Args:
            prompt: User prompt / instruction.
            system_instruction: Optional system-level instruction.
            temperature: Sampling temperature (0-1).
            max_tokens: Maximum output tokens.

        Returns:
            Generated text response.
        """
        if not self._available:
            return self._mock_response(prompt)

        temperature = temperature or settings.llm_temperature
        max_tokens = max_tokens or settings.llm_max_tokens

        import google.generativeai as genai

        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        for attempt in range(self.MAX_RETRIES):
            try:
                if system_instruction:
                    model = genai.GenerativeModel(
                        model_name=settings.gemini_model,
                        system_instruction=system_instruction,
                    )
                else:
                    model = self._client

                response = model.generate_content(
                    prompt,
                    generation_config=generation_config,
                )
                return response.text or ""

            except Exception as e:
                logger.warning(f"Gemini attempt {attempt + 1} failed: {e}")
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY * (attempt + 1))
                else:
                    logger.error(f"All Gemini retries exhausted: {e}")
                    return self._mock_response(prompt)

        return self._mock_response(prompt)

    def generate_with_history(
        self,
        messages: List[Dict[str, str]],
        system_instruction: Optional[str] = None,
    ) -> str:
        """
        Generate a response in a multi-turn conversation context.

        Args:
            messages: List of {role: 'user'|'model', content: str} dicts.
            system_instruction: Optional system instruction.

        Returns:
            Model response text.
        """
        if not self._available:
            last_msg = messages[-1]["content"] if messages else ""
            return self._mock_response(last_msg)

        try:
            import google.generativeai as genai

            model = genai.GenerativeModel(
                model_name=settings.gemini_model,
                system_instruction=system_instruction,
            )
            chat = model.start_chat(history=[
                {"role": m["role"], "parts": [m["content"]]}
                for m in messages[:-1]
            ])
            response = chat.send_message(messages[-1]["content"])
            return response.text or ""
        except Exception as e:
            logger.error(f"Gemini chat failed: {e}")
            return self._mock_response(messages[-1]["content"] if messages else "")

    def _mock_response(self, prompt: str) -> str:
        """
        Return a structured demo response when Gemini is unavailable.
        Detects query type from keywords and returns appropriate demo content.
        """
        prompt_lower = prompt.lower()

        if "forecast" in prompt_lower or "revenue" in prompt_lower:
            return (
                "**Forecast Outlook** *(Demo Mode — configure GEMINI_API_KEY for live AI)*\n\n"
                "Based on your historical performance data, revenue is projected to grow 8-12% "
                "over the next 30 days driven by continued strong Google Ads performance (ROAS 3.8x) "
                "and improving conversion rates. The P50 forecast represents our median expectation "
                "under current budget allocation.\n\n"
                "**Key Drivers:** Seasonal tailwinds (+5%), improved Meta targeting efficiency (+3%), "
                "and consistent Google Shopping campaign performance (+4%).\n\n"
                "**Recommended Actions:**\n"
                "1. Increase Google Shopping budget by 15% to capture peak demand\n"
                "2. Pause underperforming Meta Video Awareness campaigns and reallocate to Catalog Sales"
            )

        if "roas" in prompt_lower or "meta" in prompt_lower:
            return (
                "**Meta ROAS Analysis** *(Demo Mode)*\n\n"
                "Meta ROAS has declined 18% over the past 14 days, dropping from 3.2x to 2.6x. "
                "The primary cause appears to be audience saturation on your Prospecting Lookalike "
                "campaigns — CPMs have risen 22% while CTR has fallen 15%.\n\n"
                "**Immediate Action:** Refresh creative assets on Prospecting campaigns and expand "
                "the lookalike seed audience to 3% similarity to reduce frequency."
            )

        if "budget" in prompt_lower or "channel" in prompt_lower:
            return (
                "**Budget Recommendation** *(Demo Mode)*\n\n"
                "Based on current ROAS data: Google (3.8x) > Microsoft (3.2x) > Meta (2.6x). "
                "Shifting 10% of Meta budget to Google is projected to increase blended ROAS from "
                "3.2x to 3.5x and generate an additional $4,200 in revenue at current efficiency levels.\n\n"
                "Use the Budget Simulator to model specific allocation scenarios."
            )

        if "risk" in prompt_lower:
            return (
                "**Risk Assessment** *(Demo Mode)*\n\n"
                "**High Risk:** Meta ROAS declining trend (3 consecutive weeks below baseline)\n"
                "**Medium Risk:** Google CPC increased 12% — monitor for bid inflation\n"
                "**Low Risk:** Microsoft Ads performing at expected levels\n\n"
                "Overall Risk Level: **Amber** — Immediate action recommended on Meta campaigns."
            )

        # Generic copilot response
        return (
            "*(Demo Mode — configure GEMINI_API_KEY in your .env file for live AI responses)*\n\n"
            "I can help you analyze your marketing performance data, explain forecasts, "
            "identify anomalies, and recommend budget optimizations. Try asking:\n"
            "- 'Why is Meta ROAS decreasing?'\n"
            "- 'How much revenue will I lose if Google budget drops 20%?'\n"
            "- 'Which channel should get more budget?'"
        )


# Singleton instance
gemini_client = GeminiClient()
