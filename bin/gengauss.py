#!/usr/bin/env python3
from random import normalvariate
import sys

mean = 1
standard_deviation = 1
numb = 1000

for i, arg in enumerate(sys.argv):
    if arg == "-n":
        numb = int(sys.argv[i + 1])
    if arg == "-m":
        mean = float(sys.argv[i + 1])
    if arg == "-s":
        standard_deviation = float(sys.argv[i + 1])
    if arg == "-h":
        print("Usage:", sys.argv[0], "-m mean -s standard_deviation -n output_number")
        sys.exit(-1)

for i in range(0, numb):
    print(normalvariate(mean, standard_deviation))
