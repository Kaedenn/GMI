#!/usr/bin/env python

"""
Results analysis

Result structure:
    pain_level:     int from 0 to 10
    num_images:     length of working set, number of images shown
    test_items:     one or both of "hands" and "feet"
    start_time:     unix timestamp of when test started
    guess_log:      guess structure, see below

Guess structure:
    image:      path to image
    image_id:   hash of image
    type:       image's type: either 'hands' or 'feet'
    side:       image's direction: either 'left' or 'right'
    time:       time when image was presented
    correct:    boolean: if the guess was correct
    guess:      what the user guessed, either 'left' or 'right'
    guess_time: how long the user took, in seconds (with double precision)

"""

import argparse
import datetime
import json

TIME_FMT = "%d %b %Y %H:%M:%S"

def ts2dt(ts):
    return datetime.datetime.fromtimestamp(ts)

class RunAnalysis(object):
    def __init__(self, line=None):
        self._data = None
        if line is not None:
            self.load_from_str(line)

    def load_from_str(self, string):
        self._data = json.loads(string)

    def start(self):
        return self._data['start_time']

    def count(self):
        return self._data['num_images']

    def kinds(self):
        return self._data['test_items']

    def pain_level(self):
        return self._data['pain_level']

    def correct_items(self):
        return [i for i in self._data['guess_log'] if i['correct']]

    def correct(self):
        return len(self.correct_items())

    def values_of(self, log_key, **filters):
        items = self._data['guess_log']
        for k,v in filters.items():
            items = [i for i in items if i[k] == v]
        return [i[log_key] for i in items]

    def accuracy(self):
        return self.correct() * 1.0 / self.count()

    def count_of(self, type=None, side=None, **filters):
        items = self._data['guess_log']
        if type is not None:
            items = [i for i in items if i['type'] == type]
        if side is not None:
            items = [i for i in items if i['side'] == side]
        for k,v in filters.items():
            items = [i for i in items if i[k] == v]
        return len(items)

    def accuracy_of(self, type=None, side=None):
        items = self.count_of(type, side)
        num = self.count_of(type, side, correct=True)
        if items == 0:
            return float('nan')
        return num * 1.0 / items

def save_results(path, results):
    f = open(path, 'a')
    json.dump(results, f)
    f.write("\n")

def analyze(path):
    for line in open(path):
        l = line.strip()
        if len(l) == 0 or l[0] == '#':
            continue
        ra = RunAnalysis(l)
        start = ts2dt(ra.start())
        duration = sum(ra.values_of('guess_time'))
        n = ra.count()
        h = ra.count_of(type='hands')
        f = ra.count_of(type='feet')
        l = ra.count_of(side='left')
        r = ra.count_of(side='right')
        c = ra.correct()
        c_h = ra.count_of(type='hands', correct=True)
        c_f = ra.count_of(type='feet', correct=True)
        c_l = ra.count_of(side='left', correct=True)
        c_r = ra.count_of(side='right', correct=True)
        a_h = ra.accuracy_of(type='hands') * 100
        a_f = ra.accuracy_of(type='feet') * 100
        a_l = ra.accuracy_of(side='left') * 100
        a_r = ra.accuracy_of(side='right') * 100
        print("Run %s - %.03f seconds for %d images" % (
            start.strftime(TIME_FMT), duration, n))
        print("Pain level: %d" % (ra.pain_level(),))
        print("Total accuracy: %d/%d %.02f%%" % (c, n, ra.accuracy() * 100))
        print("Hand accuracy: %d/%d %.02f%%" % (c_h, h, a_h))
        print("Foot accuracy: %d/%d %.02f%%" % (c_f, f, a_f))
        print("Left accuracy: %d/%d %.02f%%" % (c_l, l, a_l))
        print("Right accuracy: %d/%d %.02f%%" % (c_r, r, a_r))
        print("Average time per image: %.02f seconds" % (duration/n,))

if __name__ == "__main__":
    p = argparse.ArgumentParser(usage="%(prog)s [options] <file>")
    p.add_argument("file", type=str, help="file to analyze")
    args = p.parse_args()
    analyze(args.file)


