# textual-imageview

[![PyPI - Version](https://img.shields.io/pypi/v/textual-imageview.svg)](https://pypi.org/project/textual-imageview)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/textual-imageview.svg)](https://pypi.org/project/textual-imageview)

![cat](https://user-images.githubusercontent.com/43352940/210931390-ad1f47fc-2340-435e-8851-234b5fa96d0f.gif)

`textual-imageview` is a both a CLI tool and Textual widget and for viewing images in the
terminal.

## Usage
Use the `vimg` CLI command to quickly view an image in the terminal.

```console
vimg <path_to_image>
```

Click and drag (or press W/S/A/D) to move around the image, and scroll (or press -/+) to zoom in/out of the image.

<details>
  <summary>Having trouble displaying colors when using `vimg` over SSH?</summary>
  
  It's likely that your `COLORTERM` environment variable is not properly set. 
</details>



`vimg` is built on `ImageView`, a Rich renderable that renders images with padding/zoom, and `ImageViewer`, a Textual widget that adds mouse interactivity to `ImageView`. Add `textual-imageview` as a dependency to use them in your Textual app!

At the highest zoom level, each character corresponds to two image pixels. I've found that `vimg` works best with a GPU-accelerated terminal like [Alacritty](https://github.com/alacritty/alacritty).

## Installation
```console
pip install textual-imageview
```

## FAQ

**`vimg` works great locally, but colors aren't displaying correctly when using `vimg` over SSH. Why?**

Rich [determines terminal color support](https://github.com/Textualize/rich/blob/7601290c3a2f574fa29763ed5a615767494f5013/rich/console.py#L796) by checking if the `COLORTERM` environment variable is set to `truecolor` or `24bit`.

If you know your terminal emulator supports truecolor - i.e., `vimg` works great locally - try setting the environment variable manually:
```console
export COLORTERM=truecolor
```

## License

`textual-imageview` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
