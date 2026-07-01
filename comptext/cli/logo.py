import sys
import argparse
from comptext.terminal.renderer import render_logo, render_image

def run_logo(logo_args: list[str]) -> None:
    """Run the logo command, displaying either the static logo or a custom image via chafa."""
    parser = argparse.ArgumentParser(description="CompText Logo Tool")
    parser.add_argument(
        "--image",
        help="Path to a custom image to render via chafa."
    )
    parser.add_argument(
        "--size",
        type=int,
        default=78,
        help="Width size in columns for chafa rendering."
    )
    parser.add_argument(
        "--symbols",
        default="braille",
        help="Symbols for chafa (e.g. braille, ascii, block)."
    )
    parser.add_argument(
        "--colors",
        default="full",
        help="Color depth for chafa (e.g. full, 16, 256, none)."
    )

    args = parser.parse_args(logo_args)

    if args.image:
        render_image(
            image_path=args.image,
            size=args.size,
            symbols=args.symbols,
            colors=args.colors
        )
    else:
        render_logo()
