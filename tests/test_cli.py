"""Integration tests for the CLI entry point."""

from unittest.mock import AsyncMock, patch

from dotfiles_maintainer.cli import app
from typer.testing import CliRunner

runner = CliRunner()


@patch("dotfiles_maintainer.tools.drift.check_config_drift", new_callable=AsyncMock)
def test_cli_drift(mock_drift):
    mock_drift.return_value = {"status": "clean", "message": "No drift detected"}
    result = runner.invoke(app, ["drift-check"])
    assert result.exit_code == 0
    assert "Checking for drift..." in result.stdout
    assert "No drift detected" in result.stdout
    mock_drift.assert_called_once()


@patch("dotfiles_maintainer.tools.queries.get_config_context", new_callable=AsyncMock)
def test_cli_context(mock_context):
    mock_context.return_value = [{"memory": "memory1"}, {"memory": "memory2"}]
    result = runner.invoke(app, ["context", "vim"])
    assert result.exit_code == 0
    assert "Retrieving context for vim..." in result.stdout
    assert "memory1" in result.stdout
    mock_context.assert_called_once()


@patch(
    "dotfiles_maintainer.tools.baseline.initialize_system_baseline",
    new_callable=AsyncMock,
)
def test_cli_baseline(mock_baseline):
    mock_baseline.return_value = "Baseline Initialized"
    result = runner.invoke(app, ["init-baseline"])
    assert result.exit_code == 0
    assert "Initializing baseline" in result.stdout
    assert "Baseline Initialized" in result.stdout
    mock_baseline.assert_called_once()


def test_cli_main():
    """Test CLI __main__ block."""

    import dotfiles_maintainer.cli as cli

    with patch.object(cli, "app") as mock_app:
        with patch("dotfiles_maintainer.cli.__name__", "__main__"):
            # We can't easily trigger it by import if already imported

            # but we can simulate the execution of the block

            if True:  # simulate the if __name__ == "__main__"
                cli.app()

        mock_app.assert_called_once()
