#!/usr/bin/env python3
import numpy as np
import math
from latqcdtools.plotting import *
from latqcdtools.readin import *
import matplotlib.pyplot as plt
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('filename')
parser.add_argument('--nt', '-nt', type = int, dest = "nt", default = -1)
parser.add_argument('--nbins', '-nbins', type = int, dest = "nbins", default = None)
parser.add_argument('--title', dest = "title", default = None)
parser.add_argument('--col', '-col', type = int, dest = "col", default = 2)
parser.add_argument('--logx', action = 'store_true')
parser.add_argument('--out-name', dest = 'out_name', default = 'hist.pdf')
parser.add_argument('--show-plot', dest = 'show_plot', action = 'store_true')
args = parser.parse_args()


if args.nt != -1:
    xdata, data, nconfs = read_in_pure(args.filename, 1, args.col, symmetrize = False)
    nt = args.nt
    index = list(xdata).index(nt)
    data = data[index]
else:
    data = np.loadtxt(args.filename)
    try:
        data[0][0]
        data = data.transpose()[args.col - 1]
    except (ValueError, IndexError):
        pass

latexify()
plot_hist(data, args.logx, args.nbins)

set_params(title = args.title)

plt.savefig(args.out_name)

if args.show_plot:
    plt.show()


