#!/usr/bin/env python

import time
import pygame
import pygame.locals as pyl

class Interface(object):
    def __init__(self, provider, mode=(800, 600)):
        self._extents = mode
        self._surf = pygame.display.set_mode(mode)
        self._provider = provider
        self._start_time = 0
        self._stop_time = 0
        self._curr = None
        self._curr_hash = None
        self._curr_start = None
        self._running = False
        self._ended = False
        self._image_times = {}
        self._images_correct = {}
        self._text('Press spacebar to begin (and ESC to end early)')

    def verbose(self, msg, *args):
        self._provider.verbose(msg, *args)

    def _text(self, text, at=None):
        font = pygame.font.Font(pygame.font.match_font('Helvetica'), 24)
        surf = font.render(text, False, (255,255,255))
        self._draw_surf(surf, at=at)

    text = _text

    def _draw(self, path):
        surf = pygame.image.load(path)
        w, h = surf.get_width(), surf.get_height()
        if w > self._extents[0] or h > self._extents[1]:
            surf = self._scale_surface(surf)
        self._draw_surf(surf)

    def _draw_surf(self, surf, at=None):
        if at is None:
            w, h = surf.get_width(), surf.get_height()
            left = (self._extents[0] - w) / 2
            top = (self._extents[1] - h) / 2
        else:
            left, top = at
        self._surf.fill((0, 0, 0))
        self._surf.blit(surf, (left, top))
        pygame.display.flip()

    def _scale_surface(self, surf):
        w_ratio = surf.get_width() * 1.0 / self._extents[0]
        h_ratio = surf.get_height() * 1.0 / self._extents[1]
        new_w = int(surf.get_width() / max(w_ratio, h_ratio))
        new_h = int(surf.get_height() / max(w_ratio, h_ratio))
        return pygame.transform.scale(surf, (new_w, new_h))

    def running(self):
        return self._running
    
    def ended(self):
        return self._ended

    def elapsed(self):
        if self._stop_time == 0:
            return time.time() - self._start_time
        return self._stop_time - self._start_time

    def start(self):
        self._running = True
        self._provider.restart()
        self._start_time = time.time()
        self._curr = self._provider.next()
        self._curr_hash = self._provider.hash(self._curr)
        self._curr_start = time.time()
        self._draw(self._curr)

    def end(self):
        now = time.time()
        if self._curr is not None:
            self._image_times[self._curr_hash] = now - self._curr_start
        self._running = False
        self._ended = True
        self._curr = None
        self._curr_hash = None
        self._curr_start = None
        self._stop_time = now

    def get_dir(self):
        return "left" if "left" in self._curr else "right"

    def do_guess(self, direction):
        self._image_times[self._curr_hash] = time.time() - self._curr_start
        correct = self.get_dir() == direction
        if correct:
            print("Correct!")
        else:
            print("Wrong! It's a %s image" % (self.get_dir(),))
        self._images_correct[self._curr_hash] = correct
        try:
            self._curr = self._provider.next()
            self._curr_hash = self._provider.hash(self._curr)
            self._curr_start = time.time()
            self._image_times[self._curr_hash] = 0
            self._draw(self._curr)
        except StopIteration as _:
            self.end()

    def _on_key_event(self, key):
        if key == pyl.K_ESCAPE:
            self.end()
        elif key == pyl.K_SPACE and not self.running():
            self.start()
        else:
            dir = None
            if key == pyl.K_LEFT:
                dir = "left"
            elif key == pyl.K_RIGHT:
                dir = "right"
            if dir is not None:
                self.do_guess(dir)

    def on_event(self, event):
        if event.type == pyl.QUIT:
            self.end()
        elif event.type == pyl.KEYDOWN:
            self._on_key_event(event.key)

    def get_results(self):
        count = self._provider.count()
        results = {}
        for img in self._images_correct:
            results[img] = (self._image_times[img], self._images_correct[img])
        return results

