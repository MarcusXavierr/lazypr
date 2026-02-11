"""Tests for AI generation (with mocked LLM calls)."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from lazypr import (
    create_pr_agent,
    generate_pr_content,
    PRContent,
    AIError,
)


class TestCreatePrAgent:
    """Tests for create_pr_agent() function."""

    def test_creates_agent_with_configured_model(self):
        """Should create agent with model from env var."""
        with patch("lazypr.get_model_name") as mock_model:
            mock_model.return_value = "cerebras:zai-glm-4.7"
            with patch("lazypr.Agent") as mock_agent_class:
                create_pr_agent()
                mock_agent_class.assert_called_once()
                call_args = mock_agent_class.call_args
                assert "cerebras:zai-glm-4.7" in str(call_args)

    def test_creates_agent_without_api_key(self):
        """Should create agent without LAZYPR_API_KEY (provider-specific env vars can be used)."""
        with patch("lazypr.get_model_name") as mock_model:
            mock_model.return_value = "cerebras:zai-glm-4.7"
            with patch("lazypr.get_api_key") as mock_api_key:
                mock_api_key.return_value = None
                with patch("lazypr.Agent") as mock_agent_class:
                    create_pr_agent()
                    mock_agent_class.assert_called_once()

    def test_raises_error_when_model_not_configured(self):
        """Should raise AIError when LAZYPR_MODEL is not set."""
        with patch("lazypr.os.environ.get") as mock_env:
            mock_env.return_value = None
            with pytest.raises(AIError, match="LAZYPR_MODEL"):
                create_pr_agent()


class TestGeneratePrContent:
    """Tests for generate_pr_content() function."""

    @pytest.mark.asyncio
    async def test_returns_pr_content(self):
        """Should return PRContent with title and description."""
        mock_result = MagicMock()
        mock_result.output = PRContent(
            title="Add user authentication",
            description="This PR adds OAuth2 authentication flow."
        )

        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(return_value=mock_result)

        with patch("lazypr.create_pr_agent", return_value=mock_agent):
            result = await generate_pr_content("some diff content")
            assert isinstance(result, PRContent)
            assert result.title == "Add user authentication"
            assert "OAuth2" in result.description

    @pytest.mark.asyncio
    async def test_includes_diff_in_prompt(self):
        """Should include the diff in the AI prompt."""
        diff_content = "diff --git a/file.py b/file.py\n+line"
        mock_agent = MagicMock()
        mock_agent.run = AsyncMock()

        with patch("lazypr.create_pr_agent", return_value=mock_agent):
            await generate_pr_content(diff_content)
            # Get the prompt passed to the agent
            call_args = mock_agent.run.call_args
            # The prompt should be the first positional argument or 'prompt' kwarg
            prompt = call_args[0][0] if call_args[0] else call_args[1].get('prompt', '')
            assert diff_content in prompt
