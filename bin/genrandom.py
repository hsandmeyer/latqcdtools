#!/usr/bin/env python3

from random import uniform
import sys

numb = 1000
min = 0
max = 1

for i, arg in enumerate(sys.argv):
    if arg == "-n":
        numb = int(sys.argv[i + 1])
    if arg == "-min":
        min = int(sys.argv[i + 1])
    if arg == "-max":
        max = int(sys.argv[i + 1])
    if arg == "-h":
        print("Usage:", sys.argv[0], "-m mean -s standard_deviation -n output_number")
        sys.exit(-1)

for i in range(0, numb):
    print(uniform(min, max))
