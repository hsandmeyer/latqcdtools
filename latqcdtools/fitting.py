import sys
from scipy.optimize import minimize, curve_fit, fmin_bfgs
import numpy as np
from scipy.linalg import inv, det
import latqcdtools.logger as lg

try:
    import mpmath as mpm
    mpm.mp.dps = 100  # For the error computation we need very high precision in some cases
    mpmath_avail = True
except ImportError:
    lg.warn("WARNING: mpmath not found. Error computation is likely to fail!", 'WARN')
    mpmath_avail = False

from numpy import linalg
import math
from latqcdtools.tools import *
from latqcdtools.statistics import *
from latqcdtools.levenmarq import *
from latqcdtools.plotting import *
from latqcdtools.optimize import *
from inspect import signature
import matplotlib.pyplot as plt
import matplotlib as mpl
import math
import subprocess
import os
import traceback
from latqcdtools.num_deriv import *


class NotAvailableError(Exception):
    pass


"""
Calculate the covariance matrix. The matrix is normalized with N-1.
This means sqrt(diag(cov))=error of single measurement and not
sqrt(diag(cov))=error of mean value

Parameters
----------

data: two dimensional array_like
2D array with the raw data. The first axis corresponds to the observables and
the second axis corresponds to the indivual measurements on that observable

Returns
-------
Covariance matrix and the mean value of the data

"""


class IllegalArgumentError(ValueError):
    pass


class Fitter:
    """
    Base class for fitting routines

    The :class:`Fitter`, contains all information necessary for fitting:
    The data and the function to be fitted and optional the data for the errors.
    For error handling one can either weight each data point as it is the usual case
    or use a full correlated fit.
    There are different minimization algorithms available. Many of them need the gradient or
    hessian of the chisquare. One way is set the derivatives of the fitting function from
    outside. The derivatives of the actual chisquare are then computed via error propagation.
    Another way is to use numerical derivatives. There are two ways to compute the derivatives
    of the chisqare numerically. Either compute the numerical derivative of the whole chisquare 
    (derive_chisq = True), or compute the derivatives of the fitting function and use error
    propagation. (derive_chisq = False) The latter is expected to be more stable and is the
    default case. For the computation of the numerical derivatives there are two possibilities:
    Either use a difference quotient (use_diff = True) or use an algorithmic derivative which
    is implemented using algopy
    (use_alg = True)

    Parameters
    ----------
    func : callable
        Function to be fitted. Depending on parameter expand the format has to be
        func(x, a, b, *args)
        or
        func(x, params, *args)
    xdata : array_like
        xdata used for fit. These data may be higher dimensional. This may be the case when
        your fit functions needs more than one parameter. However, the number of
        elements in the first axis has to be equal to the number of elements in ydata
    ydata : array_like
        ydata used for fit
    edata : arry_like, optional, default: None
        Data for the error. Either pass an 1D array of errors of a full covariance matrix.
        In case of errors, the errors are interpreted as edata = sqrt(variance).
        For the case of the covariance matrix no root has to be taken: variance = diag(edata)
    grad : callable, optional, default: None
        gradient of the fit function
    hess : callable, optional, default: None
        hessian of the fit function
    args : array_like, optional, default: ()
        Optional arguments that shall be passed to func and that should not be fitted
    grad_args : array_like, optional, default: None
        Optional parameter for the gradient. If set to None the arguments for the function 
        are used (args)
    hess_args : array_like, optional, default: None
        Optional parameter for the hessian. If set to None the arguments for the function 
        are used (args)
    expand : bool, optional, default: True
        expand the parameter for the fitting function. If set to true, function has to look
        like
        func(x, a, b, *args)
        otherwise it has to look like
        func(x, params, *args)
    tol : float, optional, default: 1e-12
        Tolerance for the minimization
    max_fev: int, optional, default: 10000
        Maximum number of iterations / function evaluations
    use_diff : bool, optional, default: True
        In case of numerical derivative use the difference quotient for approximation
    use_alg : bool, optional, default: False
        In case of numerical derivative use an analytical derivative using algopy.
        Much slower then difference quotient. If set along use_diff, use_alg is preferred.
        If boths set to False derive_chisq will be set to True and an difference quotient
        will be used for numerical derivatives
    no_chache : bool, optional, default: False
        Disable caching. Might be necessary when using custom numerical derivatives
    norm_err_chi2 : bool, optional, default: True
        Multiply errors with chi**2/d.o.f. This is the usual case for fitting algorithms
    derive_chisq : bool, optional, default: False
        In case of numerical derivative, apply the derivative to the whole chisquare
        instead of the function.
    use_corr : bool, optional, default: False
        Use the correlation matrix instead of the covariance matrix. In that case, the data
        and the fit function are rescaled. This reduces numerical errors for the inversion
        of the covariance matrix but may need more computation time.
    xmin : float, optional, default: -inf
        Minimum xvalue for xdata that should be included into the fit
    xmax : float, optional, default: inf
        Maximum xvalue for xdata that should be included into the fit
    cut_eig : bool, optional, default: False
        Cut lower eigenvalues of covariance matrix
    cut_perc : float, optional, default: 0
        percentage of eigenvalues that should be cut
    test_tol : float, optional, default: 1e-12
        Tolerance that is allowed when testing for singular matrices in error computation
    try_all : bool, optional, default: False
        In try fit: Try all algorithms and choose the best fit. The default is to return the
        results of the first fit that did not fail
    func_sup_numpy : bool, optional, default: False
        Set to true, if the function supports numpy arrays as input for xdata.
        This gives a large performance boost. If you pass a gradient, or a hessian, it is
        expected that the first index refers to the parameter index and the second one to each
        data point. This means len(grad[0]) >= len(grad).
    always_return : bool, optional, default: False
        Always return, even if error computation failed

    Returns
    -------
    :class:`Fitter` object



    Examples
    --------

    For usage, create an instance of class fitter an then call do_fit or try_fit.
    >>> func = lambda x,a:a*x**2
    >>> fitter = Fitter(func, [1,2,3,4], [1,3,2,1], [0.4, 0.5, 0.3, 0.2])
    >>> fitter.do_fit(start_params = [1])
    (array([0.08876904]), array([0.04924371]), 17.872433846281407)


    """
    # Allowed keys for the constructor
    _allowed_keys = ['grad', 'hess', 'args', 'expand', 'grad_args', 'hess_args',
                     'tol', 'use_diff', 'use_alg', 'no_cache',
                     'norm_err_chi2', 'derive_chisq', 'cut_eig',
                     'cut_perc', 'test_tol', 'max_fev', 'try_all', 'func_sup_numpy', 'use_corr',
                     'always_return']

    # All possible algorithms.
    _all_algs = ["levenberg", "curve_fit", "L-BFGS-B", "TNC", "Powell", "Nelder-Mead", "COBYLA",
                 "SLSQP", "CG", "BFGS", "dogleg", "trust-ncg"]

    # Standard algorithms for the minimization
    _std_algs = ["levenberg", "curve_fit",
                 "TNC", "Powell", "Nelder-Mead", "COBYLA"]

    # Algorithms that turn out to be rather fast
    _fast_algs = ["levenberg", "curve_fit", "TNC", "Powell", "Nelder-Mead"]

    def __init__(self, func, xdata, ydata, edata=None, **kwargs):
        diff = set(set(kwargs.keys()) - set(self._allowed_keys))
        if len(diff) != 0:
            raise IllegalArgumentError("Illegal argument(s) to fitter", *diff)

        # Store data
        self._xdata = np.array(xdata, dtype=float)
        self._ydata = np.array(ydata, dtype=float)

        # Initialize fitting data
        self._fit_xdata = self._xdata
        self._fit_ydata = self._ydata

        self._init_options(kwargs)

        # Initialize func. This is also done in set_func, but we need it before that
        self._func = func

        # Get number of parameters
        self._get_numb_params()

        # This variable store the result from the last fit. This is used as start parameters
        # for the next fit, if no new start parameters are provided
        self._saved_params = np.ones(self._numb_params)
        # Current status of the fit errors. Initialize with inf
        self._saved_errors = np.full(self._numb_params, np.inf)
        self._saved_pcov = np.full(
            (self._numb_params, self._numb_params), np.inf)

        self.set_func(func, kwargs.get('grad', None), kwargs.get('hess', None))

        # If the derivatives are computed by the minimization algorithms itself, meaning
        # that the derivatives are applied to the chi_square and not to the fit function,
        # we have to switch of caching. Otherwise the numerical derivatives will fail as they
        # work on the cache.
        if self._derive_chisq:
            self._no_cache = True

        # Caching variables. In order to boost performance, we cache results.
        self._cache_array = None
        self._cache_jac = None
        self._cache_hess = None

        # Variables that hold the parameters that belong to the above caching variables
        self._cache_p_array = np.full(self._numb_params, None)
        self._cache_p_jac = np.full(self._numb_params, None)
        self._cache_p_hess = np.full(self._numb_params, None)

        # For constrained fits. Please see https://arxiv.org/abs/hep-lat/0110175
        self._priorval = np.ones(self._numb_params)
        self._priorsigma = np.ones(self._numb_params)

        # Flag if we perform constraint fits
        self._checkprior = False

        # It might be necessary to prevent generation of new fit data when doing a fit.
        # If this variable is set, the fit is performed on the current fit data
        self._no_new_data = False

        # Check if we have the covariance matrix available and compute weights etc.
        self._init_edata(edata)
        self._xmin = None
        self._xmax = None

        self._cut_eig = kwargs.get('cut_eig', False)
        self._cut_perc = kwargs.get('cut_perc', 0.0)
        if self._cut_eig and self._use_corr:
            raise ValueError("cut_eig and use_corr are in conflict")

    """
    Initialize the arrays that are used for error handling of the fit data:
    Compute the weights, the covariance matrix and the error arrays.
    
    Parameters
    ----------
    edata: array_like
        Array of errors or covariance matrix or None
    """

    def _init_edata(self, edata):
        # Check if we have the covariance matrix available and compute weights etc.
        if edata is not None:
            edata = np.asarray(edata, dtype=float)
            try:
                edata[0][0]
                self._cov_avail = True

                # Weights of a normal non-correlated fit
                self._weights = 1 / np.diag(edata)

                # Errors of a normal non-correlated fit
                self._edata = np.sqrt(np.diag(edata))

                # Initialize fit error data
                self._fit_edata = self._edata

                # Covariance matrix
                self._cov = edata

            except (IndexError, TypeError) as e:
                self._cov_avail = False

                # Covariance matrix is diagonal
                self._cov = np.diag(np.array(edata)**2)

                # Errors of a normal non-correlated fit
                self._edata = np.asarray(edata)

                # Initialize fit error data
                self._fit_edata = self._edata

                # Weights of a normal non-correlated fit
                self._weights = 1 / self._edata**2
        else:
            # Initialize everything to one in case of non-available error information
            self._cov = np.diag(np.ones(len(self._ydata)))
            self._cov_avail = False
            self._edata = None
            self._weights = np.ones_like(self._ydata)

        # Correlation matrix
        self._cor = norm_cov(self._cov)

        # Initialize if we perform a correlated fit. This can be switched off later on.
        self._correlated_fit = self._cov_avail

    """
    Initialize all the options
    Parameters
    ----------
    kwargs: dictionary
        Dictionary with all options passed to __init__
    
    """

    def _init_options(self, kwargs):
        # Parameters defined by the use. See above documentation
        self._no_cache = kwargs.get('no_cache', True)
        self._use_diff = kwargs.get('use_diff', True)
        self._use_alg = kwargs.get('use_alg', False)
        self._derive_chisq = kwargs.get('derive_chisq', False)
        self._expand = kwargs.get('expand', True)
        self._func_sup_numpy = kwargs.get('func_sup_numpy', False)
        self._tol = kwargs.get('tol', 1e-12)
        self._test_tol = kwargs.get('test_tol', 1e-12)
        self._max_fev = kwargs.get('max_fev', None)
        self._norm_err_chi2 = kwargs.get('norm_err_chi2', True)
        self._try_all = kwargs.get('try_all', True)
        self._use_corr = kwargs.get('use_corr', False)
        self._always_return = kwargs.get('always_return', False)

        self._args = kwargs.get('args', ())
        self._grad_args = kwargs.get('grad_args', None)
        if self._grad_args is None:
            self._grad_args = self._args
        self._hess_args = kwargs.get('hess_args', None)
        if self._hess_args is None:
            self._hess_args = self._args

        if type(self._max_fev) is int:
            tmp_fev = self._max_fev
            self._max_fev = dict()
            for alg in self._all_algs:
                self._max_fev[alg] = tmp_fev

        if self._max_fev is None:
            self._max_fev = {"levenberg": 30000,
                             "curve_fit": 50000,
                             "L-BFGS-B": 15000,
                             "TNC": 15000,
                             "Powell": 30000,
                             "Nelder-Mead": 15000,
                             "COBYLA": 15000,
                             "SLSQP": 15000,
                             "CG": 15000,
                             "BFGS": 15000,
                             "dogleg": 15000,
                             "trust-ncg": 15000
                             }

    """
    Generate the data that are used for the fit. The data for the fit are stored in variables
    called self._fit_...
    A filter is applied to the data to make sure they lie between xmin and xmax.
    If self._cut_eig is set, the eigenvalues of the covariance matrix are cut.
    This function is called before each fit and creates copies of the actual
    fitting data in case of non trivial xmin and xmax. If one has passed
    a covariance matrix but does not want perform a correlated fit, i. e.
    correlated = False, only the diagonal of the covariance matrix
    will be used for the fit

    Parameters
    ----------

    xmin : bool
        minimum x-value that data points should have to be considered for the fit

    xmax : bool
        maximum x-value that data points should have to be considered for the fit

    correlated : bool/None, optional, default: None
        Define whether the next fit takes care of correlations or not. This does not
        overwrite self._cov_avail. If None, a correlated fit is performed, if the
        covariance matrix is available.
        
    """

    def gen_fit_data(self, xmin, xmax, correlated=None, ind=None):
        if correlated is None:
            correlated = self._cov_avail
        self._correlated_fit = correlated
        self._xmin = xmin
        self._xmax = xmax

        # Check if xdata is higher dimensional
        try:
            self._xdata[0][0]
            xdata_high_dim = True

        except (ValueError, IndexError):
            xdata_high_dim = False

        # Reset caching data in case we get he same parameters but fit on a different data set
        self._cache_p_array = np.full(self._numb_params, None)
        self._cache_p_jac = np.full(self._numb_params, None)
        self._cache_p_hess = np.full(self._numb_params, None)

        if ind is None:
            ind = (self._xdata >= xmin) & (self._xdata <= xmax)
        else:
            ind = (self._xdata >= xmin) & (self._xdata <= xmax) & ind

        # For multi-dimensional xdata we have to convert the index array to one dimension to
        # match to the dimensions of ydata
        if xdata_high_dim:
            ind = np.array([any(i) for i in ind], dtype=bool)

        # Subsets of the data, that match to the fit range.
        # These subsets are used for the actual fit.
        self._fit_xdata = self._xdata[ind]
        self._fit_ydata = self._ydata[ind]
        if correlated:
            if self._cut_eig:
                self._fit_cov = cut_eig_cov(self._cov[np.ix_(ind, ind)],
                                            self._fit_ydata, self._cut_perc, True, 1)
            else:
                self._fit_cov = self._cov[np.ix_(ind, ind)]
        else:
            self._fit_cov = np.diag(np.diag(self._cov)[ind])

        self._fit_cor = norm_cov(self._fit_cov)

        self._fit_weights = self._weights[ind]

        if self._edata is not None:
            self._fit_edata = self._edata[ind]
        else:
            self._fit_edata = np.ones_like(self._fit_ydata)

        # If we use the correlation matrix instead of the covariance matrix, we want to make
        # sure that the inverse covariance matrix is not used. Therefore we set it to None.
        # Same for the opposite case
        if self._use_corr:
            self._fit_inv_cor = inv(self._fit_cor)
            self._fit_inv_cov = None
            test = self._fit_inv_cor.dot(self._fit_cor)
        else:
            self._fit_inv_cor = None
            self._fit_inv_cov = inv(self._fit_cov)
            test = self._fit_inv_cov.dot(self._fit_cov)

        sum_off_diag = np.sum(test - np.identity(len(self._fit_ydata)))
        if sum_off_diag > 1e-5:
            lg.warn("WARNING: Inverse of covariance matrix is imprecise:"
                    " Off diagonals of test matrix> 1e-5")
            lg.warn("Try use_corr = True")
        if sum_off_diag > 1e-4:
            raise ValueError("Inverse of covariance matrix too imprecise: "
                             "Off diagonals of test matrix > 1e-4")

        self._numb_data = len(self._fit_ydata)

    """
    Find out the number of parameters that the fit function takes. In case of non expanded
    parameters, we simply try how large the parameter array has to be without generating
    an exception. Result is stored in self._numb_params
    """

    def _get_numb_params(self):
        ntries = 100
        if self._expand:
            self._numb_params = len(
                signature(self._func).parameters) - 1 - len(self._args)
        else:
            params = []
            i = 0
            for i in range(ntries):
                params.append(1)
                try:
                    i += 1
                    if self._func_sup_numpy:
                        self._func(self._xdata, params, *self._args)
                    else:
                        self._func(self._xdata[0], params, *self._args)
                    self._numb_params = i
                    return
                except Exception as e:
                    if i == ntries:
                        lg.debug("Last error was", e)
                        traceback.print_exc()
            raise IndexError("Fit function does not work with up to " + str(ntries)
                             + " parameters")

    """
    Set fitting function, gradient, hessian and their arguments. Also initialize self.func,
    self.hess and self.grad.
    These point to the actual wrappers which are used in the fit. In case of provided
    gradient or Hessian, this will be wrap_grad or wrap_hess, respectively. In case of
    numerical derivatives, this will be num_grad and num_hess or alg_grad and alg_hess
    depending on self._use_diff and self._use_alg

    Parameters
    ----------

    func : callable
        Function to be fitted
    grad : callable, optional, default: None
        gradient of the fit function
    hess : callable, optional, default: None
        hessian of the fit function
    args : array_like, optional, default: ()
        
    grad_args : array_like, optional, default: None
        Optional parameter for the gradient. If set to None the arguments for the function 
        are used (args)
    hess_args : array_like, optional, default: None
        Optional parameter for the hessian. If set to None the arguments for the function 
        are used (args)
    """

    def set_func(self, func, grad=None, hess=None, args=None, grad_args=None,
                 hess_args=None):

        # Direct storage of the user functions.
        self._func = func
        self._grad = grad
        self._hess = hess

        # Later we only access self.func, self.grad, and self.hess. These are wrappers around
        # the user function or the numerical derivatives. Below choose the right wrappers

        if self._hess is None:
            if self._use_diff and not self._derive_chisq:
                self.hess = self.num_hess
            elif self._use_alg and not self._derive_chisq:
                self.hess = self.alg_hess
            else:
                self.hess = None
                self._derive_chisq = True
        else:
            self.hess = self.wrap_hess

        if self._grad is None:
            if self._use_diff and not self._derive_chisq:
                self.grad = self.num_grad
            elif self._use_alg and not self._derive_chisq:
                self.grad = self.alg_grad
            else:
                self.grad = None
                self._derive_chisq = True
        else:
            self.grad = self.wrap_grad

        if args is not None:
            self._args = args

        if grad_args is not None:
            self._grad_args = grad_args
        elif self._args is not None:
            self._grad_args = self._args

        if hess_args is not None:
            self._hess_args = hess_args
        elif self._args is not None:
            self._hess_args = self._args

        self.check_start_params()

    """
    Check if the start parameters work with the fitting function. If not:
    Generate new default start_parameters. These are stored in self._saved_params
    """

    def check_start_params(self):
        try:
            if self._func_sup_numpy:
                if self._expand:
                    self._func(self._fit_xdata, *(tuple(self._saved_params)
                                                  + tuple(self._args)))
                else:
                    self._func(self._fit_xdata,
                               self._saved_params, *self._args)
            else:
                if self._expand:
                    self._func(self._xdata[0], *(tuple(self._saved_params)
                                                 + tuple(self._args)))
                else:
                    self._func(self._xdata[0], self._saved_params, *self._args)
        except Exception as e:
            raise(e)
            lg.info("Function cannot handle start_parameters. Generate new defaults")
            if lg.isLevel("DEBUG"):
                traceback.print_exc()
            self._get_numb_params()
            self._saved_params = np.ones(self._numb_params)
        if any(np.isnan(self._saved_params) | np.isinf(self._saved_params)):
            lg.info("Nan or inf in start parameters. Generate new defaults")
            self._get_numb_params()
            self._saved_params = np.ones(self._numb_params)

    """Algorithmic gradient using algopy"""

    def alg_grad(self, x, params):
        return alg_fit_grad(x, params, self._func, self._args)

    """Algorithmic Hessian using algopy"""

    def alg_hess(self, x, params):
        return alg_fit_hess(x, params, self._func, self._args)

    """Numerical gradient using the difference quotient"""

    def num_grad(self, x, params):
        return diff_fit_grad(x, params, self._func, self._args, expand=self._expand)

    """Numerical Hessian using the difference quotient"""

    def num_hess(self, x, params):
        return diff_fit_hess(x, params, self._func, self._args, expand=self._expand)

    """Wrap the gradient provided by the user"""

    def wrap_grad(self, x, params):
        if self._expand:
            return self._grad(x, *(tuple(params) + tuple(self._grad_args)))
        else:
            return self._grad(x, params, *self._grad_args)

    """Wrap the Hessian provided by the user"""

    def wrap_hess(self, x, params):
        if self._expand:
            return self._hess(x, *(tuple(params) + tuple(self._hess_args)))
        else:
            return self._hess(x, params, *self._hess_args)

    """Wrap the function provided by the user"""

    def wrap_func(self, x, params):
        if self._expand:
            return self._func(x, *(tuple(params) + tuple(self._args)))
        else:
            return self._func(x, params, *self._args)

    """
    Return the array of the function values at each position in self._fit_xdata
    """

    def fit_ansatz_array(self, params):
        params = np.asarray(params)
        # Check if we have computed the same array before. If yes, return the cached values
        if any(self._cache_p_array != params) or self._no_cache:
            # If the function supports numpy objects as input, we can call it directly.
            # Otherwise we have to loop over all values in self._fit_xdata
            if self._func_sup_numpy:
                ret = self.wrap_func(self._fit_xdata, params)
            else:
                ret = np.array([self.wrap_func(value, params) for value
                                in self._fit_xdata])
            self._cache_array = np.copy(ret)
            self._cache_p_array = params
            return ret
        else:
            return np.copy(self._cache_array)

    """
    Return the array of the gradients at each position in self._fit_xdata
    """

    def jacobian_fit_ansatz_array(self, params):
        params = np.asarray(params)
        # Check if we have computed the same array before. If yes, return the cached values
        if any(self._cache_p_jac != params) or self._no_cache:
            # If the gradient supports numpy objects as input, we can call it directly.
            # Otherwise we have to loop over all values in self._fit_xdata
            if self._func_sup_numpy:
                # grad is just a wrapper. grad_args are considered in this wrapper
                ret = self.grad(self._fit_xdata, params).transpose()
            else:
                ret = np.array([self.grad(value, params)
                               for value in self._fit_xdata])
            self._cache_jac = np.copy(ret)
            self._cache_p_jac = params
            return ret
        else:
            return np.copy(self._cache_jac)

    """
    Return the array of Hessians at each position in self._fit_xdata
    """

    def hess_fit_ansatz_array(self, params):
        params = np.asarray(params)
        # Check if we have computed the same array before. If yes, return the cached values
        if any(self._cache_p_hess != params) or self._no_cache:
            # If the Hessian supports numpy objects as input, we can call it directly.
            # Otherwise we have to loop over all values in self._fit_xdata
            if self._func_sup_numpy:
                # hess is just a wrapper. hess_args are considered in this wrapper
                ret = self.hess(self._fit_xdata, params).transpose()
            else:
                ret = np.array([self.hess(value, params)
                               for value in self._fit_xdata])
            self._cache_hess = np.copy(ret)
            self._cache_p_hess = params
            return ret
        else:
            return np.copy(self._cache_hess)

    """
    Compute the gradient of the chisquare. Used by some solvers in the minimization routine
    """

    def grad_chisquare(self, params):
        jac = self.jacobian_fit_ansatz_array(params).transpose()
        diff = self.fit_ansatz_array(params) - self._fit_ydata

        # For a non-correlated fit both will work, but the latter is faster
        if self._correlated_fit:
            # If we use the correlation matrix, we have to compensate here.
            if self._use_corr:
                inv_cov_mat = self._fit_inv_cor
                jac /= self._fit_edata
                diff /= self._fit_edata
            else:
                inv_cov_mat = self._fit_inv_cov

            ret = 2 * jac.dot(inv_cov_mat.dot(diff))
        else:
            ret = 2 * jac.dot(self._fit_weights * diff)

        if self._checkprior:
            for i in range(len(self._priorsigma)):
                ret[i] += 2 * (params[i]-self._priorval[i]) \
                    / (self._priorsigma[i]**2)
        return ret

    """
    Compute the hessian of the chisquare. Used by some solvers in the minimization routine
    """

    def hess_chisquare(self, params):
        hess = self.hess_fit_ansatz_array(params).transpose()
        jac = self.jacobian_fit_ansatz_array(params).transpose()
        diff = self.fit_ansatz_array(params) - self._fit_ydata

        # For a non-correlated fit both will work, but the latter is faster
        if self._correlated_fit:
            # If we use the correlation matrix, we have to compensate here.
            if self._use_corr:
                inv_cov_mat = self._fit_inv_cor
                hess /= self._fit_edata
                jac /= self._fit_edata
                diff /= self._fit_edata
            else:
                inv_cov_mat = self._fit_inv_cov

            ret = 2 * (hess.dot(inv_cov_mat.dot(diff.transpose()))
                       + jac.dot(inv_cov_mat.dot(jac.transpose())))
        else:
            ret = 2 * (hess.dot(self._fit_weights * diff)
                       + jac.dot((self._fit_weights * jac).transpose()))

        inv_prsig = np.diag(1.0 / np.array(self._priorsigma))
        if self._checkprior:
            ret += 2 * inv_prsig**2
        return ret

    """
    Compute the chisquare, i.e. the chi^2. This is the function that will be minimized
    """

    def calc_chisquare(self, params):
        diff = self._fit_ydata - self.fit_ansatz_array(params)

        # For a non-correlated fit both will work, but the latter is faster
        if self._correlated_fit:
            # If we use the correlation matrix, we have to compensate here.
            if self._use_corr:
                inv_cov_mat = self._fit_inv_cor
                diff /= self._fit_edata
            else:
                inv_cov_mat = self._fit_inv_cov

            res = diff.dot(inv_cov_mat.dot(diff))
        else:
            res = diff.dot(self._fit_weights * diff)

        if self._checkprior:
            for i in range(len(self._priorsigma)):
                res += ((params[i] - self._priorval[i])**2
                        / self._priorsigma[i]**2)
        return res

    """
    Compute the normalized chisqare, i.e. the chi^2/d.o.f.
    """

    def calc_chisquare_dof(self, params, xmin=-np.inf, xmax=np.inf):
        self.gen_fit_data(xmin, xmax)
        dof = len(self._fit_ydata) - len(params)
        return self.calc_chisquare(params) / dof

    """
    For the error computation we need the Jacobian of the array of function values.
    If self._derive_chisq is True, we cannot use self.grad_fit_ansatz_array.
    In that case, the Jacobian is calculated using this function
    """

    def _num_func_jacobian(self, params):
        if self._use_alg:
            ret = alg_jac(params, self.fit_ansatz_array)
        else:
            ret = diff_jac(params, self.fit_ansatz_array)
        return ret

    """
    Minimize the chi^2 using the algorithm given in algorithm. For
    algorithm = "levenberg", we use a self implemented version of the Levenberg-Marquardt
    minimization algorithm. For all other algorithms, the scipy minimize routine is used.

    Parameters
    ----------

    start_params: array_like
        The start parameters that are used for the minimization
    algorithm: string
        The algorithm that will be used


    Returns
    -------
    params:
        Array of the parameters that minimize the chisquare 
    nfev:
        Number of iterations/function evaluation that was needed to find the minimum
    chi2:
        The minimum value of the chisquare
    """

    def minimize_chi2(self, start_params, algorithm):

        if self.grad is not None:
            jac_func = self.grad_chisquare
        else:
            jac_func = None

        if self.hess is not None:
            hess_func = self.hess_chisquare
        else:
            hess_func = None

        if algorithm == "curve_fit":
            if self._func_sup_numpy:
                func = lambda x, *p: self.wrap_func(x, p)
            else:
                func = lambda xarray, * \
                    p: [self.wrap_func(x, p) for x in xarray]

            cov = self._fit_cov

            # If no gradient has been provided by the user, it is probably better to use
            # the numerical derivative from curve_fit instead of our own.
            if self._grad is not None:
                if self._func_sup_numpy:
                    grad = lambda x, *p: np.array(self.grad(x, p)).transpose()
                else:
                    grad = lambda xarray, *p: [np.array(self.grad(x, p)).transpose()
                                               for x in xarray]
            else:
                grad = None
            grad = None

            params, pcov = curve_fit(func, self._fit_xdata, self._fit_ydata,
                                     sigma=cov, p0=start_params, jac=grad, ftol=self._tol,
                                     maxfev=self._max_fev["curve_fit"])
            nfev = 0

        else:
            params, nfev = minimize(self.calc_chisquare, jac_func, hess_func, start_params,
                                    self._tol, self._max_fev[algorithm], use_alg=self._use_alg,
                                    algorithm=algorithm)

        if any(np.isnan(params)) or any(np.isinf(params)):
            raise ValueError(algorithm + ": Fit result is inf or nan!")
        chi2 = self.calc_chisquare(params)
        return params, nfev, chi2

    """
    Compute the covariance matrix of the fit parameters via error propagation from the
    original fit data. In case no errors have been provided, they are assumed to be one.
    The covariance matrix is computed as pcov = (J^t * C^-1 * J)^-1 where J is the Jacobian of
    the fit function and C is the covariance matrix of the data points.
    By default, the result is multiplied with the fit quality, i.e. chi^2/d.o.f.

    Parameters
    ----------
    params: array_like
        Parameters for which the errors should be computed
    chi2: float
        The chisquare for those parameters
    algorithm: string
        The algorithm that has been used to compute these errors
        (Necessary for strings in exceptions)

    Returns
    ------
    pcov:
        Correlation matrix of the fit parameters
    fit_errors:
        Diagonal of pcov
    dof:
        Number degree of freedoms
    """

    def compute_err(self, params, chi2, algorithm):
        if self.grad is None:
            tmp_no_cache = self._no_cache
            self._no_cache = True
            jac = self._num_func_jacobian(params)
            self._no_cache = tmp_no_cache

        else:
            jac = self.jacobian_fit_ansatz_array(params)

        if self._use_corr:
            inv_cov_mat = self._fit_inv_cor
            jac = jac.transpose() / self._fit_edata
            jac = jac.transpose()
        else:
            inv_cov_mat = self._fit_inv_cov

        dof = len(self._fit_ydata) - len(params)

        if dof > 0:
            jej = jac.transpose().dot(inv_cov_mat.dot(jac))

            try:
                if mpmath_avail:
                    inv_jej = mpm.matrix(jej)**-1
                    test = np.array(
                        (inv_jej*mpm.matrix(jej)).tolist(), dtype=float)
                    inv_jej = np.array(inv_jej.tolist(), dtype=float)

                else:
                    inv_jej = inv(jej)
                    test = inv_jej.dot(jej)

                if abs(np.sum(test) - np.sum(np.diag(test))) > self._test_tol:
                    #fit_errors = [np.nan for i in range(len(params))]
                    if self._always_return:
                        fit_errors = np.array(
                            [np.nan for i in range(len(params))])
                    else:
                        lg.warn("WARNING: Off diagonals in test matrix are larger than",
                                self._test_tol)
                        lg.warn("Test - matrix:")
                        lg.warn(test)
                        lg.warn(
                            "If not already done, installing mpmath might solve this issue!")
                        raise ValueError(
                            algorithm + ": Precision lost when computing errors!")
                else:
                    # I have seen cases where one does not multiply with chi2/dof. This is not
                    # really necessary if the fit is good enough
                    if self._norm_err_chi2 == True:
                        pcov = chi2 / dof * inv_jej
                    else:
                        pcov = inv_jej
                    if np.min(np.diag(pcov)) < 0:
                        if self._always_return:
                            fit_errors = np.array(
                                [np.nan for i in range(len(params))])
                        else:
                            raise ValueError(
                                algorithm + ": Negative entries for the variance!")
                    else:
                        fit_errors = np.sqrt(np.diag(pcov))

            except ZeroDivisionError as e:
                if self._always_return:
                    fit_errors = np.array([np.nan for i in range(len(params))])
                    pcov = np.full((len(params), len(params)), np.nan)
                else:
                    raise e

        else:
            fit_errors = np.array([np.nan for i in range(len(params))])
            pcov = np.full((len(params), len(params)), np.nan)
        return pcov, fit_errors, dof

    """
    Perform the fit. No new fit data are generated. Usually this should not be 
    called from outside.
    Parameters
    ----------
    start_params: array_like
        Start parameters for the fit
    algorithm: string
        The algorithm for the fit
    priorval:
        For constrained fits. Please see https://arxiv.org/abs/hep-lat/0110175
        Prior values for the fit
    priorsigma:
        #For constrained fits. Please see https://arxiv.org/abs/hep-lat/0110175
        Prior sigmas for the fit

    Returns
    -------
        params:
            The fit parameters
        fit_errors:
            The fit errors
        chi2:
            The chisquare at the parameters
        dof:
            Number degrees of freedom
        pcov:
            Covariance of the parameters
        nfev:
            Number of iterations/function evaluations
    """

    def general_fit(self, start_params=None, algorithm="levenberg", priorval=None,
                    priorsigma=None):

        # Prior values are a good point for starting the fit
        if priorval is not None and start_params is None:
            start_params = priorval

        # For a fit with only one parameter, we also accept a scalar. Check if this is the case
        if start_params is not None:
            try:
                start_params[0]
                self._saved_params = start_params
            except (TypeError, IndexError):  # If start_parameters is not a list
                self._saved_params = [start_params]

        # Make sure, we have a numpy object
        self._saved_params = np.array(self._saved_params, dtype=float)

        # Check for consistency
        self.check_start_params()

        # If the fit function has parameters that have default values that should also be fitted,
        # the automatic computed numb_params is wrong. Therefore we make sure that
        # self._numb_params corresponds to self._saved_params at this point
        self._numb_params = len(self._saved_params)

        # Initialize prior values
        if priorsigma is not None:
            self._priorsigma = priorsigma
            if priorval is None:
                raise ValueError("Priorsigma passed but priorval is None")
            self._priorval = priorval
            self._checkprior = True
        else:
            if priorval is not None:
                raise ValueError("Priorval passed but priorsigma is None")
            self._priorval = [0 for i in range(self._numb_params)]
            self._priorsigma = [1 for i in range(self._numb_params)]
            self._checkprior = False

        # Check for consistency
        if self._checkprior:
            if len(self._priorsigma) != self._numb_params:
                raise IndexError(
                    "Number priorsigma != number of fit parameters")

            if len(self._priorval) != self._numb_params:
                raise IndexError("Number priorval != number of fit parameters")

        # Initialize caching variables as numpy objects.
        # This is necessary, as the scipy.optimize routines which are used in
        # minimize_chi2 return simple lists
        self._cache_p_array = np.full(self._numb_params, None)
        self._cache_p_jac = np.full(self._numb_params, None)
        self._cache_p_hess = np.full(self._numb_params, None)

        dof = len(self._fit_ydata) - len(self._saved_params)
        if dof < 0:
            raise IndexError("Less data points than fit parameters")

        # Do the minimization
        params, nfev, chi2 = self.minimize_chi2(self._saved_params, algorithm)

        # Compute errors
        pcov, fit_errors, dof = self.compute_err(params, chi2, algorithm)

        return params, fit_errors, chi2, dof, pcov, nfev

    """
    Perform the fit. This is what you should usually call. Try different algorithms and 
    choose the one with the smallest chi^2.

    Parameters
    ----------
    algorithms: string or None, optional, default = None
        List of strings with the algorithms that can be used. Possible values are:
             "levenberg", "L-BFGS-B", "TNC", "Powell" ,"Nelder-Mead", "COBYLA", "SLSQP"
             "CG", "BFGS", "dogleg", "trust-ncg".
        The latter 4 usually do not work.
        When provided None, the first 7 algorithms are used
    start_params: array_like, optional, default = None
        The start parameters for the fit.
    priorval: array_like, optional, default = None
        #For constrained fits. Please see https://arxiv.org/abs/hep-lat/0110175
        Prior values for the fit
    priorsigma: array_like, optional, default = None
        #For constrained fits. Please see https://arxiv.org/abs/hep-lat/0110175
        Prior sigmas for the fit
    xmin: float, optional, default = -inf
        The minimum x-value that data points must have to be considered in the fit
    xmax: float, optional, default = inf
        The maximum x-value that data points must have to be considered in the fit
    log: bool, optional, default = False
        When trying different algorithms, exceptions might occur. To print default
        logs about this exceptions, set this to True.
        This has nothing to with with the logarithm
    correlated: bool or None, default = None
        Define whether to perform a correlated fit. This is only possible, if a 
        covariance matrix has been passed as edata.
        When None, a correlated fit is performed if the covariance matrix is available.
    ind: array of bools, optional, default = None
        array of bools that corresponds to the fitting points that should be used.
        This is useful, if you want to apply more complex filters than default

    Returns
    -------
    params:
        The final fit parameters
    params_err:
        The error of this fit parameters
    chi_dof:
        Normalized chisquare chi^2/dof
    ret_pcov:
        Return the covariance matrix of the parameters as 4th argument


     """

    def try_fit(self, algorithms=None, start_params=None, priorval=None,
                priorsigma=None, xmin=-np.inf, xmax=np.inf, correlated=None,
                ind=None, ret_pcov=False):

        if algorithms is None:
            algorithms = self._std_algs

        if correlated is None:
            correlated = self._cov_avail

        elif correlated and not self._cov_avail:
            raise NotAvailableError("Covariance matrix is not available")

        # Arrays to store the results of the fits
        all_params = []
        all_fit_errors = []
        all_chi2 = []
        all_pcov = []
        all_nfev = []
        succ_algs = []

        for i, algorithm in enumerate(algorithms):
            try:
                if not self._no_new_data:
                    self.gen_fit_data(xmin, xmax, correlated, ind)
                params, fit_errors, chi2, dof, pcov, nfev = self.general_fit(start_params,
                                                                             algorithm, priorval, priorsigma)
                if self._try_all:
                    all_params.append(params)
                    all_fit_errors.append(fit_errors)
                    all_chi2.append(chi2)
                    all_pcov.append(pcov)
                    all_nfev.append(nfev)
                    succ_algs.append(algorithm)

                    if len(algorithms) > 1:
                        lg.details(algorithm, " successful. Chi^2 = ", chi2)
                    if i < len(algorithms) - 1:
                        lg.details("Trying", algorithms[i+1], "...")
                else:
                    return params, fit_errors, chi2
            except Exception as e:
                lg.details(algorithm, "failed. Error was:", e)
                if i < len(algorithms) - 1:
                    lg.details("Trying", algorithms[i+1], "...")
                if lg.isLevel("DEBUG"):
                    traceback.print_exc()
                if len(all_chi2) == 0 and i >= len(algorithms) - 1:
                    lg.warn("No algorithm converged.")
                    if lg.isLevel("DEBUG"):
                        traceback.print_exc()
                    raise ValueError("Last error was: " + str(e), '\n')

        # Find the smallest chi^2
        min_ind = np.argmin(all_chi2)
        if len(algorithms) > 1:
            lg.details("Choosing", succ_algs[min_ind],
                       "with chi^2 =", all_chi2[min_ind])
            lg.details()

        # Store results internally
        self._saved_params = all_params[min_ind]
        self._saved_errors = all_fit_errors[min_ind]
        self._saved_pcov = all_pcov[min_ind]

        if ret_pcov:
            if dof <= 0:
                return all_params[min_ind], all_fit_errors[min_ind], np.inf, all_pcov[min_ind]
            else:
                return (all_params[min_ind], all_fit_errors[min_ind], all_chi2[min_ind]/dof,
                        all_pcov[min_ind])
        else:
            if dof <= 0:
                return all_params[min_ind], all_fit_errors[min_ind], np.inf
            else:
                return all_params[min_ind], all_fit_errors[min_ind], all_chi2[min_ind]/dof

    """
    Same as try_fit but with only one algorithm
    """

    def do_fit(self, algorithm="levenberg", **kwargs):
        return self.try_fit([algorithm], **kwargs)

    """
    The estimated likelihood of the fit parameters
    """

    def likelihood(self, params=None, xmin=np.inf, xmax=-np.inf, correlated=None):
        return np.exp(self.loglikelihood(params, xmin, xmax, correlated))

    """
    The estimated logarithm of the likelihood of the fit parameters
    """

    def loglikelihood(self, params=None, xmin=None, xmax=None, correlated=None):
        if params is None:
            params = self._saved_params
        if xmin is not None or xmax is not None:
            self.gen_fit_data(xmin, xmax, correlated)
        chi2 = self.calc_chisquare(params)

        cov = self._fit_cov
        ldetc = float(mpm.log(mpm.det(mpm.matrix(cov))))

        llkh = - 0.5 * (self._numb_data * np.log(2 * np.pi) + ldetc + chi2)
        return llkh

    """
    Akaike information criterion
    """

    def aic(self, params=None, xmin=None, xmax=None, correlated=None):
        if params is None:
            params = self._saved_params
        llkh = self.loglikelihood(params, xmin, xmax, correlated)
        return 2 * len(params) - 2 * llkh

    """
    Corrected Akaike information criterion (AICc)
    """

    def aicc(self, params=None, xmin=None, xmax=None, correlated=None):
        if params is None:
            params = self._saved_params
        aic = self.aic(params, xmin, xmax, correlated)
        k = len(params)
        n = self._numb_data
        if n - k - 1 > 0:
            return aic + 2 * k * (k + 1) / (n - k - 1)
        else:
            return np.inf

    """
    Plot the fit function using matplotlib.
    """

    def plot_func(self, params=None, params_err=None, norm_func=None,
                  xmin=None, xmax=None, color=None, alpha=0.1, no_error=False, **kwargs):

        if params_err is None and params is None:
            params_err = self._saved_pcov

        if params is None:
            params = self._saved_params

        if params_err is None:
            params_err = []

        if xmin is None:
            xmin = np.min(self._fit_xdata)
        if xmax is None:
            xmax = np.max(self._fit_xdata)

        if norm_func is None:
            if self._func_sup_numpy:
                def norm_func(x): return np.ones_like(x)
            else:
                def norm_func(x): return 1

            # Error propagation is not implemented for non-expanded parameters.
            # Therefore, we use expanded parameters in this lambda expression
        if self._expand:
            func = lambda x, *params: self._func(x, *(tuple(params) + tuple(self._args))) / \
                norm_func(x)
        else:
            func = lambda x, * \
                params: self._func(x, params, *self._args) / norm_func(x)

        if not no_error:
            # Call the grad wrapper instead of directly self._grad
            grad = lambda x, *params: np.asarray(self.grad(x, params)) / \
                norm_func(x)

            plot_func(func, xmin=xmin,
                      xmax=xmax, args=params,
                      args_err=params_err, grad=grad,
                      color=color, alpha=alpha, func_sup_numpy=self._func_sup_numpy,
                      expand=True, **kwargs
                      )
        else:
            plot_func(func, xmin=xmin,
                      xmax=xmax, args=params,
                      color=color, func_sup_numpy=self._func_sup_numpy,
                      expand=True, **kwargs
                      )

    """
    Plot the fit function using matplotlib.
    """

    def save_func(self, filename, params=None, params_err=None, norm_func=None,
                  xmin=None, xmax=None, color=None, alpha=0.1, no_error=False, **kwargs):

        if params_err is None and params is None:
            params_err = self._saved_pcov

        if params is None:
            params = self._saved_params

        if params_err is None:
            params_err = []

        if xmin is None:
            xmin = np.min(self._fit_xdata)
        if xmax is None:
            xmax = np.max(self._fit_xdata)

        if norm_func is None:
            if self._func_sup_numpy:
                def norm_func(x): return np.ones_like(x)
            else:
                def norm_func(x): return 1

            # Error propagation is not implemented for non-expanded parameters.
            # Therefore, we use expanded parameters in this lambda expression
        if self._expand:
            func = lambda x, *params: self._func(x, *(tuple(params) + tuple(self._args))) / \
                norm_func(x)
        else:
            func = lambda x, * \
                params: self._func(x, params, *self._args) / norm_func(x)

        if not no_error:
            # Call the grad wrapper instead of directly self._grad
            grad = lambda x, *params: np.asarray(self.grad(x, params)) / \
                norm_func(x)

            save_func(func, filename, xmin=xmin,
                      xmax=xmax, args=params,
                      args_err=params_err, grad=grad,
                      color=color, alpha=alpha, func_sup_numpy=self._func_sup_numpy,
                      expand=True, **kwargs
                      )
        else:
            save_func(func, filename, xmin=xmin,
                      xmax=xmax, args=params,
                      color=color, func_sup_numpy=self._func_sup_numpy,
                      expand=True, **kwargs
                      )

    """
    Plot the fit data using matplotlib
    """

    def plot_data(self, norm_func=None, xmin=-np.inf, xmax=np.inf, ylog=False,
                  **kwargs):

        if norm_func is None:
            if self._func_sup_numpy:
                def norm_func(x): return np.ones_like(x)
            else:
                def norm_func(x): return 1

        if ylog:
            plt.yscale('log')

        # We don't use self.gen_fit_data, because this might give a singluar covariance matrix
        # for this xmin and xmax. As the covariance matrix is inverted in gen_fit_data we
        # do it by hand here
        ind = (self._xdata >= xmin) & (self._xdata <= xmax)
        self._fit_xdata = self._xdata[ind]
        self._fit_ydata = self._ydata[ind]

        if self._func_sup_numpy:
            norm = norm_func(self._fit_xdata)
        else:
            norm = np.array(list(map(norm_func, self._fit_xdata)))

        if self._edata is not None:
            self._fit_edata = self._edata[ind]
            plot_dots(self._fit_xdata, self._fit_ydata / norm,
                      self._fit_edata / norm, **kwargs)
        else:
            plot_dots(self._fit_xdata, self._fit_ydata / norm, **kwargs)

    """
    Plot the fit and the fit data.
    Parameters
    ----------

    filename: string
        The filename for the plot. If None, the plot is not saved and you can add 
        further changes via matplotlib.pyplot
    params: array_like, optional
        Parameters for the fit function
    params_err:
        Errors of the above parameters
    notex:
        Do not use tex for plotting
    xmin:
        Xmin for the data plot
    xmax:
        Xmax for the data plot
    ranges:
        2D array of ints. If you want to plot multiple fit results, this array should
        contain the boundaries for each fit. It should look like
        [[xmin_1, xmax_1], [xmin_2, xmax_2]...]
        In that case params and params_err also need to be arrays of parameters
    ylog:
        Use an logarithmic y-scale
    size: 2D-tuple
        Size of the plot
    **kwargs
        Additional arguments that can be passed to the plotting functions.
        See plotting.py
    """

    def plot_fit(self, filename=None, params=None, params_err=None, notex=False,
                 norm_func=None, ranges=None,
                 ylog=False, size=(15, 10), font_size=16, no_error=False, fix_ylim=False,
                 args_data=None, args_func=None, xmin=None, xmax=None, **kwargs
                 ):

        if args_func is None:
            args_func = {}
        if args_data is None:
            args_data = {}

        args_data.update(kwargs)

        if xmin is not None:
            args_data['xmin'] = xmin

        if xmax is not None:
            args_data['xmax'] = xmax

        if filename is not None:
            if not notex:
                latexify(*size, font_size=font_size)
            else:
                init_notex(*size, font_size=font_size)

        try:
            # Save xmin and xmax, as they will be overwritten in plot_data
            try:
                xmin = np.min(self._fit_xdata)
                xmax = np.max(self._fit_xdata)
            except ValueError:
                xmin = None
                xmax = None

            if 'color' not in args_data:
                args_data['color'] = 'black'

            self.plot_data(norm_func=norm_func, ylog=ylog,
                           zod=1000, **args_data)

            if fix_ylim:
                ylims = plt.gca().get_ylim()

            if ranges is None:
                if 'xmin' not in args_func:
                    args_func['xmin'] = xmin

                if 'xmax' not in args_func:
                    args_func['xmax'] = xmax

                self.plot_func(params, params_err, norm_func, no_error=no_error,
                               **args_func)
            else:
                cmap = mpl.cm.jet
                for i, val in enumerate(ranges):
                    col = cmap(0.9 * i / max((float(len(ranges)) - 1), 1))
                    if params_err is None:
                        self.plot_func(params[i], norm_func, xmin=val[0],
                                       xmax=val[1], color=col, no_error=no_error,
                                       **args_func)
                    else:
                        self.plot_func(params[i], params_err[i], norm_func, xmin=val[0],
                                       xmax=val[1], color=col, no_error=no_error,
                                       **args_func)
            if fix_ylim:
                plt.ylim(ylims)

            if filename is not None:
                plt.savefig(filename)

        except Exception as e:
            if lg.isLevel("DEBUG"):
                traceback.print_exc()
            lg.warn("Plotting of fit failed: ", e, "\n")

    def plot_cov(self, filename=None, xmin=None, xmax=None, ymin=None,
                 ymax=None, notex=False, title=None, size=(15, 10), font_size=16):
        if filename is not None:
            if not notex:
                latexify(*size, font_size=font_size)
            else:
                init_notex(*size, font_size=font_size)

        if xmin == None:
            gxmin = -np.inf
        else:
            gxmin = xmin

        if xmax == None:
            gxmax = -np.inf
        else:
            gxmax = xmax

        try:
            self.gen_fit_data(gxmin, gxmax)
        except ValueError as e:
            lg.warn("WARNING", e)
            pass

        plot_cov(self._fit_cor, filename,
                 title=title, notex=notex,
                 xmin=xmin, xmax=ymax,
                 ymin=xmin, ymax=ymax)

    def plot_eig(self, filename=None, xmin=None, xmax=None, notex=False,
                 title=None, size=(15, 10), font_size=16):
        if filename is not None:
            if not notex:
                latexify(*size, font_size=font_size)
            else:
                init_notex(*size, font_size=font_size)

        if xmin == None:
            gxmin = -np.inf
        else:
            gxmin = xmin

        if xmax == None:
            gxmax = -np.inf
        else:
            gxmax = xmax

        try:
            self.gen_fit_data(gxmin, gxmax)
        except ValueError as e:
            lg.warn("WARNING", e)
            pass

        plot_eig(self._fit_cov, filename,
                 title=title, notex=notex)

    """
    Get value and error of the fit at a specific point x
    Parameters
    ----------
    x: scalar
        x-value at which the function is evaluated
    params: array_like, optional, default = None
        parameters for the function
    params_err: array_like, optional, default = None
        error of the parameters for the function
    """

    def get_func(self, x, params=None, params_err=None):

        if params_err is None and params is None:
            params_err = self._saved_pcov
        if params is None:
            params = self._saved_params

        if params_err is None:
            raise ValueError("Please pass params along with params_err")

        value = self.wrap_func(x, params)

        func = lambda x, *params: self.wrap_func(x, params)
        grad = lambda x, *params: self.grad(x, params)
        try:
            error = [error_prop_func(xval, func, params, params_err,
                                     grad=grad) for xval in x]
        except (ValueError, TypeError):
            error = error_prop_func(x, func, params, params_err,
                                    grad=grad)

        return value, error


"""Print aligned"""


def print_scl(string, scl, align_numb=60, level="INFO"):
    lg.log(level, string.ljust(align_numb) + "%.6e" % scl)


"""Print aligned"""


def print_res(string, res, res_err=None, chi_dof=None, align_numb=60, level="INFO"):

    if res is not None:
        lg.log(level, (string.ljust(align_numb)
                       + "[" + " ".join(["%.6e" for i in range(len(res))]) + "]") % tuple(res))
    else:
        lg.log(level, string.ljust(align_numb) + "None")

    if res_err is not None:
        lg.log(level, ("Fit error".ljust(align_numb)
                       + "[" + " ".join(["%.6e" for i in range(len(res_err))]) + "]")
               % tuple(res_err))

    if chi_dof is not None:
        print_scl("chi^2/d.o.f.", chi_dof, level=level)


"""
Wrapper to fitter initialization and the fit in one step. See above for arguments
"""


def do_fit(func, xdata, ydata, edata=None, start_params=None, priorval=None,
           priorsigma=None, algorithm="levenberg", xmin=-np.inf, xmax=np.inf, **kwargs):
    fit = Fitter(func, xdata, ydata, edata, **kwargs)
    return fit.do_fit(start_params=start_params, priorval=priorval,
                      priorsigma=priorsigma, algorithm=algorithm, xmin=xmin, xmax=xmax)


"""
Wrapper to fitter initialization and the fit in one step. See above for arguments.
For historical reasons algorithms has no default values here.
"""


def try_fit(func, algorithms, xdata, ydata, edata=None, start_params=None,
            priorval=None, priorsigma=None, log=False, xmin=-np.inf, xmax=np.inf,
            **kwargs):
    fit = Fitter(func, xdata, ydata, edata, **kwargs)
    return fit.try_fit(algorithms, start_params, priorval, priorsigma, log=log,
                       xmin=xmin, xmax=xmax)


"""
Wrapper for gnuplot fits.

Parameters
----------

data: array_like
    The data used for the fit. These data will be passed to gnuplot as the input file.
    Elements in data are accessed by data[column, row].
func_string: string
    string for the function that will be parsed by gnuplot. You do not need to specify the
    function name.
    Example: "a*x**2 + b"
variables: list of chars
    list of variables that should be fitted
column_string: string
    columns that will be used by gnuplot
    e.g.: "1:(1/$2)"
start_parameters: array_like
    start parameters for the fit
silent: bool, optional, default = True
    Suppress the gnuplot output
fit_ranges: array_like
    [xmin, xmax]
    

"""


def fit_gnuplot(data, func_string, variables, column_string='1:2', start_params=(),
                silent=True, fit_range=None):

    gnuplot = subprocess.Popen("gnuplot", shell=True, stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE)
    if silent:
        gnuplot.stdin.write("set fit quiet\n".encode())  # print to stdout

    #print(func_string + "\n")
    variables_string = ""
    print_string = "print "
    print_err_string = "print "

    for i in variables[:len(variables) - 1]:
        variables_string += i + ", "
        print_string += i + ", \" \", "
        print_err_string += i + "_err, \" \", "

    variables_string += variables[len(variables) - 1]
    print_string += variables[len(variables) - 1] + "\n"
    print_err_string += variables[len(variables) - 1] + "_err" + "\n"

    # print to stdout
    gnuplot.stdin.write("set fit logfile '/dev/null'\n".encode())
    for i, value in enumerate(start_params):
        gnuplot.stdin.write(
            (str(variables[i]) + "=" + str(value) + "\n").encode())

    gnuplot.stdin.write(("f(x)=" + func_string + "\n").encode())

    if fit_range == None:
        gnuplot.stdin.write(("fit f(x) \"-\" u " + column_string
                             + " via " + variables_string + "\n").encode())

    else:
        gnuplot.stdin.write(("fit [" + str(fit_range[0]) + ":" + str(fit_range[1])
                             + "]  f(x) \"-\" u " + column_string + " via " + variables_string + "\n").encode())

    data = np.array(data)
    for i in data.transpose():
        data_str = ""
        for j in i[:len(i) - 1]:
            data_str += str(j) + " "

        data_str += str(i[len(i) - 1]) + "\n"
        gnuplot.stdin.write(data_str.encode())
    gnuplot.stdin.write("e".encode())

    # For some reason we have to reset gnuplot print
    gnuplot.stdin.write("set print\n".encode())
    gnuplot.stdin.write("set print \"-\" \n".encode())  # print to stdout
    gnuplot.stdin.write(print_string.encode())
    gnuplot.stdin.write(print_err_string.encode())
    gnuplot.stdin.write("print FIT_STDFIT\n".encode())
    gnuplot.stdin.close()
    try:
        output = gnuplot.stdout.readline()
        #print("OUTPUT", output)
        res = [float(i) for i in output.split()]
        if len(variables) < len(data[0]):
            output = gnuplot.stdout.readline()
            #print("OUTPUT", output)
            res_err = [float(i) for i in output.split()]
            output = gnuplot.stdout.readline()
            #print("OUTPUT", output)
            chi_dof = float(output)
        else:
            res_err = [np.nan for i in range(len(res))]
            chi_dof = 0
    except Exception as e:
        lg.info(output)
        lg.info("Error in gnuplot fit. Return nan")
        res = [np.nan for i in range(len(variables))]
        res_err = [np.nan for i in range(len(variables))]
        chi_dof = np.nan

    if len(res) != len(variables) or len(res_err) != len(variables):
        lg.info("Error in gnuplot fit. Return nan")
        res = [np.nan for i in range(len(variables))]
        res_err = [np.nan for i in range(len(variables))]
        chi_dof = np.nan

    return res, res_err, chi_dof**2


"""
Cut eigenvalues of the covariance matrix
method=1: cut values to threshold
method=2: average lowest eigenvalues
"""


def cut_eig_cov(ncov, ydata, numb_cut, percentage, method):
    if percentage:
        numb_cut = int(len(ydata) * numb_cut / 100.)
# Cut eigenvalues
    v, w = np.linalg.eig(ncov)
    infl_eig = []
    sorted_eig = np.sort(v)
    cut_value = sorted_eig[numb_cut]
    for i, value in enumerate(v):
        if(value < cut_value):
            if method == 1:
                v[i] = cut_value
            infl_eig.append(v[i])
    if method == 2:
        if len(infl_eig) == 0:
            return ncov
        av = np.mean(infl_eig)
        for i, value in enumerate(v):
            if(value < cut_value):
                v[i] = av
    lg.details(len(infl_eig), "of", len(v), "eigenvalues have been cut. "
               "Largest cut eigenvalue was", sorted_eig[numb_cut])
    ncov = np.real(w.dot(np.diag(v).dot(w.transpose())))
    return ncov


if __name__ == "__main__":
    import doctest
    doctest.testmod()
