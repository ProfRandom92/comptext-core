import pytest
from unittest.mock import patch, MagicMock
from comptext.providers.google import GoogleProvider
from comptext.providers.xai import XAIProvider
from comptext.providers.nvidia import NVIDIAProvider
from comptext.providers import (
    get_provider,
    ProviderAuthError,
    ProviderRateLimitError,
    ProviderConnectionError,
    ProviderAPIError
)
from google.genai import types
from openai import RateLimitError

def test_google_provider_complete():
    with patch("google.genai.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Gemini complete response"
        mock_client.models.generate_content.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        provider = GoogleProvider(api_key="test_key")
        res = provider.complete("hello")
        assert res == "Gemini complete response"
        
        mock_client_class.assert_called_once_with(api_key="test_key")
        mock_client.models.generate_content.assert_called_with(
            model="gemini-2.5-pro",
            contents="hello"
        )

def test_google_provider_chat():
    with patch("google.genai.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Gemini chat response"
        mock_client.models.generate_content.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        provider = GoogleProvider(api_key="test_key")
        
        history = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "hello"}
        ]
        
        res = provider.chat(history)
        assert res == "Gemini chat response"
        
        args, kwargs = mock_client.models.generate_content.call_args
        assert kwargs["model"] == "gemini-2.5-pro"
        
        contents = kwargs["contents"]
        assert len(contents) == 2
        assert contents[0].role == "user"
        assert contents[0].parts[0].text == "hi"
        assert contents[1].role == "model"
        assert contents[1].parts[0].text == "hello"
        
        config = kwargs["config"]
        assert config.system_instruction == "You are helpful"

def test_google_provider_missing_key():
    provider = GoogleProvider(api_key="")
    with pytest.raises(ProviderAuthError) as exc:
        provider.complete("hi")
    assert "GOOGLE_API_KEY" in str(exc.value)

def test_xai_provider_complete():
    provider = XAIProvider(api_key="test_key")
    
    with patch("httpx.post") as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Grok complete response"}}]
        }
        mock_post.return_value = mock_response
        
        res = provider.complete("hello")
        assert res == "Grok complete response"
        
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert kwargs["json"]["model"] == "grok-3"
        assert kwargs["json"]["messages"] == [{"role": "user", "content": "hello"}]
        assert kwargs["headers"]["Authorization"] == "Bearer test_key"

def test_xai_provider_chat():
    provider = XAIProvider(api_key="test_key")
    
    with patch("httpx.post") as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Grok chat response"}}]
        }
        mock_post.return_value = mock_response
        
        history = [{"role": "user", "content": "hello"}]
        res = provider.chat(history)
        assert res == "Grok chat response"
        
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert kwargs["json"]["messages"] == history

def test_xai_provider_missing_key():
    provider = XAIProvider(api_key="")
    with pytest.raises(ProviderAuthError) as exc:
        provider.complete("hi")
    assert "XAI_API_KEY" in str(exc.value)

def test_get_provider_registration():
    with patch("google.genai.Client"):
        google_prov = get_provider("google", api_key="abc")
        assert isinstance(google_prov, GoogleProvider)
    
    xai_prov = get_provider("xai", api_key="xyz")
    assert isinstance(xai_prov, XAIProvider)
    
    with patch("comptext.providers.nvidia.OpenAI"):
        nvidia_prov = get_provider("nvidia", api_key="nvapi-123")
        assert isinstance(nvidia_prov, NVIDIAProvider)
        
    with pytest.raises(ValueError):
        get_provider("unknown")

def test_nvidia_provider_complete():
    with patch("comptext.providers.nvidia.OpenAI") as mock_openai_class:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "NVIDIA complete response"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        provider = NVIDIAProvider(api_key="nvapi-test_key", model="deepseek-ai/deepseek-v4-flash")
        res = provider.complete("hello")
        assert res == "NVIDIA complete response"
        
        mock_openai_class.assert_called_once_with(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key="nvapi-test_key"
        )
        mock_client.chat.completions.create.assert_called_once_with(
            model="deepseek-ai/deepseek-v4-flash",
            messages=[{"role": "user", "content": "hello"}],
            stream=False
        )

def test_nvidia_provider_chat():
    with patch("comptext.providers.nvidia.OpenAI") as mock_openai_class:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "NVIDIA chat response"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        provider = NVIDIAProvider(api_key="nvapi-test_key", model="deepseek-ai/deepseek-v4-flash")
        history = [{"role": "user", "content": "hi"}]
        res = provider.chat(history)
        assert res == "NVIDIA chat response"
        
        mock_client.chat.completions.create.assert_called_once_with(
            model="deepseek-ai/deepseek-v4-flash",
            messages=history,
            stream=False
        )

def test_nvidia_provider_invalid_key():
    with pytest.raises(ProviderAuthError) as exc:
        NVIDIAProvider(api_key="invalid_key")
    assert "must start with 'nvapi-'" in str(exc.value)

    provider = NVIDIAProvider(api_key="")
    with pytest.raises(ProviderAuthError) as exc2:
        provider.complete("hello")
    assert "NVIDIA_API_KEY" in str(exc2.value)

def test_nvidia_provider_rate_limit_retry():
    with patch("comptext.providers.nvidia.OpenAI") as mock_openai_class:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "NVIDIA success after retry"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        
        import httpx
        fake_request = httpx.Request("POST", "https://integrate.api.nvidia.com/v1/chat/completions")
        fake_response = httpx.Response(429, request=fake_request)
        rate_limit_err = RateLimitError("Rate limit exceeded", response=fake_response, body=None)
        
        mock_client.chat.completions.create.side_effect = [
            rate_limit_err,
            rate_limit_err,
            mock_response
        ]
        mock_openai_class.return_value = mock_client
        
        provider = NVIDIAProvider(api_key="nvapi-test_key")
        
        with patch("time.sleep") as mock_sleep:
            res = provider.complete("hello")
            assert res == "NVIDIA success after retry"
            assert mock_client.chat.completions.create.call_count == 3
            assert mock_sleep.call_count == 2
            mock_sleep.assert_any_call(1.0)
            mock_sleep.assert_any_call(2.0)

def test_nvidia_provider_rate_limit_exhausted():
    with patch("comptext.providers.nvidia.OpenAI") as mock_openai_class:
        mock_client = MagicMock()
        
        import httpx
        fake_request = httpx.Request("POST", "https://integrate.api.nvidia.com/v1/chat/completions")
        fake_response = httpx.Response(429, request=fake_request)
        rate_limit_err = RateLimitError("Rate limit exceeded", response=fake_response, body=None)
        
        mock_client.chat.completions.create.side_effect = [rate_limit_err] * 5
        mock_openai_class.return_value = mock_client
        
        provider = NVIDIAProvider(api_key="nvapi-test_key")
        
        with patch("time.sleep") as mock_sleep:
            with pytest.raises(ProviderRateLimitError) as exc:
                provider.complete("hello")
            assert "rate limits exceeded after 3 retries" in str(exc.value)
            assert mock_client.chat.completions.create.call_count == 4

def test_google_provider_connection_error():
    with patch("google.genai.Client") as mock_client_class:
        mock_client = MagicMock()
        import httpx
        mock_client.models.generate_content.side_effect = httpx.ConnectError("Connection timed out")
        mock_client_class.return_value = mock_client
        
        provider = GoogleProvider(api_key="test_key")
        with pytest.raises(ProviderConnectionError) as exc:
            provider.complete("hello")
        assert "connection failed" in str(exc.value)

def test_xai_provider_api_error():
    provider = XAIProvider(api_key="test_key")
    with patch("httpx.post") as mock_post:
        import httpx
        fake_request = httpx.Request("POST", XAIProvider.BASE_URL)
        fake_response = httpx.Response(400, request=fake_request)
        # Emulate raise_for_status raising HTTPStatusError
        fake_response.raise_for_status = MagicMock(side_effect=httpx.HTTPStatusError("Bad Request", request=fake_request, response=fake_response))
        mock_post.return_value = fake_response
        
        with pytest.raises(ProviderAPIError) as exc:
            provider.complete("hello")
        assert "status error" in str(exc.value)

def test_nvidia_provider_api_auth_error():
    with patch("comptext.providers.nvidia.OpenAI") as mock_openai_class:
        mock_client = MagicMock()
        from openai import AuthenticationError
        import httpx
        fake_request = httpx.Request("POST", "https://integrate.api.nvidia.com/v1/chat/completions")
        fake_response = httpx.Response(401, request=fake_request)
        mock_client.chat.completions.create.side_effect = AuthenticationError(
            "Invalid authentication", response=fake_response, body=None
        )
        mock_openai_class.return_value = mock_client
        
        provider = NVIDIAProvider(api_key="nvapi-test_key")
        with pytest.raises(ProviderAuthError) as exc:
            provider.complete("hello")
        assert "authentication failed" in str(exc.value)


