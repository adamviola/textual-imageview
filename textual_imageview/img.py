import math
from typing import Optional, Tuple

from PIL import Image
from rich.color import Color
from rich.console import Console, ConsoleOptions, RenderResult
from rich.segment import Segment
from rich.style import Style

Zoom = int


class ImageView:
    """Renders an image with zoom and padding.

    Args:
        image (Image.Image): PIL image to render.
        zoom (int): Zoom level. Must be non-negative. Zoom increase -> zoom out.
        origin_position (Tuple[int, int]): Image position (x,y) of the top-left corner
            of the container. Defaults to (0,0).
        container_size (Tuple[int, int], optional): Size of the container of the image
            (w,h). If None, nothing is rendered. Defaults to None.

    Notes:
        Throughout this class, "image position" refers to the coordinate frame with the
        origin at the top-left corner of the image, +x-axis pointed right, and +y-axis
        pointed down. The width of a single character is 1 unit along the x-axis. The
        height of a single character is 2 units along the y-axis.
    """

    ZOOM_RATE = 0.8

    def __init__(
        self,
        image: Image.Image,
        zoom: int = 0,
        origin_position: Tuple[int, int] = (0, 0),
        container_size: Optional[Tuple[int, int]] = None,
    ):
        self.images: dict[Zoom, Image.Image] = {}
        self.segment_cache: dict[Zoom, dict[Tuple[int, int], Segment]] = {}

        self.image = image
        self._container_size = container_size
        self._zoom = 0
        self.set_zoom(zoom)
        self.origin_position = origin_position

    def zoom(self, delta: int, zoom_position: Optional[Tuple[int, int]] = None):
        """Adjusts the zoom level of the image at the specified zoom image position. If
        no zoom position is specified, the center of the console is used.

        Args:
            zoom: Zoom delta. Postivie -> zoom out.
            zoom_position: Image-space position (x,y) to zoom into. Conceptually, the
                pixel at this image will not move no matter the zoom level.
        """
        self.set_zoom(self._zoom + delta, zoom_position=zoom_position)

    def set_zoom(self, zoom: int, zoom_position: Optional[Tuple[int, int]] = None):
        """Sets the zoom level of the image at the specified zoom image position. If
        no zoom position is specified, the center of the console is used.

        Args:
            zoom: Zoom level. Must be non-negative. Zoom increase -> zoom out.
            zoom_position: Image-space position (x,y) to zoom into. Conceptually, the
                pixel at this image will not move no matter the zoom level.
        """
        # Lower bound on zoom
        zoom = max(zoom, 0)

        # Upper bound on zoom
        if zoom > self._zoom and min(self.zoomed_size) <= 8:
            zoom = self._zoom

        if zoom not in self.images:
            multiplier = self.ZOOM_RATE**zoom
            w, h = self.image.size
            self.images[zoom] = self.image.resize(
                (round(w * multiplier), round(h * multiplier))
            )
            self.segment_cache[zoom] = {}

        if self._container_size is not None:
            w, h = self._container_size
            origin_x, origin_y = self.origin_position
            if zoom_position is None:
                zoom_position = origin_x + w // 2, origin_y + h
            old_zoom_x, old_zoom_y = zoom_position

            old_w, old_h = self.images[self._zoom].size
            new_w, new_h = self.images[zoom].size

            multiplier_x = new_w / old_w
            multiplier_y = new_h / old_h

            new_zoom_x = old_zoom_x * multiplier_x
            new_zoom_y = old_zoom_y * multiplier_y

            # Set zoom here because it's used in origin_position bounds checking
            self._zoom = zoom
            self.origin_position = (
                origin_x + round(new_zoom_x - old_zoom_x),
                origin_y + round(new_zoom_y - old_zoom_y),
            )

    def move(self, delta_x: int, delta_y: int):
        """Moves the image using the specified delta (x,y), where +x moves the image
        right, and +y moves the image down.

        Args:
            delta_x (int): Number of pixels to move the image along the x-axis.
            delta_y (int): Number of pixels to move the image along the x-axis. Note
                that the one character height is two pixels.
        """
        origin_x, origin_y = self.origin_position
        self.origin_position = (origin_x - delta_x, origin_y - delta_y)

    def set_container_size(self, width: int, height: int, maintain_center: bool = True):
        """Adjusts the render to reflect a change in container size, where height is the
        number of lines and width is the length of each line.

        Args:
            width (int): New width of the container of the image.
            height (int): New height of the container of the image.
            maintain_center (bool): If True, the pixels in the center of the console
                before the resize remain in the center of the console after the resize.
                If False, the image remains in the same position. Defaults to True.
        """

        if maintain_center and self._container_size is not None:
            old_w, old_h = self._container_size
            new_w, new_h = width, height

            origin_x, origin_y = self.origin_position

            if new_w != old_w:
                delta_w = new_w - old_w

                if delta_w % 2 == 0:
                    origin_x = origin_x - delta_w // 2
                else:
                    # If we're 1 by 1 resizing, this keeps things even
                    op = math.floor if new_w % 2 == 0 else math.ceil
                    origin_x = op(origin_x - delta_w / 2)

            if new_h != old_h:
                delta_h = new_h - old_h
                origin_y -= delta_h

            self.origin_position = (origin_x, origin_y)

        self._container_size = (width, height)

        # Keeps origin_position valid after container resize
        self.origin_position = self.origin_position

    def rowcol_to_xy(
        self, row: int, col: int, offset: Tuple[int, int]
    ) -> Tuple[int, int]:
        """Converts a character position (row,col) to an image position (x,y) given the
        offset (number of rows, number of columns) between the top-left of the terminal
        and top-left of the widget.

        Args:
            row (int): Row of the terminal (starting from the top at 0) to convert to an
                image y-value.
            col (int): Column of the terminal (starting from the left at 0) to convert
                to an image x-value.
            offset (Tuple[int, int]): Offset (number of rows, number of columns) between
                the top-left of the terminal and top-left of the widget.

        Returns:
            (x, y): Image position.
        """
        offset_row, offset_col = offset
        origin_x, origin_y = self.origin_position
        return origin_x + col - offset_col, origin_y + 2 * (row - offset_row)

    def xy_to_rowcol(self, x: int, y: int, offset: Tuple[int, int]) -> Tuple[int, int]:
        """Converts an image position (x,y) to a character position (row,col) given the
        offset (number of rows, number of columns) between the top-left of the terminal
        and top-left of the widget.

        Args:
            row (int): Row of the terminal (starting from the top at 0) to convert to an
                image y-value.
            col (int): Column of the terminal (starting from the left at 0) to convert
                to an image x-value.
            offset (Tuple[int, int]): Offset (number of rows, number of columns) between
                the top-left of the terminal and top-left of the widget.

        Returns:
            (row, col): Character position.
        """
        offset_row, offset_col = offset
        origin_x, origin_y = self.origin_position
        return (y - origin_y) // 2 + offset_row, x - origin_x + offset_col

    @property
    def origin_position(self) -> Tuple[int, int]:
        return self._origin_position

    @origin_position.setter
    def origin_position(self, value: Tuple[int, int]):
        origin_x, origin_y = value
        img_w, img_h = self.zoomed_size
        if self._container_size is not None:
            w, h = self._container_size[0], self._container_size[1] * 2
        else:
            w, h = 0, 0

        if origin_x <= -w + 1:
            origin_x = -w + 1

        if origin_x >= img_w - 1:
            origin_x = img_w - 1

        if origin_y <= -h + 1:
            origin_y = -h + 1

        if origin_y >= img_h - 1:
            origin_y = img_h - 1

        self._origin_position = origin_x, origin_y

    @property
    def size(self) -> Tuple[int, int]:
        """Size of the original image."""
        return self.image.size

    @property
    def zoomed_size(self) -> Tuple[int, int]:
        """Size of the image at the current zoom level."""
        return self.images[self._zoom].size

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        if self._container_size is None:
            return ""

        image = self.images[self._zoom]
        img_w, img_h = image.size
        w, h = self._container_size[0], self._container_size[1] * 2
        origin_x, origin_y = self.origin_position

        null_style = Style.null()
        newline = Segment("\n", null_style)

        segments = []
        for y in range(origin_y, min(origin_y + h, img_h), 2):
            # Skip lines with no image
            if y < -1:
                segments.append(newline)
                continue

            # Add padding to the left of the image
            if origin_x < 0:
                segments.append(Segment(" " * -origin_x, style=null_style))
                x_start = 0
            else:
                x_start = origin_x

            for x in range(x_start, min(x_start + w, img_w)):
                # Add segment for each pixel-pair of the image
                segments.append(self.get_segment(x, y))

            segments.append(newline)

        return segments

    def get_segment(self, x: int, y: int) -> Segment:
        """Computes the Segment (character + style) at a particular image position.
        Segments are cached because profiling suggested that the instantiation of Color
        and Style objects was taxing.

        Args:
            x (int): Image x-coordinate of returned segment.
            y (int): Image y-coordinate of returned segment. Note that the y-coordinate
                refers to the top half of the segment, as each character corresponds to
                two pixels.
        """
        position = (x, y)
        image = self.images[self._zoom]
        cache = self.segment_cache[self._zoom]
        _, img_h = image.size

        # Check if we've already computed the segment for this position
        if position not in cache:
            upper = None
            if y >= 0:
                pixel = image.getpixel(position)
                if not isinstance(pixel, tuple):
                    pixel = (pixel, pixel, pixel)
                upper = Color.from_rgb(*pixel[:3])

            lower = None
            if y < img_h - 1:
                pixel = image.getpixel((x, y + 1))
                if not isinstance(pixel, tuple):
                    pixel = (pixel, pixel, pixel)
                lower = Color.from_rgb(*pixel[:3])

            # Render each pixel as a half-height character
            if upper is None:
                segment = Segment("▄", Style(color=lower))
            else:
                segment = Segment("▀", Style(color=upper, bgcolor=lower))

            # Cache segment for next render
            cache[position] = segment

        return cache[position]
