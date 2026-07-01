import os
import shutil
import subprocess
import sys
from pathlib import Path

def get_logo_path() -> Path:
    """Find the path to the static ANSI logo file."""
    # 1. Try relative to current working directory
    cwd_path = Path("assets/comptext-logo-braille-color.ans")
    if cwd_path.exists():
        return cwd_path
        
    # 2. Try relative to the package directory
    pkg_path = Path(__file__).parent.parent.parent / "assets" / "comptext-logo-braille-color.ans"
    if pkg_path.exists():
        return pkg_path
        
    return None

def render_logo() -> None:
    """Render the static ANSI logo, falling back to plain text if not found."""
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
        
    logo_path = get_logo_path()
    if logo_path:
        try:
            logo_text = logo_path.read_text(encoding="utf-8", errors="ignore")
            print(logo_text)
            return
        except Exception:
            pass
            
    print("\nCOMPTEXT — THE OPERATING SYSTEM FOR CONTEXT\n")

def render_image(image_path: str, size: int = 78, symbols: str = "braille", colors: str = "full") -> None:
    """Render an image to the terminal using chafa if available, otherwise degrade gracefully."""
    chafa_path = shutil.which("chafa")
    if chafa_path:
        cmd = [chafa_path]
        if size:
            cmd.extend(["--size", f"{size}"])
        if symbols:
            cmd.extend(["--symbols", symbols])
        if colors:
            cmd.extend(["--colors", colors])
        cmd.append(str(image_path))
        
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(res.stdout)
            return
        except Exception:
            pass
            
    # Fallback to static logo or text
    render_logo()
