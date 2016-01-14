#!/usr/bin/env python

import argparse
import csv
import hashlib
import os
import random
import sys
import time

import pyg
import analysis

import pygame
import pygame.locals as pyl

SELF_PATH = os.path.dirname(sys.argv[0])
ASSETS_PATH = os.path.join(SELF_PATH, "assets")
ASSETS_HANDS = os.path.join(ASSETS_PATH, "hands")
ASSETS_LHAND = os.path.join(ASSETS_HANDS, "left")
ASSETS_RHAND = os.path.join(ASSETS_HANDS, "right")
ASSETS_FEET = os.path.join(ASSETS_PATH, "feet")
ASSETS_LFOOT = os.path.join(ASSETS_FEET, "left")
ASSETS_RFOOT = os.path.join(ASSETS_FEET, "right")
ASSET_KINDS = ("hands", "feet")
ASSET_SIDES = ("left", "right")

def make_asset_dirs():
    for k in ASSET_KINDS:
        for s in ASSET_SIDES:
            d = os.path.join(ASSETS_PATH, k, s)
            if not os.path.exists(d):
                os.makedirs(d)

def image_kind(path):
    if os.path.commonprefix((ASSETS_HANDS, path)) == ASSETS_HANDS:
        return "hands"
    if os.path.commonprefix((ASSETS_FEET, path)) == ASSETS_FEET:
        return "feet"
    return None

def image_side(path):
    if '/left/' in path:
        return 'left'
    if '/right/' in path:
        return 'right'
    return None

def list_files(path):
    for item in os.listdir(path):
        yield os.path.join(path, item)

def rand_resize_list(seq, size):
    if len(seq) < size:
        while len(seq) < size:
            seq.append(random.choice(seq))
    elif len(seq) > size:
        while len(seq) > size:
            del seq[random.randrange(0, len(seq))]
    return seq

def hash_image(path):
    return hashlib.sha256(open(path).read()).hexdigest()[:8]

class GMITest(object):
    def __init__(self, pain_level, limit_to=None, equal_assets=True,
                 num_images=30, verbose=False):
        # verify arguments
        if not 0 <= pain_level <= 10:
            raise ValueError("Pain level must be in [0, 10]")
        if limit_to not in ('hands', 'feet', None):
            raise ValueError("limit_to must be 'hands', 'feet', or None")
        if num_images < 1:
            raise ValueError("num_images must be at least 1")

        # initialize members
        self._pain_level = pain_level
        self._test_items = ('hands', 'feet') if limit_to is None else (limit_to,)
        self._assets = {}
        self._num_images = num_images
        self._verbose = verbose
        self._working_assets = []
        self._seen = []
        self._unseen = []
        self._curr = None
        self._curr_time = None
        self._start_time = None
        self._done = False
        self._guess_log = []

        # initialize and prepare asset lists
        if 'hands' in self._test_items:
            self._assets['hands'] = {
                'left': list(list_files(ASSETS_LHAND)),
                'right': list(list_files(ASSETS_RHAND))
            }
        if 'feet' in self._test_items:
            self._assets['feet'] = {
                'left': list(list_files(ASSETS_LFOOT)),
                'right': list(list_files(ASSETS_RFOOT)),
            }

        # limit assets if desired
        if equal_assets:
            def each_asset_len(assets):
                for kind, lr in assets.items():
                    for side, l in lr.items():
                        yield len(l)
            minval = min(each_asset_len(self._assets))
            for kind, lr in self._assets.items():
                for side, seq in lr.items():
                    lr[side] = random.sample(seq, minval)

        for kind, lr in self._assets.items():
            for side, seq in lr.items():
                self._working_assets.extend(seq)

        rand_resize_list(self._working_assets, self._num_images)

        # prepare unseen list
        self.reset_seen()

        for kind in self._assets:
            for side in self._assets[kind]:
                self.verbose("%s %s %d", kind, side,
                             len(self._assets[kind][side]))
        self.verbose("unseen: %d", len(self._unseen))
        for item in self._unseen:
            self.verbose("unseen item: %s", item)

    def image_index(self):
        return len(self._seen)

    def image_count(self):
        return len(self._working_assets)

    def verbose(self, message, *args):
        if self._verbose:
            sys.stderr.write(message % args if args else message)
            sys.stderr.write('\n')

    def reset_seen(self):
        self._seen = list()
        self._unseen = list(self._working_assets)

    def seen_all(self):
        return len(self._unseen) == 0

    def done(self):
        return self._done

    def curr(self):
        return self._curr

    def next(self):
        if self.seen_all():
            self._done = True
            return
        idx = random.randrange(0, len(self._unseen))
        item = self._unseen[idx]
        del self._unseen[idx]
        self._seen.append(item)
        self._curr = item
        self._curr_time = time.time()
        self._guess_log.append({
            'image': self._curr,
            'image_id': hash_image(self._curr),
            'type': image_kind(self._curr),
            'side': image_side(self._curr),
            'time': self._curr_time,
            'correct': None,
            'guess': None,
            'guess_time': None,
        })
        if self._start_time is None:
            self._start_time = time.time()
        return item

    def do_guess(self, side):
        correct = image_side(self._curr) == side
        self._guess_log[-1]['guess'] = side
        self._guess_log[-1]['correct'] = correct
        self._guess_log[-1]['guess_time'] = time.time() - self._guess_log[-1]['time']
        self.next()
    
    def results(self):
        return {
            'pain_level': self._pain_level,
            'num_images': len(self._working_assets),
            'test_items': ' '.join(self._test_items),
            'start_time': self._start_time,
            'guess_log': self._guess_log
        }

def main():
    p = argparse.ArgumentParser(usage="%(prog)s [options]")
    p.add_argument("--size", type=str, metavar="W,H", default="800,600",
                   help="screen size of the form W,H (default: 800,600)")
    p.add_argument("--limit", choices=('hands', 'feet'), default=None,
                   help="limit to either 'hands' or 'feet' (default None)")
    p.add_argument("-o", "--out", type=str, metavar="PATH", default="log.txt",
                   help="file to record outputs to")
    p.add_argument("-c", "--count", type=int, metavar="NUM", default=30,
                   help="limit number of images to NUM (default 30)")
    p.add_argument("--analyze", type=str, metavar="FILE",
                   help="analyze FILE and exit")
    p.add_argument("-v", "--verbose", action="store_true",
                   help="be verbose about operations performed")

    args = p.parse_args()

    if args.analyze:
        analysis.analyze(args.analyze)
        raise SystemExit(0)

    w, h = args.size.split(',')
    g = pyg.PyGame(mode=(int(w), int(h)), verbose=args.verbose)

    # 1) obtain pain level
    g.data_set(u'')
    def on_keydown_step1(gobj, event):
        gobj.verbose("%s keydown: %s" % (gobj, event))
        gobj.verbose("%s", event.unicode in u'0123456789\n\r')
        if pyl.K_0 <= event.key <= pyl.K_9 or event.key == pyl.K_RETURN:
            gobj.data_set(g.data_get() + event.unicode)
    g.bind_on_event(pyl.KEYDOWN, on_keydown_step1)
    pain_level = None
    g.text("What is your current pain level (0-10)?\nPress Enter when done")
    while pain_level is None and g.active():
        g.run_once(render=True)
        text = g.data_get()
        if text.endswith(u'\r') or text.endswith('\n'):
            if not text.strip().isdigit() or not 0 <= int(text.strip()) <= 10:
                g.text("Please enter a number between 0 and 10 and press Enter")
                g.data_set(u'')
            else:
                pain_level = int(text.strip())
    g.unbind_on_event(pyl.KEYDOWN, on_keydown_step1)

    if not g.active():
        return

    # 2) prompt user to start
    g.text("""Your pain level is %d
If the image is of a left hand or foot, press A or Left
If the image is of a right hand or foot, press D or Right
Press space to start.""" % (pain_level,))
    g.data_set(None)
    def on_keydown_step2(gobj, event):
        gobj.data_set(True)
    g.bind_on_key(pyl.K_SPACE, on_keydown_step2)
    while g.data_get() is None and g.active():
        g.run_once(render=True)
    g.unbind_on_key(on_keydown_step2)

    if not g.active():
        return

    # 3) perform test
    test = GMITest(pain_level, limit_to='feet', verbose=args.verbose)
    test.next()
    g.data_set(test)
    def on_keydown_step3(gobj, event):
        if event.key == pyl.K_a or event.key == pyl.K_LEFT:
            gobj.data_get().do_guess("left")
        elif event.key == pyl.K_d or event.key == pyl.K_RIGHT:
            gobj.data_get().do_guess("right")
    g.bind_on_event(pyl.KEYDOWN, on_keydown_step3)
    while not test.done() and g.active():
        g.image(test.curr())
        g.text("Image %d of %d" % (test.image_index(), test.image_count()),
               at=(0, 0), size=12)
        g.run_once(render=True)
    results = test.results()
    g.verbose("Results: %s", results)

    # 4) finally, save results
    analysis.save_results(args.out, results)

if __name__ == "__main__":
    make_asset_dirs()
    main()

