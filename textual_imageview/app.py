from argparse import ArgumentParser
from pathlib import Path
from typing import Union

from PIL import Image
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header

from textual_imageview.__about__ import __version__
from textual_imageview.viewer import ImageViewer


class ImageViewerApp(App):
    """Sample Textual app that uses the ImageViewer widget to view images. This app
    also includes keyboard suppport for translating and scaling the image."""

    TITLE = "vimg"

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", priority=True),
        # Movement
        Binding("w,up", "move(0, 1)", "Up", show=True, key_display="W/↑"),
        Binding("s,down", "move(0, -1)", "Down", show=True, key_display="S/↓"),
        Binding("a,left", "move(1, 0)", "Left", show=True, key_display="A/←"),
        Binding("d,right", "move(-1, 0)", "Right", show=True, key_display="D/→"),
        Binding("q,=", "zoom(-1)", "Zoom In", show=True, key_display="Q/+"),
        Binding("e,-", "zoom(1)", "Zoom Out", show=True, key_display="E/-"),
        # Faster movement
        Binding("W,shift+up", "move(0, 3)", "Fast Up", show=False),
        Binding("S,shift+down", "move(0, -3)", "Fast Dowm", show=False),
        Binding("A,shift+left", "move(3, 0)", "Fast Left", show=False),
        Binding("D,shift+right", "move(-3, 0)", "Fast Right", show=False),
        Binding("E,+", "zoom(-2)", "Fast Zoom In", show=False),
        Binding("Q,_", "zoom(2)", "Fast Zoom Out", show=False),
    ]

    def __init__(self, image_path: Union[str, Path]):
        """Inits vimg

        Args:
            image_path (Path or str): Path of image to view.
        """
        super().__init__()
        image_path = Path(image_path)
        if not image_path.exists():
            print(f"{image_path} does not exist.")
            exit()

        self.sub_title = image_path.name
        self.image = Image.open(image_path)
        self.image_viewer = ImageViewer(self.image)

    def action_move(self, delta_x: int, delta_y: int):
        self.image_viewer.image.move(delta_x, delta_y)
        self.image_viewer.refresh()
        self.refresh()

    def action_zoom(self, delta: int):
        self.image_viewer.image.zoom(delta)
        self.image_viewer.refresh()
        self.refresh()

    def compose(self) -> ComposeResult:
        yield Header()
        yield self.image_viewer
        yield Footer()


def vimg():
    """CLI entry point"""
    parser = ArgumentParser(description="A simple terminal-based image viewer.")
    parser.add_argument("image_path", help="Path of image to view.")
    parser.add_argument(
        "-v",
        "--version",
        help="Show version information.",
        action="version",
        version=__version__,
    )

    args = parser.parse_args()

    app = ImageViewerApp(args.image_path)
    app.run()
