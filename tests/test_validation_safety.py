import os
import pytest
from pathlib import Path
from comptext.core.capabilities import run_validation_step

def test_normal_allowed_command():
    res = run_validation_step("python -V")
    assert res["ok"] is True
    assert res["exit_code"] == 0

def test_echo_normal():
    # If the system can execute echo, it will run. On some systems "echo" might be a shell builtin,
    # but under shell=False, executing "echo" directly requires a binary or it fails.
    res = run_validation_step("echo hello")
    # Both success or fail due to no binary is fine as long as no shell is opened.
    assert "hello" in res.get("stdout_excerpt", "") or not res["ok"]

def test_argument_with_spaces():
    res = run_validation_step('python -c "print(\'hello world\')"')
    assert res["ok"] is True
    assert res["exit_code"] == 0
    assert "hello world" in res["stdout_excerpt"]

def test_missing_executable():
    res = run_validation_step("nonexistent_command_12345_abc")
    assert res["ok"] is False
    assert res["exit_code"] == -1

def test_non_zero_exitcode():
    res = run_validation_step('python -c "import sys; sys.exit(42)"')
    assert res["ok"] is False
    assert res["exit_code"] == 42

def test_and_chaining_blocked():
    res = run_validation_step("python -c \"print('first')\" && python -c \"print('second')\"")
    # Under shell=False, the second command 'python -c "print('second')"' is not executed
    assert "second" not in res.get("stdout_excerpt", "")

def test_or_chaining_blocked():
    res = run_validation_step("nonexistent_command_12345_abc || python -c \"print('second')\"")
    # Under shell=False, the second command is not executed
    assert "second" not in res.get("stdout_excerpt", "")

def test_semicolon_chaining_blocked():
    res = run_validation_step("python -c \"print('first')\" ; python -c \"print('second')\"")
    assert "second" not in res.get("stdout_excerpt", "")

def test_pipeline_blocked():
    cmd = 'python -c "print(\'hello\')" | python -c "import sys; print(\'second\')"'
    res = run_validation_step(cmd)
    assert "second" not in res.get("stdout_excerpt", "")

def test_redirection_blocked():
    marker_path = Path("marker_test_redirect.txt")
    if marker_path.exists():
        marker_path.unlink()
    try:
        res = run_validation_step(f"python -c \"print('leak')\" > {marker_path.name}")
        assert not marker_path.exists()
    finally:
        if marker_path.exists():
            marker_path.unlink()

def test_append_redirection_blocked():
    marker_path = Path("marker_test_append.txt")
    if marker_path.exists():
        marker_path.unlink()
    try:
        res = run_validation_step(f"python -c \"print('leak')\" >> {marker_path.name}")
        assert not marker_path.exists()
    finally:
        if marker_path.exists():
            marker_path.unlink()

def test_input_redirection_blocked():
    # If shell redirection was active, reading from a nonexistent file would crash the shell.
    # Under shell=False, it succeeds (exits with 0) because the '<' and file are ignored/treated as raw args.
    res = run_validation_step("python -c \"import sys; print('success')\" < nonexistent_file_abc.txt")
    assert res["exit_code"] == 0
    assert "success" in res.get("stdout_excerpt", "")

def test_subshell_dollar_blocked():
    res = run_validation_step("python -c \"import sys; print(sys.argv)\" $(echo hello)")
    # '$(echo' will be treated as raw literal argument
    assert any("$(echo" in arg for arg in [res.get("stdout_excerpt", ""), res.get("stderr_excerpt", "")]) or res["exit_code"] != 0

def test_backticks_blocked():
    res = run_validation_step("python -c \"import sys; print(sys.argv)\" `echo hello`")
    # '`echo' will be treated as raw literal argument
    assert any("`echo" in arg for arg in [res.get("stdout_excerpt", ""), res.get("stderr_excerpt", "")]) or res["exit_code"] != 0

def test_comspec_env_blocked():
    # Attempting to use %COMSPEC% environment variable substitution is blocked under shell=False
    res = run_validation_step("python -c \"import sys; print(sys.argv)\" %COMSPEC%")
    assert "%COMSPEC%" in res.get("stdout_excerpt", "") or "%COMSPEC%" in res.get("stderr_excerpt", "") or res["exit_code"] != 0

def test_powershell_chaining_blocked():
    res = run_validation_step("python -c \"print('first')\" & python -c \"print('second')\"")
    assert "second" not in res.get("stdout_excerpt", "")

def test_script_extensions_blocked():
    # .cmd extension blocked
    res_cmd = run_validation_step("test.cmd")
    assert res_cmd["ok"] is False
    assert "Security Policy Violation" in res_cmd["stderr_excerpt"]

    # .bat extension blocked
    res_bat = run_validation_step("test.bat")
    assert res_bat["ok"] is False
    assert "Security Policy Violation" in res_bat["stderr_excerpt"]

    # .ps1 extension blocked
    res_ps1 = run_validation_step("test.ps1")
    assert res_ps1["ok"] is False
    assert "Security Policy Violation" in res_ps1["stderr_excerpt"]

def test_windows_parsing_and_suffix_bypasses():
    # 1. Trailing dot bypasses blocked
    res_cmd_dot = run_validation_step("test.cmd.")
    assert res_cmd_dot["ok"] is False
    assert "Security Policy Violation" in res_cmd_dot["stderr_excerpt"]

    res_bat_dot = run_validation_step("test.bat.")
    assert res_bat_dot["ok"] is False
    assert "Security Policy Violation" in res_bat_dot["stderr_excerpt"]

    # 2. Trailing space bypasses blocked
    res_bat_space = run_validation_step("test.bat ")
    assert res_bat_space["ok"] is False
    assert "Security Policy Violation" in res_bat_space["stderr_excerpt"]

    res_ps1_space = run_validation_step("test.ps1 ")
    assert res_ps1_space["ok"] is False
    assert "Security Policy Violation" in res_ps1_space["stderr_excerpt"]

    # 3. Windows path parsing (backslashes preserved)
    # We test that we can parse a command with backslashes correctly.
    # Note: run_validation_step will fail execution if the binary doesn't exist, but it should NOT fail with "empty validation command".
    # And it should not strip backslashes on Windows.
    # Let's inspect the parsed command arguments by mocking/asserting behavior or executing python -c
    import sys
    import os
    python_exe = sys.executable
    # Backslash path to python exe should work under Windows
    cmd = f'"{python_exe}" -c "import sys; print(sys.argv)" "arg\\with\\backslashes" "arg with spaces"'
    res = run_validation_step(cmd)
    assert res["ok"] is True
    # Verify that backslashes and spaces in arguments are preserved in output
    assert "arg\\\\with\\\\backslashes" in res["stdout_excerpt"]
    assert "arg with spaces" in res["stdout_excerpt"]
