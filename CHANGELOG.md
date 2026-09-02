## v2.0.0rc0 (2026-09-02)

### BREAKING CHANGE

- Colour is now Color rather than a subclass of it, and the
named-colour accessors HSL, RGB and HEX are NAMED_HSL, NAMED_RGB and
NAMED_HEX. The old accessor names still work and warn. Version 2.0.0.

### Feat

- read a98-rgb and rec2020, and let in_srgb_gamut answer for them
- read CSS color(), for the spaces that need no new constants
- read CSS color-mix()
- say what an unrecognised colour was probably meant to be
- say what a CSS system colour is instead of reporting a typo
- add the hue, saturation, color and luminosity blend modes
- add the soft-light, color-dodge and color-burn blend modes
- read CSS percentages on chroma and the a/b axes
- make Colour the same class as Color, and rename the accessors
- add Color.equals, and say what == costs
- measure how far apart two colours are, and name the nearest
- composite a colour onto another, with the CSS blend modes
- show a colour as a colour, and answer light or dark
- read and write the colour syntax CSS uses
- adjust and mix colours, with the step readable either way
- answer whether two colours are readable together, and pick the text
- add relative luminance and contrast ratio, and say what luminance is
- say whether a colour is one sRGB can show, before it gets clipped
- interpolate colour scales in Oklab
- add XYZ, LAB, LCH, CMYK and YUV colour spaces
- implement HSV
- add a ColorError hierarchy for bad colour values

### Fix

- stop the tests asserting the interpreter, and repin two actions
- pick the same colour for the same value in every process
- say what the trailing keywords do, and stop them writing the slots
- interpolate alpha across a scale, and land linspace on its endpoint
- keep the alpha of a colour built from another colour
- identify RGBA and HSLA sequences again, keeping the alpha they carry
- say which package provides tkinter when preview cannot import it
- say which package provides tkinter when preview cannot import it
- make Color satisfy the equality and hashing protocols
- tolerate FLOAT_ERROR at colour range boundaries
- return floats from every public output

### Refactor

- dispatch the constructor's colour inputs from a table
- type colour formats with NamedTuple and Protocol

### Perf

- stop scaling normalized components through 0-255 and back
- memoize conversions with a bounded LRU cache

## v1.0.0 (2025-11-29)

## v0.4.1 (2025-04-10)

## v0.4.0 (2025-03-22)

## v0.3.1 (2025-03-02)

## v0.3.0 (2025-03-02)

## v0.2.3 (2025-02-26)

## v0.2.2 (2025-02-25)

## v0.2.1 (2025-02-13)

## v0.2.0 (2025-02-11)

## v0.1.0 (2025-02-10)
