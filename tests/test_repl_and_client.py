import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from comptext.repl import CompTextREPL
from comptext.state import AppState
from comptext.nvidia_client import NVIDIAClient
import httpx

@pytest.mark.asyncio
async def test_repl_exits_on_quit():
    with patch("comptext.repl.PROMPT_TOOLKIT_AVAILABLE", False):
        app_state = AppState()
        repl = CompTextREPL(app_state)
        
        # Mock prompt to return /quit
        repl.prompt = AsyncMock(return_value="/quit")
        
        # Run the REPL loop - it should exit immediately
        await repl.run()
        
        assert not repl._running

@pytest.mark.asyncio
async def test_repl_exits_on_exit():
    with patch("comptext.repl.PROMPT_TOOLKIT_AVAILABLE", False):
        app_state = AppState()
        repl = CompTextREPL(app_state)
        
        # Mock prompt to return /exit
        repl.prompt = AsyncMock(return_value="/exit")
        
        # Run the REPL loop - it should exit immediately
        await repl.run()
        
        assert not repl._running

@pytest.mark.asyncio
async def test_nvidia_client_non_streaming():
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"choices": [{"message": {"content": "Hello"}}]}
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        client = NVIDIAClient(api_key="nvapi-test")
        
        # Call chat in non-streaming mode
        results = []
        async for chunk in client.chat(messages=[], stream=False):
            results.append(chunk)
            
        assert len(results) == 1
        assert results[0] == {"choices": [{"message": {"content": "Hello"}}]}
        
        # Verify that post was called and stream is set to False
        mock_client.post.assert_called_once()
        args, kwargs = mock_client.post.call_args
        assert kwargs["json"]["stream"] is False
