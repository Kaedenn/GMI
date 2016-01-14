#!/usr/bin/env python

import json

def save_results(path, results):
    f = open(path, 'a')
    json.dump(results, f)
    f.write("\n")

def analyze(path):
    pass
