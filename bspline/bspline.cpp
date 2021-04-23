#include "bspline.h"

int bspline_interpolator::set_data(double *xdata, double *ydata, double *yerr, int len){
    if(_ndata > 0){
	free_mem();
    }
    _ndata = len;
    for (int i = 0; i < len; i++){
	//cout << xdata[i] << " " << ydata[i] << " " << yerr[i] << endl;
	xin.push_back(xdata[i]);
	yin.push_back(ydata[i]);
	yerrin.push_back(yerr[i]);
    }

    _lmin = getLrange();
    _lmax = getLrange();

    allocate();
    return(_ndata);

}

int bspline_interpolator::set_data(double *xdata, double *ydata, double *yerr, int len, double lmin, double lmax){

    set_data(xdata, ydata, yerr, len);
    _lmin = lmin;
    _lmax = lmax;

    return(_ndata);

}

void bspline_interpolator::allocate(){
    /* allocate a bspline workspace*/
    bw = gsl_bspline_alloc(_order, _nbreak);
    B = gsl_vector_alloc(_ncoeffs);

    x = gsl_vector_alloc(_ndata);
    y = gsl_vector_alloc(_ndata);
    X = gsl_matrix_alloc(_ndata, _ncoeffs);
    dB = gsl_matrix_alloc(_nbreak + _order - 2, 2);
    c = gsl_vector_alloc(_ncoeffs);
    w = gsl_vector_alloc(_ndata);
    cov = gsl_matrix_alloc(_ncoeffs, _ncoeffs);
    mw = gsl_multifit_linear_alloc(_ndata, _ncoeffs);
}


int bspline_interpolator::read_data(char *s, double minval, double maxval){
    if(_ndata > 0){
	free_mem();
    }
    _ndata = readin(s, xin, yin, yerrin, minval, maxval);
    if(_ndata == 0){
	cout << "No data points read in!" << endl;
	throw -2;
    }
    allocate();
    return(_ndata);
}


void bspline_interpolator::fit(){

    double chisq;
    //double chisq, Rsq, dof, tss;
    for (size_t i = 0; i < xin.size(); ++i)
    {

	gsl_vector_set(x, i, xin[i]);
	gsl_vector_set(y, i, yin[i]);
	if( (yerrin[i]*yerrin[i])>0.0){
	    gsl_vector_set(w, i, 1.0/(yerrin[i]*yerrin[i]));
	    // gsl_vector_set(w, i, yerrin[i]);
	    // gsl_vector_set(w, i, 1.0);
	}else{
	    gsl_vector_set(w, i, 1.0);
	}

    }

    /* this is the data to be fitted */
    gsl_bspline_knots_uniform(_lmin, _lmax, bw);

    /* construct the fit matrix X */
    for (int i = 0; i < _ndata; ++i)
    {
	double xi = gsl_vector_get(x, i);

	/* compute B_j(xi) for all j */
	gsl_bspline_eval(xi, B, bw);

	/* fill in row i of X */
	for (size_t j = 0; j < _ncoeffs; ++j)
	{
	    double Bj = gsl_vector_get(B, j);
	    gsl_matrix_set(X, i, j, Bj);
	}
    }

    /* do the fit */
    gsl_multifit_wlinear(X, w, y, c, cov, &chisq, mw);

//    dof = _ndata - _ncoeffs;
//    tss = gsl_stats_wtss(w->data, 1, y->data, 1, y->size);
//    Rsq = 1.0 - chisq / tss;
//
    //cerr << "chisq/dof = " << chisq/dof << ", Rsq = " << Rsq << endl; 

}


//Print bspline at a certain value. 
void bspline_interpolator::print_bspline(double xi){
    double yi, yerr;

    get_bspline(xi, &yi, &yerr);
    printf("%f %f %f ", xi, yi, yerr);
    get_bspline_deriv(xi, &yi, &yerr);
    printf("%f %f\n", yi, yerr);

}

//Print bspline in a given interval. 
void bspline_interpolator::print_bspline(double lrange, double rrange, int numbpoints){
    double stepsize = (rrange-lrange)/numbpoints;
    double xi=lrange;
    for (int i = 0; i < numbpoints; ++i){
	print_bspline(xi);
	xi+=stepsize;
    }
}

void bspline_interpolator::print_bspline(char *s, double lrange, double rrange, int numbpoints){
    ofstream ofs(s);
    if(!ofs.is_open()){
	cout << "readin error: Cannot open file '" << s << "'!\n";
	throw -1;
    }   
    double stepsize = (rrange-lrange)/numbpoints;
    double xi=lrange;
    for (int i = 0; i < numbpoints; ++i){
	double yi, yerr;
	get_bspline(xi, &yi, &yerr);
	ofs << xi << ' ' << yi << ' ' << yerr << ' ';

	get_bspline_deriv(xi, &yi, &yerr);
	ofs << yi << ' ' << yerr << endl;
	xi+=stepsize;
    }
    ofs.close();
}
void bspline_interpolator::get_bspline(double x, double *y, double *yerr){
    gsl_bspline_eval(x, B, bw);
    gsl_multifit_linear_est(B, c, cov, y, yerr);
}

void bspline_interpolator::get_bspline_deriv(double x, double *yderiv, double *yderiverr, int nderiv){
#if GSL_MAJOR_VERSION < 2
    gsl_bspline_deriv_eval(x, nderiv, dB, bw, dw);
#else
    gsl_bspline_deriv_eval(x, nderiv, dB, bw);
#endif
    gsl_matrix_get_col(B, dB, nderiv);
    gsl_multifit_linear_est(B, c, cov, yderiv, yderiverr);
}


double bspline_interpolator::getLrange(){
    return *min_element(xin.begin(), xin.end());
}

double bspline_interpolator::getRrange(){
    return *max_element(xin.begin(), xin.end());
}

void bspline_interpolator::setOrder(size_t order){
    _order = order;
    _nbreak = _ncoeffs + 2 - _order;
}
size_t bspline_interpolator::getOrder(){
    return _order;
}

void bspline_interpolator::setNcoeffs(size_t ncoeffs){
    _ncoeffs = ncoeffs;
    _nbreak = _ncoeffs + 2 - _order;

}
size_t bspline_interpolator::getNcoeffs(){
    return _ncoeffs;
}
