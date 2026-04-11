from unittest.mock import MagicMock, patch

from langchain_core.messages import AIMessage

import main


def test_main_smoke_mode_uses_builtin_query():
    with patch("main.create_llm") as mock_create_llm, \
         patch("main.build_graph") as mock_build_graph, \
         patch("main.run_interaction") as mock_run_interaction:
        mock_create_llm.return_value = MagicMock()
        mock_build_graph.return_value = MagicMock()

        exit_code = main.main(["--smoke-test"])

        assert exit_code == 0
        mock_run_interaction.assert_called_once()
        _, kwargs = mock_run_interaction.call_args
        assert kwargs["interactive"] is False
        assert kwargs["initial_query"] == main.DEFAULT_SMOKE_QUERY


def test_run_interaction_non_interactive_skips_input():
    app = MagicMock()
    app.stream.return_value = iter(
        [{"Researcher": {"messages": [AIMessage(content="research result")]}}]
    )

    with patch("builtins.input", side_effect=AssertionError("input should not be called")) as mock_input:
        result = main.run_interaction(app, initial_query="smoke query", interactive=False)

    assert result is None
    mock_input.assert_not_called()
    app.stream.assert_called_once()
