# colourings
[![PyPI - Version](https://img.shields.io/pypi/v/colourings)](https://pypi.org/project/colourings/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/colourings)
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/colourings?period=total&units=INTERNATIONAL_SYSTEM&left_color=GREY&right_color=BRIGHTGREEN&left_text=downloads)](https://pepy.tech/projects/colourings)
[![codecov](https://codecov.io/github/Stoops-ML/colourings/graph/badge.svg?token=NQUPC3NY6S)](https://codecov.io/github/Stoops-ML/colourings)
[![Documentation](https://img.shields.io/readthedocs/colourings)](https://colourings.readthedocs.io/en/latest/)

A lightweight Python library for creating, converting, comparing and interpolating colours. No runtime dependencies, typed throughout.

**📖 [Read the documentation](https://colourings.readthedocs.io/en/latest/)**

This project is a modernized fork of [vaab/colour](https://github.com/vaab/colour/) with additional formats, typing, revised channel ranges, and updated packaging.

## Install

```bash
pip install colourings
```

## A taste

```python
from colourings import Color

c = Color("#3d7ab8")

c.hsl                      # HSL(hue=210.24..., saturation=50.20..., lightness=48.03...)
c.oklch                    # OKLCH(lightness=0.5677..., chroma=0.1153..., hue=250.8861...)
c.mix("white", 0.3).hex_l  # '#78a2cf'
c.contrast_ratio("white")  # 4.4925...
c.best_text_color()        # <Color black>
c.nearest_name()           # 'steelblue'
```

## What it does

| | | |
| --- | --- | --- |
| **15 formats** | `rgb` `hsl` `hsv` `hex` `web` `xyz` `lab` `lch` `oklab` `oklch` `cmyk` `yuv` and alpha variants, each readable and writable | [Creating colours](https://colourings.readthedocs.io/en/latest/colors.html) |
| **CSS Color 4 & 5** | `rgb()` `hsl()` `lab()` `lch()` `oklab()` `oklch()`, `color-mix()`, `color()` with `display-p3` / `a98-rgb` / `rec2020`, plus `to_css()` output | [CSS syntax](https://colourings.readthedocs.io/en/latest/css.html) |
| **Gradients** | `range_to` and `color_scale`, interpolating in `hsl` `lab` `lch` `oklab` `oklch`, either way round the hue circle, alpha included | [Gradients](https://colourings.readthedocs.io/en/latest/gradients.html) |
| **Adjustment** | `lighten` `darken` `saturate` `desaturate` with absolute or relative steps, `grayscale` `invert` `rotate_hue` `mix`, and the hue harmonies | [Adjusting](https://colourings.readthedocs.io/en/latest/adjusting.html) |
| **WCAG contrast** | `contrast_ratio` `relative_luminance` `is_readable` `best_text_color` `is_dark` | [Contrast](https://colourings.readthedocs.io/en/latest/contrast.html) |
| **Perceptual distance** | `delta_e` over CIE76, CIE94, CIEDE2000 and Oklab, and `nearest_name` | [Difference](https://colourings.readthedocs.io/en/latest/difference.html) |
| **Compositing** | `over` and `blend` through all sixteen CSS blend modes, encoded or linear | [Compositing](https://colourings.readthedocs.io/en/latest/compositing.html) |
| **Gamut checking** | `in_srgb_gamut`, to ask before a value gets clipped | [Ranges and gamut](https://colourings.readthedocs.io/en/latest/ranges.html) |
| **Stable picking** | `pick_for`, mapping any object to the same colour in every process | [Equality and picking](https://colourings.readthedocs.io/en/latest/equality.html) |

## The one thing worth knowing up front

A `Color` holds sRGB. `lab`, `lch`, `oklab`, `oklch`, `xyz` and `yuv` can each name a colour that sRGB cannot show, and such a value is **clipped** on the way in — quietly, and often. Afterwards it is indistinguishable from a colour that always fitted, so ask first:

```python
from colourings import in_srgb_gamut

in_srgb_gamut((53.2408, 80.0925, 67.2032), "lab")  # True, this is red
in_srgb_gamut((100, 120, -120), "lab")             # False, would be clipped
```

[Ranges and the sRGB gamut](https://colourings.readthedocs.io/en/latest/ranges.html) covers this properly, and it is the page to read before choosing a space to work in.

## Correctness

Most of this library is arithmetic on published constants, and a wrong constant there does not raise — it returns a plausible colour that is simply wrong. So every constant is either quoted from a citable source or derived in exact arithmetic, and anything whose constants could not be confirmed raises instead of guessing.

CIEDE2000 is checked against all 34 pairs of the published Sharma–Wu–Dalal test data. The CSS wide-gamut matrices are each derived twice, independently. Coverage is 100% of statements and branches, and every example in the README and the docs is executed by the test suite with its claimed output checked.

## Contributing

Bug reports, colour-science corrections and pull requests are welcome. [CONTRIBUTING.md](CONTRIBUTING.md) describes the checks CI runs, all of which you can run locally, and what a change needs before it can be merged.

## Security

To report a vulnerability, use [GitHub's private reporting](https://github.com/Stoops-ML/colourings/security/advisories/new) rather than a public issue. [SECURITY.md](SECURITY.md) sets out what is in scope — the short version is that `colourings` performs no I/O, opens no network connections and has no runtime dependencies, which leaves crafted inputs and the release process itself.

## License

BSD-3-Clause. See [LICENSE](LICENSE).