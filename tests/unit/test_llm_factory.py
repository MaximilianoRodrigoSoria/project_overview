from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

from src.adapters.llm_factory import create_llm
from src.adapters.llm_ollama import OllamaLLM
from src.config.settings import settings


def test_llm_factory_creates_ollama():
    settings.LLM_PROVIDER = "ollama"
    llm = create_llm()
    assert isinstance(llm, OllamaLLM)


def test_llm_factory_invalid_provider():
    settings.LLM_PROVIDER = "invalid"
    with pytest.raises(ValueError):
        create_llm()
