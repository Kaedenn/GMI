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
import csv
import datetime
import json
import os

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

    def items(self):
        return self._data['guess_log'][:]

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

    def accuracy_of(self, type=None, side=None, **filters):
        items = self.count_of(type, side, **filters)
        num = self.count_of(type, side, correct=True, **filters)
        if items == 0:
            return float('nan')
        return num * 1.0 / items

def save_results(path, results):
    f = open(path, 'a')
    json.dump(results, f)
    f.write("\n")

def each_run_analysis(path):
    for line in open(path):
        l = line.strip()
        if len(l) == 0 or l[0] == '#':
            continue
        yield RunAnalysis(l)

def analyze(path):
    for ra in each_run_analysis(path):
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

def write_csv(path, dest, append=False):
    fobj = open(dest, 'a' if append else 'w')
    def ts(type_side, **kwargs):
        """Helper function to make ra_to_row simpler:
            type_side:
                'H' -> 'hands', 'F' -> 'feet'
                'L' -> 'left', 'R' -> 'right'
                'C' -> correct=True"""
        tch = 'h' if 'h' in type_side.lower() else 'f'
        sch = 'l' if 'l' in type_side.lower() else 'r'
        if 'c' in type_side.lower():
            kwargs['correct'] = True
        kwargs['type'] = {'h': 'hands', 'f': 'feet'}[tch]
        kwargs['side'] = {'l': 'left', 'r': 'right'}[sch]
        return kwargs

    def ra_to_row(ra):
        """
        Notation:
            H -> Hands, F -> Feet, L -> Left, R -> Right, C -> Correct

        [timestamp as "Day Mon Year Hour:Min:Sec",
         pain_level as int 0 - 10,
         'hands' or 'feet' or 'hands feet',
         test_length as seconds,
         test_count as int,
         correct as int,
         count_HL as int,
         count_HR as int,
         count_FL as int,
         count_FR as int,
         count_HLC as int,
         count_HRC as int,
         count_FLC as int,
         count_FRC as int,
         total_time_HL as seconds,
         total_time_HR as seconds,
         total_time_FL as seconds,
         total_time_FR as seconds,
         total_time_HLC as seconds,
         total_time_HRC as seconds,
         total_time_FLC as seconds,
         total_time_FRC as seconds]
        """
        row = [ts2dt(ra.start()).strftime(TIME_FMT),
                ra.pain_level(),
                ra.kinds(),
                sum(ra.values_of('guess_time')),
                ra.count(), ra.correct()]
        for correct in ('', 'c'):
            for type in 'HF':
                for side in 'LR':
                    args = ts("%s%s%s" % (type, side, correct))
                    row.append(ra.count_of(**args))
        for correct in ('', 'c'):
            for type in 'HF':
                for side in 'LR':
                    args = ts("%s%s%s" % (type, side, correct))
                    row.append(sum(ra.values_of('guess_time', **args)))
        return row

    w = csv.writer(fobj)
    headers = ['timestamp', 'pain_level', 'kinds', 'duration', 'count',
                'correct']
    for what in 'count correct time correct_time'.split():
        for type in 'hands feet'.split():
            for side in 'left right'.split():
                headers.append("%s_%s_%s" % (what, type, side))

    if not append:
        w.writerow(headers)

    for ra in each_run_analysis(path):
        w.writerow(ra_to_row(ra))

def write_detailed_csv(path, dest):
    headers = ['timestamp', 'image_id', 'image', 'type', 'side', 'time',
               'correct', 'guess', 'guess_time']
    dirname, filename = os.path.split(dest)
    for i,ra in enumerate(each_run_analysis(path)):
        fobj = open(os.path.join(dirname, "%d_%s" % (i+1, filename)), 'w')
        w = csv.writer(fobj)
        w.writerow(headers)
        for item in ra.items():
            row = [ts2dt(ra.start()).strftime(TIME_FMT),
                    item['image_id'], item['image'], item['type'],
                    item['side'], item['time'], item['correct'],
                    item['guess'], item['guess_time']]
            w.writerow(row)

if __name__ == "__main__":
    p = argparse.ArgumentParser(usage="%(prog)s [options] <file>")
    p.add_argument("file", type=str, help="file to analyze")
    p.add_argument("--csv", type=str, metavar="FILE",
                   help="write summary CSV to <FILE>")
    p.add_argument("-a", "--append", action="store_true",
                   help="append to CSV file; do not overwrite")
    p.add_argument("--detailed-csv", type=str, metavar="FILE",
                   help="write each test to N_<FILE>, N = 1, 2, 3, ...")
    args = p.parse_args()
    analyze(args.file)
    if args.csv:
        write_csv(args.file, args.csv, append=args.append)
    if args.detailed_csv:
        write_detailed_csv(args.file, args.detailed_csv)


