#!/usr/bin/env python3
import argparse
from latqcdtools.plateau_finder import *


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = "Program to select a plateau of data points."
            " To the compute the expectation value of that plateau, Gaussian noise"
            " is generated around each data point. The resulting distributions are added and the"
            " final expectation value is computed using the median."
            " The corresponding error is computed using 68% percentiles."
            " The final result is printed to stdout")
    parser.add_argument('filename')

    parser.add_argument('--xdata-col', '-xc', type = int, dest = "xdata_col", default = 1, 
            help = "Column in text file in which the xdata is stored")
    parser.add_argument('--data-col', '-dc', type = int, dest = "data_col", default = 2, 
            help = "Column in text file in which the ydata is stored")
    parser.add_argument('--edata-col', '-ec', type = int, dest = "edata_col", default = None, 
            help = "Column in text file in which the error is stored")

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--chi-col', type = int, dest = "chi_col", default = None,
            help = "Column in text file in which the chi^2 is stored")
    group.add_argument('--amp-col', type = int, dest = 'amp_col', default = None,
            help = "Column in text file in which an amplitude is stored."
            " For instance the amplitude of a mass fit")

    parser.add_argument('--xmin', type = float, dest = 'xmin', default = -np.inf,
            help = "Minimal x-value for data")

    parser.add_argument('--xmax', type = float, dest = 'xmax', default = np.inf,
            help = "Maximal x-value for data")

    parser.add_argument('--range', nargs = 2, dest = 'bounds', type = float, default = None,
            help = "Do not select the range with a plot. Use the range given by this values")
    parser.add_argument('--auto', action = 'store_true', dest = 'auto_range',
            help = "Automatically select the range. Usually imprecise")
    parser.add_argument('--npoints', type = int, dest = 'npoints', default = None,
            help = "How many points shall be used for the automatic plateau selection")
    parser.add_argument('--out-name', dest = 'out_name', default = 'plateau.pdf',
            help = "Output name of the plateau plot")
    parser.add_argument('--title', dest = 'title', default = None,
            help = "Title in plateau plot")
    parser.add_argument('--show-plot', action = 'store_true', dest = 'show_plot',
            help = "Open a window with the results after the plateau selection")
    parser.add_argument('--no-tex', action = 'store_true', dest = 'no_tex',
            help = "Do not use LaTeX for text rendering")
    parser.add_argument('--hist-name', dest = 'hist_name', default = None,
            help = "Name of a histogram that shows the error estimation. "
            "No histogram is plotted without this option")

    parser.add_argument('--xlabel', dest = 'xlabel', default = None,
            help = "X-label of plot")
    parser.add_argument('--ylabel', dest = 'ylabel', default = None,
            help = "Y-label of plot")
    parser.add_argument('--amp-label', dest = 'amp_label', default = "Amplitude",
            help = "Label of the amplitude corresponding to --amp-col")

    parser.add_argument('--acc', type = float, dest = "acc_factor", default = 0.5,
        help = "The plot ranges for the mass plot are chosen automatically. Use this flag, to "
        "define how man points shall enter into the plot. Higher value = more points")
    parser.add_argument('--err-threshold', type = float, default = 0.5,
        help = "Points whose error/value ratio is larger than this threshold"
        " will not enter the plateau calculation")


    args = parser.parse_args()

    if args.edata_col is None:
        args.edata_col = args.data_col + 1

    xdata, ydata, edata = read_in(args.filename, args.xdata_col, args.data_col,
            args.edata_col)

    if args.chi_col is not None:
        chi_dof = read_in(args.filename, args.chi_col)[0]
    else:
        chi_dof = None


    if args.amp_col is not None:
        amp, amp_err = read_in(args.filename, args.amp_col,
                args.amp_col + 1)
    else:
        amp = None
        amp_err = None

    plat_finder = PlateauFinder(xdata, ydata, edata, amp, amp_err, chi_dof,**vars(args))
    res = plat_finder.get_average(args.bounds)
    plat_finder.plot_plat()






    print(*res)





