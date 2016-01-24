#!/usr/bin/env python

import re
import sys

import pygame
import pygame.locals as pyl

# Console constants for printing in color
T_COLOR = '\033[%sm'
F_COLOR = lambda *v: T_COLOR % (';'.join(str(i) for i in v),)
TC_BOLD = 1
TC_RED = 31
TC_NONE = 0

# Color constants
C_WHITE = (255, 255, 255)
C_BLACK = (0, 0, 0)

def rgb_hex(hexstr):
    if len(hexstr) == 0 or hexstr[0] != '#':
        raise ValueError("Color '%r' must begin with a #" % (hexstr,))
    piece_len = (len(hexstr)-1) / 3
    hexcolor = hexstr[1:]
    red = hexcolor[0:piece_len]
    green = hexcolor[piece_len:piece_len*2]
    blue = hexcolor[piece_len*2:]
    return rgb(int(red, 16), int(green, 16), int(blue, 16))

def rgb(*args):
    if len(args) in (3, 4):
        return args[:3] # discard alpha
    if len(args) == 1:
        if isinstance(args[0], basestring):
            if len(args[0]) > 1 and args[0][0] == '#':
                return rgb_hex(args[0])
        else:
            try:
                return rgb_hex("#%06x" % (hex(args[0]),))
            except TypeError as e:
                pass
    raise ValueError("unable to parse %s as rgb" % (args,))

def _dict_pop(d, k, *args):
    if k not in d:
        if not args:
            raise KeyError("%s not in dict %s" % (k, d))
        else:
            return args[0]
    v = d[k]
    del d[k]
    return v

class PyGame(object):
    def __init__(self, mode=(800,600), text_color=C_WHITE, bg_color=C_BLACK,
                 verbose=False, fps=30):
        if not pygame.display.get_init():
            pygame.init()
            pygame.display.init()
            pygame.font.init()

        self._extents = mode
        self._surf = pygame.display.set_mode(mode)
        self._clock = pygame.time.Clock()
        self._text_color = text_color
        self._bg_color = bg_color
        self._fps = fps

        self._drawing = False
        self._active = True
        self._bindings = {None: []}
        self._verbose = verbose
        self._data = None

    def verbose(self, message, *args):
        if self._verbose:
            sys.stderr.write(message % args if args else message)
            sys.stderr.write("\n")

    def data_get(self):
        return self._data

    def data_set(self, d):
        self._data = d

    def width(self):
        return self._extents[0]
    
    def height(self):
        return self._extents[1]

    def active(self):
        return self._active

    __nonzero__ = active

    def deactivate(self):
        self._active = False

    def set_text_color(self, color):
        self._text_color = tuple(color[0], color[1], color[2])

    def set_bg_color(self, color):
        self._bg_color = tuple(color[0], color[1], color[2])

    def _scale_surface(self, surf):
        w_ratio = surf.get_width() * 1.0 / self._extents[0]
        h_ratio = surf.get_height() * 1.0 / self._extents[1]
        new_w = int(surf.get_width() / max(w_ratio, h_ratio))
        new_h = int(surf.get_height() / max(w_ratio, h_ratio))
        return pygame.transform.scale(surf, (new_w, new_h))

    def _center(self, w, h):
        "returns (x,y) for centering an object of w x h pixels"
        return (self.width() - w) / 2, (self.height() - h) / 2

    def _position(self, w, h, at):
        "returns at if it isn't None, otherwise self._center(w, h)"
        if at is not None:
            return at
        return self._center(w, h)

    def _render_begin(self):
        if not self.active():
            raise pygame.error("PyGame object is no longer active")
        self._surf.fill(self._bg_color)
        self._drawing = True

    def _render_end(self):
        if not self.active():
            raise pygame.error("PyGame object is no longer active")
        pygame.display.flip()
        self._drawing = False

    def render_begin(self):
        "Begins rendering if not currently drawing (called automatically)"
        if not self._drawing:
            self._render_begin()

    def render_end(self):
        "Ends rendering if currently drawing (called automatically)"
        if self._drawing:
            self._render_end()

    def text(self, text, at=None, font="Helvetica", size=24, **kwargs):
        """text(text, at=None, font="Helvetica", size=24)
        
        Render `text` with the given `font` and `size` (in points).

        text:       the text message to draw, allowing newlines
        at:         where to anchor the text (centered on-screen if None)
        font:       the font to use
        size:       the size to use in points

        Supported keyword arguments:

        antialias:  whether or not to antialias the font (default False)
        background: text background color (default is transparent)

        All other keyword arguments are then passed to self.draw_many
        """
        font = pygame.font.Font(pygame.font.match_font(font), size)
        lines = text.splitlines()
        aa = _dict_pop(kwargs, "antialias", False)
        bg = _dict_pop(kwargs, "background", None)
        if bg is None:
            surfaces = [font.render(t, aa, self._text_color) for t in lines]
        else:
            surfaces = [font.render(t, aa, self._text_color, bg) for t in lines]
        self.draw_many(surfaces, at=at, **kwargs)

    def image(self, path, at=None, **kwargs):
        surf = pygame.image.load(path)
        w, h = surf.get_width(), surf.get_height()
        if w > self.width() or h > self.height():
            surf = self._scale_surface(surf)
        self.draw(surf, at=at, **kwargs)

    def draw(self, surf, at=None, **kwargs):
        """draw(surf, at=None)

        Draws the surface at the position given (or centered on-screen
        otherwise)

        surf:   the surface to draw
        at:     a pair of coordinates stating where to draw the surface
        """
        self.render_begin()
        pos = self._position(surf.get_width(), surf.get_height(), at)
        self._surf.blit(surf, pos)
        if kwargs.get("render_now", False):
            self.render_end()

    def draw_many(self, surfs, at=None, align_center=True, **kwargs):
        """draw_many(surfaces, at=None, align_center=True, **kwargs)
        
        Draws each surface with the given padding, aligned according to the
        `align` param.

        surfs:      a list of surfaces to draw
        at:         a pair of coordinates to anchor the surfaces; surfaces are
                    centered if at=None
        align_center:   boolean, whether or not to center or left-justify text

        The following kwargs are supported:

        v_padding:  if present, specifies additional spacing in pixels between
                    subsequent surfaces, otherwise:
        v_spacing:  if present, specifies the distance between the top of one
                    surface to the top of the next surface, otherwise the
                    surfaces are drawn with no space between them
        """
        v_padding = _dict_pop(kwargs, "v_padding", None)
        v_spacing = _dict_pop(kwargs, "v_spacing", None)
        render_now = _dict_pop(kwargs, "render_now", False)
        width = max(s.get_width() for s in surfs)
        height = sum(s.get_height() for s in surfs)
        if v_padding is not None:
            height += v_padding * len(surfs)
        x, y = self._position(width, height, at)
        for surf in surfs:
            if align_center:
                x = (self.width() - surf.get_width()) / 2
            self.draw(surf, at=(x, y), **kwargs)
            if v_padding is not None:
                y += surf.get_height() + v_padding
            elif v_spacing is not None:
                y += v_spacing
            else:
                y += surf.get_height()
        if render_now:
            self.render_end()

    def get_keystate(self):
        "returns the state of all keys"
        return pygame.key.get_pressed()

    def get_keydown(self, key):
        "True if `key` is pressed"
        return self.get_keystate()[key]

    def get_events(self):
        "yields all un-processed events"
        if not self.active():
            raise pygame.error("PyGame object is no longer active")
        for event in pygame.event.get():
            yield event

    def bind_on_event(self, evt, func):
        """bind `func` to be called when event type `evt` is fired; the event
        will be passed two arguments: `self` and the event fired"""
        if evt not in self._bindings:
            self._bindings[evt] = []
        self._bindings[evt].append(func)

    def bind_on_key(self, key, func):
        "bind `func` to be called when `key` is pressed"
        def wrapper(event):
            if event.key == key:
                fn(self, event)
        self.bind_on_event(pyl.KEYDOWN, func)

    def unbind_on_event(self, evt, func):
        fnlist = self._bindings[evt]
        del fnlist[fnlist.index(func)]

    def unbind_on_key(self, func):
        fnlist = self._bindings[pyl.KEYDOWN]
        del fnlist[fnlist.index(func)]

    def bind_on_iterate(self, func):
        "bind `func` to be called each iteration of the main loop"
        self._bindings[None].append(func)

    def unbind_on_iterate(self, func):
        del self._bindings[None][self._bindings[None].index(func)]

    def run(self):
        "call to invoke the main loop until the program ends"
        while self.active():
            self.run_once()
            self._clock.tick(self._fps)

    def tick(self):
        "sleeps the program as long as necessary to ensure an FPS limit"
        self._clock.tick(self._fps)

    def run_once(self, render=False):
        "call to run one iteration of the main loop"
        for fn in self._bindings[None]:
            fn(self)
        for event in self.get_events():
            for fn in self._bindings.get(event.type, list()):
                fn(self, event)
            if event.type == pyl.QUIT:
                self.deactivate()
            elif event.type == pyl.KEYDOWN and self.get_keydown(pyl.K_ESCAPE):
                self.deactivate()
        if render and self.active():
            self.render_end()

if __name__ == "__main__":
    # for testing
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--mode", type=str, default="800,600",
                   help="window size; default is '800,600'")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args()

    w, h = args.mode.split(',')
    mode = (int(w), int(h))
    g = PyGame(mode=mode, verbose=args.verbose)
    g.text("Hi!\nPress ESC to close", render_now=True)
    g.run()

    g = PyGame(mode=mode, verbose=args.verbose)
    pressed = False
    def on_iter(pg):
        if not pressed:
            pg.render_begin()
            pg.text("This is some text!\nAnd some more!")
            pg.render_end()
    def on_key_evt(pg, evt):
        global pressed
        if not pressed:
            pg.unbind_on_iterate(on_iter)
        pressed = True
        pg.render_begin()
        pg.text("You pressed the %s key" % (evt.scancode,))
        pg.render_end()
    g.bind_on_iterate(on_iter)
    g.bind_on_event(pyl.KEYDOWN, on_key_evt)
    g.run()

