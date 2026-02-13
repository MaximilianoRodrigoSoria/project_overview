"""
Contract tests for ports and their adapters.
"""

from src.adapters.cache_memory import MemoryCache
from src.adapters.llm_anthropic import AnthropicLLM
from src.adapters.llm_google import GoogleLLM
from src.adapters.llm_ollama import OllamaLLM
from src.adapters.llm_openai import OpenAILLM
from src.adapters.report_writer_fs import FileSystemReportWriter
from src.ports.cache_port import CachePort
from src.ports.llm_port import LLMPort
from src.ports.report_writer_port import ReportWriterPort


def test_llm_adapters_implement_port():
    for adapter_cls in (OllamaLLM, OpenAILLM, AnthropicLLM, GoogleLLM):
        assert issubclass(adapter_cls, LLMPort)


def test_cache_adapter_implements_port():
    assert issubclass(MemoryCache, CachePort)


def test_report_writer_implements_port():
    assert issubclass(FileSystemReportWriter, ReportWriterPort)
