#!/usr/bin/env python3
import sys
import argparse
from latqcdtools.jackknife import *
from latqcdtools.bootstr import *
from latqcdtools.tools import *
from latqcdtools.readin import *
from latqcdtools.statistics import *

def print_match(match_data, res, error):
    if match_data is not None:
        for ind, c in enumerate(match_data):
            print(c, " ", end="")
            try:
                for i in res:
                    print(i[ind], " ", end="")
                for i in error:
                    print(i[ind], " ", end="")
            except IndexError:
                print(res[ind], " ", end="")
                print(error[ind], " ", end="")
            print()
    else:
        print(*(tuple(res) + tuple(error)))


def main():

    reparse_argv()
    parser = argparse.ArgumentParser(description = "Program to compute averages "
            "using different statistical methods")


    parser.add_argument('-bs', '--bootstrap', action = 'store_true', default = False)
    parser.add_argument('-jk', '--jackknife', action = 'store_true', default = False)
    parser.add_argument('-ste', '--standard-error', action = 'store_true', default = False)
    parser.add_argument('-std', '--standard-deviation', action = 'store_true', default = False)

    parser.add_argument('--data-cols', '-c', type = int, nargs = '+', default = None,
            help = "Column where data are stored")

    parser.add_argument('-m', '--match', action = 'store_true', default = False,
            help = "Do not compute the average over one total column. "
            "Instead compute the average on data sets that are distinguished by another column")
    parser.add_argument('--match-col', '-mc', type = int, default = 1,
            help = "Column to distinguish data with --match")

    parser.add_argument('--numb-samples', '-ns', type = int, default = 1000,
            help = "Number of samples for bootstrap, default = 1000")
    parser.add_argument('--numb-blocks', '-nb', type = int, default = 20,
            help = "Number of blocks for jackknife, default = 20")

    parser.add_argument('filenames', nargs='*', default = [sys.stdin])

    
    args = parser.parse_args()

    if args.data_cols is None:
        if not args.match:
            args.data_cols = [1]
        else:
            args.data_cols = [2]

    if args.match:
        data = match_data, data, nconfs = read_in_pure(args.filenames[0], args.match_col, args.data_cols[0])
    else:
        data = []
        match_data = None
        for filename in args.filenames:
            data += list(read_in(filename, *args.data_cols))

    if not (args.jackknife or args.bootstrap or args.standard_error or args.standard_deviation):
        args.jackknife = True
    
    if args.jackknife:
        res, res_err = jackknife(std_mean, data, numb_blocks = args.numb_blocks, args = {'axis' : 1})
        print_match(match_data, res, res_err)
    if args.bootstrap:
        res, res_err = bootstr(std_mean, data, args.numb_samples, conf_axis = 1, args = {'axis' : 1})
        print_match(match_data, res, res_err)
    if args.standard_error:
        res, res_err = mean_and_err(data, axis = 1)
        print_match(match_data, res, res_err)
    if args.standard_deviation:
        res, res_err = mean_and_std_dev(data, axis = 1)
        print_match(match_data, res, res_err)


    


if __name__ == '__main__':
    main()
