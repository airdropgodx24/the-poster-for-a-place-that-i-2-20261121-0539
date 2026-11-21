# AURHAVEN — The Poster for a Place That Isn't There

A travel poster for AURHAVEN, a cliffside town that does not exist: lantern-lit
white stairways wind down violet cliffs to a teal lagoon, where glass-sail
boats drift under the amber beam of a tall lighthouse at golden dusk.

The tagline says it plainly: WHERE THE LIGHT NEVER SETS.

## How it works

`main.py` draws the whole poster procedurally with the Python standard
library only. There are no image files, no fonts on disk, no network calls:

- the sky, sun, clouds, cliffs, lighthouse, lagoon and boats are all drawn
  pixel by pixel into an in-memory RGB canvas;
- the place name and tagline use a small built-in 5x7 bitmap font, scaled up
  and drawn with a dark shadow so the letters stay legible against the sky;
- the PNG is written by hand with `zlib` and `struct` (filter type 0,
  truecolour, 8-bit).

The output is deterministic: every run produces the exact same file.

## Run it

```sh
python3 main.py
```

It creates `/output` if needed and writes `/output/entry.png`
(1024x1024, well under the 1 MiB limit).
