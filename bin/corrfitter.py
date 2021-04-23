#!/usr/bin/env python3
from latqcdtools.performcorrfit import *
import latqcdtools.logger as lg
from argparse import RawTextHelpFormatter
import sys




class SmartFormatter(argparse.HelpFormatter):

    def _split_lines(self, text, width):
        if text.startswith('R|'):
            return text[2:].splitlines()  
        # this is the RawTextHelpFormatter._split_lines
        return argparse.HelpFormatter._split_lines(self, text, width)



def main():
    print(*sys.argv)
    reparse_argv()
    less_indent_formatter = lambda prog: argparse.RawTextHelpFormatter(prog, max_help_position=40)
    parser = argparse.ArgumentParser(description = " This is a very general program to perform\n"
            " correlator fits. It can handle an arbitrary number of states for the non-oscillating\n"
            " as well as for the oscillating channel. Estimating the initial guess for the fit is completely\n"
            " automatized.\n\n"

            " This routine works in two steps. First data are read in and processed, which\n"
            " means that the mean and the error of the correlator are computed. Additionally\n"
            " the raw input data are stored. Afterwards\n"
            " the fit is performed based on this mean and error. For some fitting options this\n"
            " mean and error are ignored and the fitting process works directly on the raw data.\n"
            " In that case, the mean and the error are only used for the generated plots.\n"

            " The way how errors and mean values of the correlator data are computed\n"
            " is controlled by flags\n that end with \"-data\" (See below). This also defines\n"
            " how the error-bars on the data points that appear in the plots are computed.\n\n"
            " The method to compute the errors of the fit parameters is defined by flags\n"
            " that end with \"-fit\". Please note that for bootstrapping and for the jackknife,\n"
            " the errors on the data points are ignored and the fit is calculated directly\n"
            " from the raw input. In that case, the errors defined by the \"-data\"-flag only\n"
            " show up in the plots but do not contribute to anything else.\n\n"
            " If no \"-data\"-flag is passed, the best method is chosen base on the fit method.\n"
            " This means in particular by default:\n"
            " --jack-fit comes with --jack-data\n\n"
            " --btstr-fit comes with --btstr-data\n\n"
            " --ratio-fit comes with --ratio-data\n\n"
            " --direct-fit comes with std-err-data for correlated fits and\n"
            " with --jack-data otherwise\n\n"

            " The results will be given in the output folder (\"results\" by default)\n"
            " You will find the final fit results in fitmass_*.txt. A plot of the correlator\n"
            " will be given in corr_*.pdf. The effective mass will be given in effmass*.txt.\n"
            " For the effective mass, some of the \"-data\"-keywords might be ignored and\n"
            " a jackknife is used instead\n"
            " If there is at least one oscillating state, you will find additional versions\n"
            " of the files mentioned above with \"_osc_\" or \"non-osc\" in the file names.\n"
            " This will contain information about the separated correlators\n"
            " (See https://arxiv.org/abs/1411.3018 how to separate correlators into oscillating\n"
            " and non-oscillating part).\n"
            " If the fit is correlated you will find a plot of the normalized covariance matrix\n"
            " in cov_*.pdf and a plot of its eigenvalues in eig_*.pdf.\n"
            " For the meaning of the rest of the abbreviations in the filenames,\n"
            " please see below flags.\n"
            ,formatter_class=less_indent_formatter
            )
    parser.add_argument('--corr', '--correlated', action = 'store_true', dest = 'correlated',
            help = "Perform a correlated fit involving the covariance matrix of the data\n"
            " points. This will add \"_cov\" to the output file names.")
    parser.add_argument('--sym', action = 'store_true', default = True,
            help = "Fit only half of the correlator. The correlator will be symmetrized.\n"
            " This will add \"_sym\" to the output file names.")
    parser.add_argument('--asym', action = 'store_false', dest = 'sym',
            help = "Fit the full correlator. The correlator will not be symmetrized.\n"
            " This will add \"_asym\" to the output file names.")
    parser.add_argument('--change-sign', action = 'store_true', dest = 'change_sign',
            help = "Multiply the correlator with -(-1)**nt.\n"
            " This interchanges oscillating and non-oscillating part!\n"
            " Be careful with this option!\n"
            " This will add \"_sc\" to the output file names.")
    parser.add_argument('--auto-sign', action = 'store_true', dest = 'auto_sign',
            help = "Automatically change the sign of even data points if more than half of\n"
            " them have a negative sign\n"
            " If this is the case, the oscillating and non-oscillating part are interchanged!\n"
            " Be careful with this option!")
    parser.add_argument('--nstates', type = int, default = 1,
            help = "Number of non-oscillating states")
    parser.add_argument('--nstates-osc', type = int, dest = 'nstates_osc', default = 0,
            help = "Number of oscillating oscillating")
    parser.add_argument('--cut-eig', action = 'store_true', dest = 'cut_eig',
            help = "Cut lower eigenvalues of the covariance matrix")
    parser.add_argument('--cut-perc', type = float, dest = "cut_perc", default = 30,
            help = "Percentage how many eigenvalues should be cut")
    parser.add_argument('--min-cov-det', action = 'store_true', dest = 'min_cov_det',
            help = "Use the minimal covariance determinant method to estimate mean and covariance\n"
            " See http://scikit-learn.org/stable/modules/generated/sklearn.covariance.MinCovDet.html#id3\n"
            " matrix. This will add \"_mcd\" to the output file names.")
    parser.add_argument('--mcd-supp-frac', type = float, dest = "mcd_supp_frac", default = None,
            help = "Support fraction for Minimum covariance method. (See above link)")
    parser.add_argument('--folder', default = "results",
            help = "Output folder")
    parser.add_argument('--title', default = None,
            help = "The title for all the plots")
    parser.add_argument('--file-string', default = "", dest = 'file_string',
            help = "String that will be put into the naming of the output files")
    parser.add_argument('--nt-column', '-ntc', type = int, dest = "nt_col", default = 1,
            help = "Column of the lattice points (n_\\tau or n_\\sigma)")
    parser.add_argument('--data-column', '-dc', type = int, dest = "data_col", default = 2,
            help = "Column of the data points")
    parser.add_argument('--error-col', '-ec', type = int, dest = "err_col", default = 3,
            help = "When reading direct data, this is the column of the error bars")
    parser.add_argument('--Nt', '-Nt', type = int, dest = "Nt", default = None,
            help = "Do not compute Nt from the data. Instead use this one. This prevents\n"
            " symmetrization of the correlator!")
    parser.add_argument('--numb-samples', '-ns', type = int, dest = "numb_samples", default = 1000,
            help = "Number of samples in the bootstrap for averaging data points")
    parser.add_argument('--numb-fit-samples', '-nfs', type = int, dest = "nfit_samples", default = 100,
            help = "Number of samples in the bootstrap for fitting")
    parser.add_argument('--numb-blocks', '-nb', type = int, dest = "numb_blocks", default = 10,
            help = "Number of jackknife blocks")

    parser.add_argument('--no-tex', dest='notex', action='store_true',
            help = "Do not use Latex for rendering labels")
    parser.add_argument('--log-level', default = "INFO",
            help = "Log level. Available are WARN, INFO, PROGRESS, DETAILS, DEBUG, NONE",
            dest = 'log_level')
    parser.add_argument('--try-all', action='store_true',
            help = "Try fits with all available start parameter"
            " estimation methods. Very expensive", dest = 'try_all', default = None)
    parser.add_argument('--start-params', nargs = '+', dest = 'start_params', type = float,
            help = "Initial guess for the fit")
    parser.add_argument('--fit-range', '--fit-interval', nargs = 2, dest = 'fit_interval',
            type = int,
            help = "Range of n_min that shall be scanned")
    parser.add_argument('--nmax', '--xmax', type = int, dest = 'xmax', default = None,
            help = "Upper limit of the correlator fit")
    parser.add_argument('--priorval', '--prior-val', nargs = '+', dest = 'priorval',
            type = float,
            help = "Perform a constraint fits, this will be the prior values")
    parser.add_argument('--priorsigma', '--prior-sigma', nargs = '+', dest = 'priorsigma',
            type = float,
            help = "Perform a constraint fits, this will be the prior sigmas")
    parser.add_argument('--seed', type = int, default = None,
            help = "Seed for the bootstrap analysis")

    #Read in flags
    parser.add_argument('--jack-data', action = 'store_true', dest = 'jack_data',
            help = "Compute the errors of the data points from a jackknife.\n"
            " This will add \"_jk-data\" to the output file names.")
    parser.add_argument('--std-err-data', action = 'store_true', dest = 'std_err_data',
            help = "Compute the errors of the data points from a standard error.\n"
            " This will add \"_std-err-data\" to the output file names.")
    parser.add_argument('--btstr-data', action = 'store_true', dest = 'btstr_data',
            help = "Compute the errors of the data points from a bootstrap.\n"
            " This will add \"_bs-data\" to the output file names.")
    parser.add_argument('--sample-data', action = 'store_true', dest = 'sample_data',
            help = "Compute the errors of the data points from a standard deviation. \n"
            " This makes sense if the data are averages over bootstrap samples.\n"
            " This will add \"_fr-sample\" (from sample) to the output file names.")
    parser.add_argument('--direct-data', action = 'store_true', dest = 'direct_data',
            help = "Read data that are already averaged.\n"
            " This will add \"_direct-data\" to the output file names.")
    parser.add_argument('--ratio-data', action = 'store_true', dest = 'ratio_data',
            help = "Read in data and compute the ratio G(nt)/G(nt+1).\n"
            " This will add \"_ratio-data\" to the output file names.")

    #Fit flags
    parser.add_argument('--jack-fit', action = 'store_true', dest = 'jack_fit',
            help = "Compute the error on the fit parameters from a jackknife.\n"
            " This will ignore the errors that are given by the data-flag\n"
            " Instead everything is computed directly on the raw data.\n"
            " This will add \"_jk-fit\" to the output file names.")
    parser.add_argument('--direct-fit', action = 'store_true', dest = 'direct_fit',
            help = "Compute the error on the fit parameters directly from the fit.\n"
            " This will add \"_direct-fit\" to the output file names.")
    parser.add_argument('--btstr-fit', action = 'store_true', dest = 'btstr_fit',
            help = "Compute the error on the fit parameters from a bootstrap. \n"
            " This will ignore the errors that are given by the data-flag\n"
            " Instead everything is computed directly on the raw data.\n"
            " If you perform a correlated fit, the same random numbers per n_t value will be used.\n"
            " If not, different random numbers will be chosen to break up the correlation\n"
            " This will add \"_bs-fit\" to the output file names.")
    parser.add_argument('--no-median', action = 'store_false', dest = 'ng_btstr',
            help = "With this flag, all bootstrap routines compute the error by the standard\n"
            " deviation and not by the distribution using quantiles .\n"
            " This will add no-median to the output file names\n"
            )
    parser.add_argument('--scnd-btstr', action = 'store_true', dest = 'scnd_btstr',
            help = "Perform a second bootstrap on each bootstrap sample to determine the error\n"
            " This will add _scnd-bs-fit- to the output file names\n"
            )
    parser.add_argument('--ratio-fit', action = 'store_true', dest = 'ratio_fit',
            help = "Perform a direct fit on the ratio G(nt)/G(nt+1). (Implies --ratio-data)\n"
            " This will add \"_ratio-fit\" to the output file names.")

    parser.add_argument('--xlabel', default = "$n_{\\tau/\\sigma,\mathrm{min.}}$",
            dest = 'xlabel',
            help = "X-label in all the plots")
    parser.add_argument('--ylabel', default = "", dest = 'ylabel',
            help = "Y-label in all the plots")
    parser.add_argument('--plot-size', nargs = 2, dest = 'plot_size', default = (18, 12), 
            type = int,
            help = "Size of the plots")
    parser.add_argument('--plot-no-ylog', action = 'store_true', dest = 'plot_no_ylog',
            help = "Do not use logarithmic y-scale for correlator plots")
    parser.add_argument('--font-size', dest = 'font_size', type = int, default = 11,
            help = "The font size of the plots")

    parser.add_argument('--plot-file', default = None, dest = 'res_filename',
            help = "Plot the correlator from a file instead of performing a fit. \n"
            " You can pass a fitmass... file here")
    parser.add_argument('--plot-start', action = 'store_true', dest = 'plot_start',
            help = "Do not perform a fit. Instead generate a plot with the start parameters.\n"
            " Has to be passed along with --start-params")


    parser.add_argument('filename', help = "The filename containing the data")
    args = parser.parse_args()

    lg.set_log_level(args.log_level)
    args = vars(args)
    del args['log_level']


    #Check that we get all the keys from the command line
    for key in PerformCorrFit.default_args:
        if key not in args:
            raise ParameterError("Key " + key + " not set")

    pfit = PerformCorrFit(**args)
    pfit.run()

if __name__ == '__main__':
    main()

