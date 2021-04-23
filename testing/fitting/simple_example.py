#!/usr/bin/env python3

from latqcdtools.readin import *
from latqcdtools.fitting import *


def fit_func(x, params):
    a = params[0]
    b = params[1]
    c = params[2]
    return a * x**2 + b * x + c

def grad(x, a, b, c):
    return [x**2, x, 1]

xdata, ydata, edata = read_in("wurf.dat", 1, 3, 4)

fitter = Fitter(fit_func, xdata, ydata, expand = False)

res, res_err, chi_dof, pcov = fitter.try_fit(start_params = [1, 2, 3], algorithms = ['levenberg', 'curve_fit'], ret_pcov = True)

fitter.plot_fit()
plt.show()

print(res, res_err, chi_dof, pcov)


