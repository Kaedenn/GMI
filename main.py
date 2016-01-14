#!/usr/bin/env python

"""
Program for graded motor imagery left/right discrimination treatment

http://www.gradedmotorimagery.com

This program is intended for use in graded motor imagery treatments focusing
on left/right discrimination for hands or feet. Images are stored in a local
./assets folder (configurable via --paths argument) with the following paths
built-in:
    ./assets/feet/left
    ./assets/feet/right

Assets are identified by path:
    ./assets/<object>/left/<image>
    ./assets/<object>/right/<image>

Both PNG and JPG image formats are supported. Other formats are supported if
pygame (http://pygame.org) understands the format.

Due to copyright reasons the individual images are not present; obtaining the
necessary images is done by the user of the program.

Every image is timed and response recorded, either correct or incorrect. The
number of images and presence of repeats are configurable.
"""

import argparse
import csv
import hashlib
import random
import os
import sys
import time

import pygame
import pygame.locals as pyl

from interface import Interface

pygame.init()
pygame.font.init()

SELF_PATH = os.path.dirname(sys.argv[0])
ASSETS_PATH = os.path.join(SELF_PATH, "assets")
ASSETS_HANDS = os.path.join(ASSETS_PATH, "hands")
ASSETS_LHAND = os.path.join(ASSETS_HANDS, "left")
ASSETS_RHAND = os.path.join(ASSETS_HANDS, "right")
ASSETS_FEET = os.path.join(ASSETS_PATH, "feet")
ASSETS_LFOOT = os.path.join(ASSETS_FEET, "left")
ASSETS_RFOOT = os.path.join(ASSETS_FEET, "right")
ASSET_DIRS = (ASSETS_LHAND, ASSETS_RHAND, ASSETS_LFOOT, ASSETS_RFOOT)

for dir in ASSET_DIRS:
    if not os.path.exists(dir):
        os.makedirs(dir)

def image_type(path):
    real = os.path.realpath(path)
    for typ in (ASSETS_HANDS, ASSETS_FEET):
        real_type = os.path.realpath(typ)
        if os.path.commonprefix((real_type, real)) == real_type:
            return os.path.basename(typ)
    return None

def _is_image(path):
    try:
        surf = pygame.image.load(path)
    except (IOError, pygame.error) as e:
        print("Not an image: %s" % (path,))
        return False
    if image_type(path) is None:
        print("Image %s type is unknown; may cause statistical problems!" % (
            path,))
    return True

def hash_str(s):
    return hashlib.sha256(s).hexdigest()[:8]

class ImageProvider(object):
    def __init__(self, assets_paths, count=None, repeats=False,
                 verbose=False):
        self._images = []
        self._repeats = repeats
        self._verbose_on = verbose
        self._seen = set()
        self._unseen = set()
        self._count = 0
        self._total = count
        for path in assets_paths:
            self._images.extend(self._load_images(path))
        if len(self._images) == 0:
            raise ValueError("No images found in paths %s" % (asset_paths,))
        hashes = tuple((f, hash_str(open(f).read())) for f in self._images)
        self._hashes = dict((f,h) for f,h in hashes)
        self._lookup = dict((h,f) for f,h in hashes)
        if len(self._hashes) != len(self._lookup):
            print("ERROR! Duplicate images detected!!")
            for i in self._hashes.keys():
                if i not in self._lookup.values():
                    print("%s duplicates %s!" % (self._lookup[self._hashes[i]], i))
        if self._verbose_on:
            for p in self._images:
                self.verbose("Image %s hash %s" % (p, self._hashes[p]))
        self.restart()

    def verbose(self, msg, *args):
        if self._verbose_on:
            m = msg % args if args else msg
            sys.stderr.write("%s\n" % (m,))

    def _load_images(self, path):
        results = []
        for f in os.listdir(path):
            fpath = os.path.join(path, f)
            if _is_image(fpath):
                results.append(fpath)
        self.verbose("Found %d image%s in %s", len(results),
                      '' if len(results) == 1 else 's', path)
        return results

    def count(self):
        return self._count

    def hash(self, image):
        return self._hashes[image]

    def lookup(self, hash):
        return self._lookup[hash]

    def restart(self):
        self._seen = set()
        self._unseen = set(self._images)
        self._count = 0

    def next(self):
        if self._total is not None and self._count >= self._total:
            raise StopIteration("displayed max number of images")
        if not self._repeats and len(self._unseen) == 0:
            raise StopIteration("No more images left, please call .restart()")
        img = random.choice(list(self._unseen))
        if not self._repeats:
            self._seen.add(img)
            self._unseen.remove(img)
            self.verbose("%s seen, %s unseen", len(self._seen),
                          len(self._unseen))
        self._count += 1
        if self._total is not None:
            self.verbose("Seen %d of %d total images; %2d%% done",
                         self._count, self._total,
                         self._count * 100 / self._total)
        return img

def do_analysis(args):
    batches = []
    for line in csv.reader(open(args.analyze)):
        if line[0] == 'Batch':
            batches.append({})
        else:
            pass

def do_key_event(interface, provider, started):
    finished = False
    keys = pygame.key.get_pressed()
    if keys[pyl.K_SPACE] and not interface.running():
        started = True
        interface.start()
    elif keys[pyl.K_LEFT] or keys[pyl.K_RIGHT]:
        if interface.running():
            d = key2dir(keys[pyl.K_LEFT], keys[pyl.K_RIGHT])
            if d is not None:
                interface.do_guess(d)
        elif started:
            finished = True
    return started, finished

def do_interactive(args):
    provider = ImageProvider(args.paths, count=args.count,
                             repeats=args.repeats, verbose=args.verbose)
    interface = Interface(provider)
    finished = False
    started = False

    """
    pain_level = None
    while pain_level is None:
        interface.text("What is your current pain level, between 0 and 10?")
        for event in pygame.event.get():
            if event.type == pyl.QUIT:
                raise SystemExit(0)
            elif event.type == pyl.KEYDOWN:
                pass

    print("Current pain level: %d" % (pain_level,))
    """

    while not finished:
        for event in pygame.event.get():
            interface.on_event(event)
        if interface.running():
            started = True
        elif started or interface.ended():
            finished = True

    log = [('Batch', time.time(), args.repeats, args.count, args.paths)]
    results = interface.get_results()
    for img,result in results.iteritems():
        sec, correct = result
        log.append((img, provider.lookup(img), correct, sec))
        print("Image %s %s in %s seconds" % (
            img, "correct" if correct else "incorrect", sec))

    if args.out is not None:
        writer = csv.writer(open(args.out, 'a'))
        writer.writerows(log)

def main():
    p = argparse.ArgumentParser(usage="%(prog)s [options]")
    p.add_argument("-p", "--paths", type=str, metavar="PATHS", nargs="*",
                   default=(ASSETS_LFOOT, ASSETS_RFOOT),
                   help="load images from PATHS (default: ./assets/*)")
    p.add_argument("-o", "--out", type=str, metavar="PATH", default=None,
                   help="file to record outputs to")
    p.add_argument("-c", "--count", type=int, metavar="NUM", default=30,
                   help="limit number of images to NUM (default 30)")
    p.add_argument("--repeats", action="store_true", help="allow repeats")
    p.add_argument("--analyze", type=str, metavar="FILE",
                   help="analyze FILE and exit")
    p.add_argument("-v", "--verbose", action="store_true",
                   help="be verbose about operations performed")

    args = p.parse_args()
    if args.analyze:
        do_analysis(args)
    else:
        do_interactive(args)

if __name__ == "__main__":
    main()

# TODO: swap out interface.py with pyg.py
# TODO: add proper "current pain level" prompt
