#!/usr/bin/env python3
import numpy as np
import math
from latqcdtools.plotting import *
from latqcdtools.readin import *
import matplotlib.pyplot as plt
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('filename')
parser.add_argument('--title', dest = "title", default = None)
parser.add_argument('--xdata-col',type = int, dest = "xdata_col", default = 1)
parser.add_argument('--ydata-col', type = int, dest = "ydata_col", default = 2)

parser.add_argument('--xmin', type = float, dest = "xmin", default = None)
parser.add_argument('--ymin', type = float, dest = "ymin", default = None)

parser.add_argument('--xmax', type = float, dest = "xmax", default = None)
parser.add_argument('--ymax', type = float, dest = "ymax", default = None)

parser.add_argument('--label', dest = 'label', default = None)

parser.add_argument('--out-name', dest = 'out_name', default = 'cov.pdf')
parser.add_argument('--show-plot', dest = 'show_plot', action = 'store_true')
args = parser.parse_args()


xdata, data, nconfs = read_in_pure(args.filename, args.xdata_col, args.ydata_col, symmetrize = False)

cov = calc_cov(data)

latexify()
plot_cov(cov, xrange = xdata, yrange = xdata, xmin = args.xmin, xmax = args.xmax,
        ymin = args.ymin, ymax = args.ymax, xlabel = args.label, ylabel = args.label)

set_params(title = args.title)

plt.savefig(args.out_name)

if args.show_plot:
    plt.show()


