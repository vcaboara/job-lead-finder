#!/usr/bin/env /workspace/tmp_windsurf/venv/bin/python3

import argparse
import base64
import logging
import mimetypes
import os
import sys
from pathlib import Path
from typing import Optional

import google.generativeai as genai
from anthropic import Anthropic
from dotenv import load_dotenv
from openai import AzureOpenAI, OpenAI

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def load_environment():
    """Load environment variables from .env files in order of precedence"""
    # Order of precedence:
    # 1. System environment variables (already loaded)
    # 2. .env.local (user-specific overrides)
    # 3. .env (project defaults)
    # 4. .env.example (example configuration)

    env_files = [".env.local", ".env", ".env.example"]
    env_loaded = False

    logger.debug("Current working directory: %s", Path(".").absolute())
    logger.debug("Looking for environment files: %s", env_files)

    for env_file in env_files:
        env_path = Path(".") / env_file
        logger.debug("Checking %s", env_path.absolute())
        if env_path.exists():
            logger.info("Found %s, loading variables...", env_file)
            load_dotenv(dotenv_path=env_path)
            env_loaded = True
            logger.info("Loaded environment variables from %s", env_file)
            # Log loaded keys (but not values for security)
            with open(env_path) as f:
                keys = [line.split("=")[0].strip() for line in f if "=" in line and not line.startswith("#")]
                logger.debug("Keys loaded from %s: %s", env_file, keys)

    if not env_loaded:
        logger.warning("No .env files found. Using system environment variables only.")
        logger.debug("Available system environment variables: %s", list(os.environ.keys()))


# Load environment variables at module import
load_environment()


def encode_image_file(image_path: str) -> tuple[str, str]:
    """
    Encode an image file to base64 and determine its MIME type.

    Args:
        image_path (str): Path to the image file

    Returns:
        tuple: (base64_encoded_string, mime_type)
    """
    mime_type, _ = mimetypes.guess_type(image_path)
    if not mime_type:
        mime_type = "image/png"  # Default to PNG if type cannot be determined

    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")

    return encoded_string, mime_type


def create_llm_client(provider="openai"):
    """Create an LLM client for the specified provider."""

    provider_configs = {
        "openai": {
            "env_key": "OPENAI_API_KEY",
            "client_class": OpenAI,
            "kwargs": lambda key: {"api_key": key},
        },
        "azure": {
            "env_key": "AZURE_OPENAI_API_KEY",
            "client_class": AzureOpenAI,
            "kwargs": lambda key: {
                "api_key": key,
                "api_version": "2024-08-01-preview",
                "azure_endpoint": "https://msopenai.openai.azure.com",
            },
        },
        "deepseek": {
            "env_key": "DEEPSEEK_API_KEY",
            "client_class": OpenAI,
            "kwargs": lambda key: {"api_key": key, "base_url": "https://api.deepseek.com/v1"},
        },
        "siliconflow": {
            "env_key": "SILICONFLOW_API_KEY",
            "client_class": OpenAI,
            "kwargs": lambda key: {"api_key": key, "base_url": "https://api.siliconflow.cn/v1"},
        },
        "anthropic": {
            "env_key": "ANTHROPIC_API_KEY",
            "client_class": Anthropic,
            "kwargs": lambda key: {"api_key": key},
        },
        "gemini": {
            "env_key": "GOOGLE_API_KEY",
            "client_class": None,  # Special case
            "kwargs": lambda key: {"api_key": key},
        },
        "local": {
            "env_key": None,  # No API key required
            "client_class": OpenAI,
            "kwargs": lambda key: {"base_url": "http://192.168.180.137:8006/v1", "api_key": "not-needed"},
        },
    }

    if provider not in provider_configs:
        raise ValueError(f"Unsupported provider: {provider}")

    config = provider_configs[provider]

    # Get API key if required
    if config["env_key"]:
        api_key = os.getenv(config["env_key"])
        if not api_key:
            raise ValueError(f"{config['env_key']} not found in environment variables")
    else:
        api_key = None

    # Special case for Gemini
    if provider == "gemini":
        genai.configure(api_key=api_key)
        return genai

    # Create and return client
    return config["client_class"](**config["kwargs"](api_key))


def query_llm(
    prompt: str, client=None, model=None, provider="openai", image_path: Optional[str] = None
) -> Optional[str]:
    """
    Query an LLM with a prompt and optional image attachment.

    Args:
        prompt (str): The text prompt to send
        client: The LLM client instance
        model (str, optional): The model to use
        provider (str): The API provider to use
        image_path (str, optional): Path to an image file to attach

    Returns:
        Optional[str]: The LLM's response or None if there was an error
    """
    if client is None:
        client = create_llm_client(provider)

    # Default models per provider
    default_models = {
        "openai": "gpt-4o",
        "azure": os.getenv("AZURE_OPENAI_MODEL_DEPLOYMENT", "gpt-4o-ms"),
        "deepseek": "deepseek-chat",
        "siliconflow": "deepseek-ai/DeepSeek-R1",
        "anthropic": "claude-3-7-sonnet-20250219",
        "gemini": "gemini-2.5-flash",
        "local": "Qwen/Qwen2.5-32B-Instruct-AWQ",
    }

    model = model or default_models.get(provider, "gpt-4o")

    try:
        # OpenAI-compatible providers (use chat completions API)
        if provider in ["openai", "local", "deepseek", "azure", "siliconflow"]:
            return _query_openai_compatible(client, model, prompt, image_path, provider)
        elif provider == "anthropic":
            return _query_anthropic(client, model, prompt, image_path)
        elif provider == "gemini":
            return _query_gemini(client, model, prompt, image_path)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    except Exception as e:
        logger.error("Error querying LLM: %s", e, exc_info=True)
        return None


def _query_openai_compatible(client, model: str, prompt: str, image_path: Optional[str], provider: str) -> str:
    """Query OpenAI-compatible APIs (OpenAI, Azure, DeepSeek, SiliconFlow, Local)."""
    messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]

    # Add image content if provided (only OpenAI supports vision currently)
    if image_path and provider == "openai":
        encoded_image, mime_type = encode_image_file(image_path)
        messages[0]["content"].append(
            {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{encoded_image}"}}
        )

    kwargs = {"model": model, "messages": messages, "temperature": 0.7}

    # Special handling for o1 models
    if model == "o1":
        kwargs["response_format"] = {"type": "text"}
        kwargs["reasoning_effort"] = "low"
        del kwargs["temperature"]

    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message.content


def _query_anthropic(client, model: str, prompt: str, image_path: Optional[str]) -> str:
    """Query Anthropic Claude API."""
    content = [{"type": "text", "text": prompt}]

    # Add image content if provided
    if image_path:
        encoded_image, mime_type = encode_image_file(image_path)
        content.append({"type": "image", "source": {"type": "base64", "media_type": mime_type, "data": encoded_image}})

    response = client.messages.create(model=model, max_tokens=1000, messages=[{"role": "user", "content": content}])
    return response.content[0].text


def _query_gemini(client, model_name: str, prompt: str, image_path: Optional[str]) -> str:
    """Query Google Gemini API."""
    model = client.GenerativeModel(model_name)

    if image_path:
        file = genai.upload_file(image_path, mime_type="image/png")
        chat_session = model.start_chat(history=[{"role": "user", "parts": [file, prompt]}])
    else:
        chat_session = model.start_chat(history=[{"role": "user", "parts": [prompt]}])

    response = chat_session.send_message(prompt)
    return response.text


def main():
    parser = argparse.ArgumentParser(description="Query an LLM with a prompt")
    parser.add_argument("--prompt", type=str, help="The prompt to send to the LLM", required=True)
    parser.add_argument(
        "--provider",
        choices=["openai", "anthropic", "gemini", "local", "deepseek", "azure", "siliconflow"],
        default="openai",
        help="The API provider to use",
    )
    parser.add_argument("--model", type=str, help="The model to use (default depends on provider)")
    parser.add_argument("--image", type=str, help="Path to an image file to attach to the prompt")
    args = parser.parse_args()

    if not args.model:
        if args.provider == "openai":
            args.model = "gpt-4o"
        elif args.provider == "deepseek":
            args.model = "deepseek-chat"
        elif args.provider == "siliconflow":
            args.model = "deepseek-ai/DeepSeek-R1"
        elif args.provider == "anthropic":
            args.model = "claude-3-7-sonnet-20250219"
        elif args.provider == "gemini":
            args.model = "gemini-2.5-flash"
        elif args.provider == "azure":
            # Get from env with fallback
            args.model = os.getenv("AZURE_OPENAI_MODEL_DEPLOYMENT", "gpt-4o-ms")

    client = create_llm_client(args.provider)
    response = query_llm(args.prompt, client, model=args.model, provider=args.provider, image_path=args.image)
    if response:
        print(response)  # Output to stdout for CLI usage
    else:
        logger.error("Failed to get response from LLM")
        sys.exit(1)


if __name__ == "__main__":
    main()
