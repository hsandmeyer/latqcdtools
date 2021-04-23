#!/usr/bin/env python3
import argparse
from latqcdtools.tools import *
from latqcdtools.extrapolator import *
import latqcdtools.readin as rd
import latqcdtools.logger as lg
import re
import sys


def main():
    print(*sys.argv)
    reparse_argv()
    parser = argparse.ArgumentParser(description = "Very handy tool to perform continuum"
            " extrapolation using splines. Each data set corresponding to a different Nt shall "
            " be passed in a different file. The extrapolation is performed linear in 1/Nt^2."
            " The continuum extrapolation is performed in two steps. First, the data are read "
            " in. One can distinguish "
            " whether these data stem from each lattice configuration, from a bootstrap sample"
            " or if they are already averaged and have error bars. Use the --data-input flag to"
            " define the read-in-method."
            " Afterwards the data are processed and a continuum extrapolation is performed."
            " You can specify how the errors shall be computed using the --method flag"
            )
    parser.add_argument('files', nargs = '+', help = "The files to be used")
    parser.add_argument('--method', default = 'btstr',
            help = "The method used to calculate the error:"
            " 'btstr' for a standard bootstrapping on the raw data."
            " 'gauss_btstr' for a Gaussian bootstrapping around the mean value and error bars."
            " 'from_sample' If the data stem from a bootstrap sample. In each case, the mean"
            " value and error are"
            " calculated using median and 68%% percentiles. Use 'direct', if you only want to"
            " calculate a quick estimate without error computation"
            )
    parser.add_argument('--data-input', dest = 'data_input', default = None,
            help = "Specify how the data shall be interpreted:"
            " 'raw' for raw lattice data."
            " 'direct' for data that are already averaged and have error bars."
            " 'sample' for data that stem from a bootstrap sample."
            )
    parser.add_argument('--Nts', nargs = '+', dest = 'Nts', type = int, default = [],
            help = "The Nt values that correspond to the data. Not necessary, if the"
            " file names look like *_Nt8_* etc.")
    parser.add_argument('--order', type = int, default = 3, help = "Oder of the spline")
    parser.add_argument('--constraints', nargs = '+', type = float, default = [],
            help = "Constraints to stabilize the spline: Pass as multiple of three:" 
            " constraint_position order_of_derivative constraint_value")
    parser.add_argument('--nknots', nargs = '+', dest = 'nknots', type = int,
            help = "Number of knots for the spline. Multiple values possible")
    parser.add_argument('--knots', nargs = '+', dest = 'knots', type = float,
            help = "Define knots. This overwrites --nknots")
    parser.add_argument('--outname', default = "extr", help = "Output name of files")
    parser.add_argument('--folder', default = "./", help = "Output folder. Default = ./")
    parser.add_argument('--plot-results', nargs = '+', dest = 'plot_results', default = [],
            help = "Plot old results. Arguments shall be extr_parameters.txt "
            "extr_cont.txt extr_coeffs.txt")

    parser.add_argument('--xmin', type = float, default = -np.inf,
            help = "Minimal x-value for the extrapolation")
    parser.add_argument('--xmax', type = float, default = np.inf,
            help = "Maximal x-value for the extrapolation")
    parser.add_argument('--tol', type = float, default = 1e-8,
            help = "Tolerance for the fit")
    parser.add_argument('--nsamples', '-ns', type = int, default = None,
            help = "Number of samples for the bootstrap")
    parser.add_argument('--randomization-factor', type = float, default = 0.5,
            help = "The position of the knots is randomized during the bootstrap."
            " Specify how much randomization shall be used. (0 = None, 1 = max)")
    parser.add_argument('--xdata-col', type = int, default = 1,
            help = "Column where the x-values are stored")
    parser.add_argument('--ydata-col', type = int, default = 2,
            help = "Column where the y-values are stored")
    parser.add_argument('--edata-col', type = int, default = None,
            help = "Column where the error-values (if present) are stored")

    parser.add_argument('--base-point', type = float, dest = 'base_point', default = 0.0,
            help = "base point of the spline. Shift this, if you want to use constraints "
            "at x = 0")
    parser.add_argument('--no-tex', action = 'store_true', dest = 'no_tex',
            help = "Do not use LaTeX for text rendering")
    parser.add_argument('--show-plot', action = 'store_true', dest = 'show_plot',
            help = "Show a result plot after the bootstrap")

    parser.add_argument('--plot-xmin', type = float, dest = 'plot_xmin' , default = None,
            help = "Minimal value that shall be plotted")
    parser.add_argument('--plot-xmax', type = float, dest = 'plot_xmax' , default = None,
            help = "Maximal value that shall be plotted")
    parser.add_argument('--title', default = None, help = "Title in plots")
    parser.add_argument('--xlabel', default = None, help = "x-label in plots")
    parser.add_argument('--ylabel', default = None, help = "y-label in plots")

    parser.add_argument('--save-sample', default = False, help = "Save the sample of the"
            " extrapolated data. This file is large")


    parser.add_argument('--log-level', default = "INFO",
            help = "Log level. Available are WARN, INFO, PROGRESS, DETAILS, DEBUG, NONE",
            dest = 'log_level')

    args = parser.parse_args()

    lg.set_log_level(args.log_level)
    kwargs = vars(args)
    del kwargs['log_level']

    if args.data_input is None:
        if args.method == "btstr":
            args.data_input = 'raw'
        if args.method == "gauss_btstr":
            args.data_input = 'direct'
        if args.method == "from_sample":
            args.data_input = 'sample'
        if args.method == "direct":
            raise ValueError("Need data input (--data-input)")

    xdata, ydata, edata, Nts = read_in_extr_files(args.files, args.xdata_col,
            args.ydata_col, args.edata_col, args.Nts, args.data_input)



    kwargs['constraints'] = np.array(kwargs['constraints']).reshape(-1,3)
    #Remove invalid arguments for Extrapolator
    del kwargs['Nts']
    del kwargs['xdata_col']
    del kwargs['ydata_col']
    del kwargs['edata_col']
    del kwargs['files']

    extr = Extrapolator(Nts, xdata, ydata, edata, **kwargs)

    if len(args.plot_results) == 0:
        extr.perform_fits()
        extr.compute_extrapolation()
        extr.save_extrapolation()
    else:
        extr.read_extrapolation()

    extr.plot_extrapolation(args.outname)



if __name__ == '__main__':
    main()
    

