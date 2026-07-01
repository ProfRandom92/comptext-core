import subprocess
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from comptext.terminal.renderer import render_logo, render_image, get_logo_path

def test_get_logo_path():
    path = get_logo_path()
    assert path is not None
    assert path.name == "comptext-logo-braille-color.ans"
    assert path.exists()

def test_render_logo(capsys):
    # Call render_logo
    render_logo()
    
    # Check it prints something from the logo file (since it exists)
    captured = capsys.readouterr()
    assert len(captured.out) > 0
    # The printed text should contain ANSI escape sequences or the logo text
    # Let's assert it printed successfully
    assert "COMPTEXT" in captured.out or "\033" in captured.out

def test_render_logo_not_found(capsys):
    # Mock get_logo_path to return None
    with patch("comptext.terminal.renderer.get_logo_path", return_value=None):
        render_logo()
        captured = capsys.readouterr()
        assert "COMPTEXT — THE OPERATING SYSTEM FOR CONTEXT" in captured.out

def test_render_image_chafa_fallback(capsys):
    # Mock shutil.which to return None
    with patch("shutil.which", return_value=None):
        render_image("fake_image.png")
        captured = capsys.readouterr()
        # Should fall back to printing the logo
        assert len(captured.out) > 0
        assert "COMPTEXT" in captured.out or "\033" in captured.out

def test_render_image_chafa_exists(capsys):
    # Mock shutil.which to return path
    with patch("shutil.which", return_value="/usr/bin/chafa"):
        # Mock subprocess.run
        with patch("subprocess.run") as mock_run:
            mock_res = MagicMock()
            mock_res.stdout = "Chafa Rendered Output"
            mock_run.return_value = mock_res
            
            render_image("fake_image.png", size=60, symbols="ascii", colors="16")
            
            captured = capsys.readouterr()
            assert "Chafa Rendered Output" in captured.out
            mock_run.assert_called_once()
            
            # Check arguments passed to subprocess.run
            args, kwargs = mock_run.call_args
            cmd = args[0]
            assert cmd[0] == "/usr/bin/chafa"
            assert "--size" in cmd
            assert "60" in cmd
            assert "--symbols" in cmd
            assert "ascii" in cmd
            assert "--colors" in cmd
            assert "16" in cmd
            assert "fake_image.png" in cmd

def test_repl_style_validity():
    from comptext.repl import CompTextREPL
    assert CompTextREPL.STYLE is not None
