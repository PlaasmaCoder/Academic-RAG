"""Shared Gemini client setup and configuration checks."""

import os
from functools import lru_cache

from dotenv import load_dotenv
from google import genai

from src.errors import ConfigurationError

load_dotenv()


@lru_cache(maxsize=2)
def _client_for(api_key: str):
    return genai.Client(api_key=api_key)


def get_gemini_client():
    """Create or reuse a Gemini client, reporting missing configuration clearly."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        # Streamlit Community Cloud stores deployed secrets in st.secrets.
        # Local development continues to use the .env file above.
        try:
            import streamlit as st

            api_key = str(st.secrets.get("GEMINI_API_KEY", "")).strip()
        except Exception:
            # Streamlit raises when no secrets file is configured locally.
            api_key = ""

    if not api_key:
        raise ConfigurationError(
            "GEMINI_API_KEY is missing. For local use, add it to .env; "
            "for Streamlit Cloud, add it under the app's Settings > Secrets."
        )
    try:
        return _client_for(api_key)
    except Exception as error:
        raise ConfigurationError("Could not initialize the Gemini client. Check the installed google-genai package.") from error
