#!/usr/bin/env python3
import sys
sys.path.append("..")
from test_tools import *
from latqcdtools.fitting import *
from latqcdtools.readin import *
from latqcdtools.tools import *
import numpy as np
#import pylib.ad.admath as adm
import latqcdtools.tools as tools
from latqcdtools.plotting import *


def simple(x, a):
    return a * x

# simple quadratic fit


def fit_func(x, a, b, c):
    return a * x**2 + b * x + c


def fit_func_ne(x, a):  # Same as above withou expansion (ne = no expansion)
    return fit_func(x, *a)


def grad_fit_func(x, a, b, c):
    return [x**2, x, 1]


def grad_fit_func_ne(x, a):
    return grad_fit_func(x, *a)


def hess_fit_func(x, a, b, c):
    return [[0, 0, 0], [0, 0, 0], [0, 0, 0]]


def hess_fit_func_ne(x, a):
    return hess_fit_func(x, *a)


# correlator fit
def one_state(x, A, m, Nt):
    return A * np.cosh(m * (Nt / 2 - x))


def grad_one_state(x, A, m, Nt):
    return [np.cosh(m * (Nt / 2 - x)), A * np.sinh(m * (Nt / 2 - x)) * (Nt / 2 - x)]


def hess_one_state(x, A, m, Nt):
    return np.array([[0, np.sinh(m * (Nt / 2 - x)) * (Nt / 2 - x)],
                     [np.sinh(m * (Nt / 2 - x)) * (Nt / 2 - x), A * np.cosh(m * (Nt / 2 - x)) * (Nt / 2 - x)**2]])


xdata, ydata, edata = read_in("wurf.dat", 1, 3, 4)


print("Testing quadradic fit with expansion of parameters...\n")


res_true = [-1.943413e+00, 6.800332e+00, -1.123906e-01]
res_err_true = [8.859594e-02, 3.204274e-01, 2.476714e-01]


res, res_err, chi_dof = do_fit(
    fit_func, xdata, ydata, grad=grad_fit_func, hess=hess_fit_func)
print_results(res, res_true, res_err, res_err_true,
              "Exact levenberg without error")

res_true = [-1.930355e+00, 6.747380e+00, -6.979050e-02]
res_err_true = [9.072495e-02, 3.357190e-01, 2.676424e-01]


res, tmp = curve_fit(fit_func, xdata, ydata, sigma=edata)
res_err = np.sqrt(np.diag(tmp))
print_results(res, res_true, res_err, res_err_true,
              "As a reference: Curve_fit")


fitter = Fitter(fit_func, xdata, ydata, edata,
                grad=grad_fit_func, hess=hess_fit_func)
res, res_err, chi_dof = fitter.do_fit(start_params=[1, 1, 1])
fitter.plot_fit("quadratic_fit.pdf")

print_results(res, res_true, res_err, res_err_true, "Exact levenberg")

# Most algorithms are extremly sensitive to the numerical derivatives.
# There are even cases, where they work only with their built in derivative

fitter = Fitter(fit_func, xdata, ydata, edata, func_sup_numpy=True)
res, res_err, chi_dof = fitter.do_fit(start_params=[1, 1, 1])
fitter.plot_fit("quadratic_fit_num.pdf")

print_results(res, res_true, res_err, res_err_true,
              "Numerical levenberg using difference quotient")


res, res_err, chi_dof = do_fit(fit_func, xdata, ydata, edata, [1, 1, 1], use_diff=True,
                               use_alg=False, derive_chisq=True)
print_results(res, res_true, res_err, res_err_true, "Numerical levenberg using difference "
              "quotient applied on chisquare")


res, res_err, chi_dof = do_fit(fit_func, xdata, ydata, edata, [1, 1, 1], use_diff=True,
                               use_alg=False, derive_chisq=True, use_corr=True, func_sup_numpy=True)
print_results(res, res_true, res_err, res_err_true, "Numerical levenberg using difference "
              "quotient applied on chisquare with normalized covariance matrix")


res, res_err, chi_dof = do_fit(fit_func, xdata, ydata, edata, [1, 1, 1], algorithm="BFGS",
                               grad=grad_fit_func)
print_results(res, res_true, res_err, res_err_true, "Exact BFGS")


res, res_err, chi_dof = do_fit(fit_func, xdata, ydata, edata, [1, 1, 1], algorithm="TNC",
                               grad=grad_fit_func)
print_results(res, res_true, res_err, res_err_true, "Exact TNC")


res, res_err, chi_dof = do_fit(fit_func, xdata, ydata, edata, [1, 1, 1], algorithm="L-BFGS-B",
                               derive_chisq=True)
print_results(res, res_true, res_err, res_err_true,
              "Numerical L-BFGS-B using built in derivative")


res, res_err, chi_dof = do_fit(fit_func, xdata, ydata, edata, [1, 1, 1], algorithm="SLSQP",
                               derive_chisq=True)
print_results(res, res_true, res_err, res_err_true,
              "Numerical SLSQP using built in derivative")


res, res_err, chi_dof = do_fit(fit_func, xdata, ydata, edata, [
                               1, 1, 1], algorithm="Powell")
print_results(res, res_true, res_err, res_err_true, "Powell quadratic ")


print("Testing quadradic fit without expansion of parameters...\n")


if tools.algopy_avail:

    res, res_err, chi_dof = do_fit(fit_func_ne, xdata, ydata, edata, [1, 1, 1],
                                   use_diff=False, use_alg=True, expand=False)
    print_results(res, res_true, res_err, res_err_true,
                  "Numerical levenberg using algorithmic derivative")

    res, res_err, chi_dof = do_fit(fit_func_ne, xdata, ydata, edata, [1, 1, 1],
                                   use_diff=False, use_alg=True, derive_chisq=True, expand=False)
    print_results(res, res_true, res_err, res_err_true,
                  "Numerical levenberg using algorithmic derivative applied on chisquare")

    res, res_err, chi_dof = do_fit(fit_func_ne, xdata, ydata, edata, [1, 1, 1],
                                   algorithm="BFGS", use_diff=False, use_alg=True, expand=False)
print_results(res, res_true, res_err, res_err_true,
              "Numerical BFGS using algorithmic derivative")


print("Testing correlator fit...\n")


xdata, ydata, edata = read_in("corr.dat", 1, 2, 3)

res_true = [5.088129e-05, 2.943403e-01]
res_err_true = [5.042611e-08, 8.380914e-05]


res, res_err, chi_dof = do_fit(one_state, xdata, ydata, edata,
                               [1, 1], grad=grad_one_state, hess=hess_one_state, args=(64,))
print_results(res, res_true, res_err, res_err_true, "Exact levenberg")


res, res_err, chi_dof = do_fit(one_state, xdata, ydata, edata,
                               [1, 1], grad=grad_one_state, hess=hess_one_state, args=(64,), use_corr=True)
print_results(res, res_true, res_err, res_err_true,
              "Exact levenberg using normalized covariance matrix")


res, res_err, chi_dof = do_fit(one_state, xdata, ydata, edata,
                               [1, 1], grad=grad_one_state, hess=hess_one_state, args=(64,), use_corr=True)
print_results(res, res_true, res_err, res_err_true,
              "Exact levenberg using normalized covariance matrix")


res, res_err, chi_dof = do_fit(one_state, xdata, ydata, np.diag(edata)**2,
                               [1, 1], grad=grad_one_state, hess=hess_one_state, args=(64,))
print_results(res, res_true, res_err, res_err_true,
              "Diagonal correlation matrix")


res, res_err, chi_dof = do_fit(one_state, xdata, ydata, edata, [1, 1], args=(64,),
                               use_diff=False)
print_results(res, res_true, res_err, res_err_true,
              "Numerical levenberg with difference quotient applied on chisquare")


# Numerical derivative gives a slightly different result
res_err_true = [5.0425819803e-08, 8.38114689761e-05]


res, res_err, chi_dof = do_fit(one_state, xdata, ydata, edata, [1, 1], args=(64,),
                               use_diff=True)
print_results(res, res_true, res_err, res_err_true,
              "Numerical levenberg with difference quotient")


xdata, data, nconfs = read_in_pure("corr_pure.dat", 1, 2)
cov = calc_cov(data)
ydata = std_mean(data, axis=1)

#np.savetxt("cov.txt", cov)
cov_true = np.loadtxt("cov.txt")
cov_test = True

for i in range(len(cov)):
    for j in range(len(cov[i])):
        if not rel_check(cov[i, j], cov_true[i, j]):
            cov_test = False
            print("cov[" + str(i) + "," + str(j) + "] = " + str(cov[i, j])
                  + " != cov_true[" + str(i) + "," + str(j) + "] = " + str(cov_true[i, j]))

print("============================")
if cov_test:
    print("Covariance matrix test passed")
else:
    print("Covariance matrix test test FAILED!")
print("============================")
print()


res, res_err, chi_dof = do_fit(one_state, xdata, ydata, cov / nconfs,
                               res_true, grad=grad_one_state, hess=hess_one_state, args=(64,))
res_true = [4.988713e-05, 2.950030e-01]
res_err_true = [1.176005e-06, 5.573209e-04]
print_results(res, res_true, res_err, res_err_true,
              "Exact levenberg for correlated data")


res, res_err, chi_dof = do_fit(one_state, xdata, ydata, cov / nconfs,
                               res_true, grad=grad_one_state, hess=hess_one_state, args=(
                                   64,),
                               algorithm="curve_fit")
print_results(res, res_true, res_err, res_err_true,
              "Curve_fit for correlated data")


res, res_err, chi_dof = do_fit(one_state, xdata, ydata, cov / nconfs,
                               res_true, args=(64,),
                               algorithm="curve_fit")
print_results(res, res_true, res_err, res_err_true,
              "Numerical curve_fit for correlated data")


res, tmp = curve_fit(lambda x, a, b: one_state(
    x, a, b, 64), xdata, ydata, sigma=cov / nconfs)
res_err = np.sqrt(np.diag(tmp))
print_results(res, res_true, res_err, res_err_true,
              "As a reference: Direct correlated curve fit")

res, res_err, chi_dof = do_fit(one_state, xdata, ydata, cov / nconfs,
                               grad=grad_one_state, hess=hess_one_state, args=(64,), use_corr=True,
                               no_cache=True)
print_results(res, res_true, res_err, res_err_true,
              "Exact levenberg for correlated data with normalized covariance matrix")

print("============================")
print("Testing constraint fit...\n")


startparam = [5e-05, 3e-01]
sigma = [5e-05, 3e-01]

res, res_err, chi_dof = do_fit(one_state, xdata, ydata, cov / nconfs, priorval=startparam,
                               priorsigma=sigma, args=(64,), func_sup_numpy=True)
print_results(res, res_true, res_err, res_err_true, "Constraint fit")


print("============================")
print("Testing 2D xdata...\n")


xdata = np.ones((10, 2))
xdata[:, 0] = np.arange(10)
xdata[:5, 1] = np.full(5, 4)

ydata = np.arange(10)
edata = np.ones(10)


def func_2d(x, a):
    return a*x[0]*x[1]


res_true = [5.102041e-01]
res_err_true = [1.189990e-01]
res, res_err, chi_dof = do_fit(func_2d, xdata, ydata, edata)

print_results(res, res_true, res_err, res_err_true, "2D xdata fit")


print("============================")
print("All tests done. Please see also generated pdfs")
