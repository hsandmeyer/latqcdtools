import scipy.optimize as opt
from latqcdtools.levenmarq import *
import latqcdtools.logger as lg


def minimize(func, jack=None, hess=None, start_params=None, tol=1e-12,
             maxiter=10000, use_alg=False, algorithm=None):

    if algorithm == "levenberg":
        args = (start_params, func, jack, hess)
        kwargs = {'eps': tol, 'use_alg': use_alg,
                  'max_itt': maxiter}
        params, nfev = levenberg(*args, **kwargs)

    else:
        args = (func, start_params)

        if algorithm == "BFGS":
            kwargs = {'method': algorithm,
                      'jac': jack,
                      'tol': tol,
                      'options': {'gtol': tol, 'maxiter': maxiter}}

        elif algorithm == "TNC":
            kwargs = {'method': algorithm,
                      'jac': jack,
                      'tol': tol,
                      'options': {'maxiter': maxiter}}

        elif algorithm == "COBYLA":
            kwargs = {'method': algorithm,
                      'tol': tol,
                      'options': {'maxiter': maxiter}}

        elif algorithm == "SLSQP":
            kwargs = {'method': algorithm,
                      'jac': jack,
                      'tol': tol,
                      'options': {'maxiter': maxiter}}

        elif algorithm == "L-BFGS-B":
            kwargs = {'method': algorithm,
                      'jac': jack,
                      'tol': tol,
                      'options': {'maxiter': maxiter}}

        elif algorithm == "Powell":
            kwargs = {'method': algorithm,
                      'tol': tol,
                      'options': {'xtol': tol, 'ftol': tol,
                                  'maxfev': maxiter}}

        elif algorithm == "Nelder-Mead":
            kwargs = {'method': algorithm,
                      'tol': tol,
                      'options': {'maxiter': maxiter}}

        else:
            kwargs = {'method': algorithm,
                      'jac': jack,
                      'hess': hess,
                      'tol': tol,
                      'options': {'maxiter': maxiter}}

        # At least COBYLA sometimes get stuck in an endless loop. Use timeout to make
        # sure we finish
        res = timeout(opt.minimize, args=args,
                      kwargs=kwargs, timeout_duration=100)

    if algorithm != "levenberg":
        params = res.x
        nfev = res.nfev
        if not res.success:
            lg.details(algorithm, res.message)
            raise ValueError(algorithm + ": Minimization did not converge!")

    try:
        params[0]
    except Exception:
        if isinstance(params, (np.ndarray, np.generic)):
            # somhow numpy 0D arrays have to be converted to scalar explicitly
            params = [np.asscalar(params)]
        else:
            params = [params]

    return params, nfev
