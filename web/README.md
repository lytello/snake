# Snake on the web

Two ways to run Snake in a browser. The original desktop game lives in
[`../snake.py`](../snake.py).

## Option A — `canvas/` (HTML5 canvas reimplementation)

A from-scratch port of the game in vanilla JavaScript on an HTML5 canvas.
No dependencies, no build step — it's a single self-contained file.

```bash
open web/canvas/index.html        # or just double-click it
```

Faithful to the pygame original: edge-wrapping, neon color pairs that cycle
every 5 points, particle bursts on eat, circular segments with eyes, and the
animated title screen. Adds WASD keys and touch swipe controls.

This is the version embedded on [lawrencetello.com](https://lawrencetello.com).

**Best for:** dropping the game onto a website. Tiny, instant load, mobile-friendly.

## Option B — `pygame/` (real Python, compiled to WebAssembly)

The actual pygame game running in the browser via
[pygbag](https://github.com/pygame-web/pygbag), which packages CPython + pygame
to WebAssembly. `pygame/main.py` is the same game as `snake.py`, restructured
into a single async loop (a pygbag requirement).

```bash
pip install pygbag
cd web/pygame
pygbag .                          # dev server at http://localhost:8000
```

To produce a static build to host anywhere:

```bash
cd web/pygame
pygbag --build .                  # output lands in build/web/
```

**Best for:** running the genuine Python code in-browser. Heavier — visitors
download a multi-MB Python runtime — and touch controls are limited, but it's
the real thing.
