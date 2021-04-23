#include <gsl/gsl_bspline.h>
#include <gsl/gsl_multifit.h>
#include <gsl/gsl_randist.h>
#include <gsl/gsl_statistics.h>
#include <gsl/gsl_version.h>
#include <vector>
#include "readin.h"
#include <algorithm>
#include <limits>

/*Default value for the order of the polynomial*/
#define ORDER 4

/* Default number of fit coefficients */
#define NCOEFFS  10

//Class works as following:
//First adjust the parameters order and number of coefficients (number of intervals).
//Then readin the data
//The spline functions have to be fitted to the data
//Output the spline
class bspline_interpolator{
    size_t _order;
    size_t _ncoeffs;
    size_t _nbreak;
    int _ndata;
    gsl_bspline_workspace *bw;
#if ( GSL_MAJOR_VERSION < 2 ) || ((GSL_MAJOR_VERSION == 2) && (GSL_MINOR_VERSION < 4 ))
    gsl_bspline_deriv_workspace *dw;
#else
    gsl_bspline_workspace *dw;
#endif
    gsl_vector *B;
    gsl_vector *c, *w;
    gsl_vector *x, *y;
    gsl_matrix *X, *cov, *dB;
    gsl_multifit_linear_workspace *mw;
    double _lmin;
    double _lmax;
    vector<double> xin;
    vector<double> yin;
    vector<double> yerrin;

    void free_mem(){
	gsl_bspline_free(bw);
	gsl_vector_free(B);
	gsl_vector_free(x);
	gsl_vector_free(y);
	gsl_matrix_free(X);
	gsl_vector_free(c);
	gsl_vector_free(w);
	gsl_matrix_free(cov);
	gsl_matrix_free(dB);
	gsl_multifit_linear_free(mw);
    }

    void allocate();

    public:

    bspline_interpolator():_order(ORDER), _ncoeffs(NCOEFFS), _nbreak(_ncoeffs + 2 - _order), _ndata(0){

    }


    int read_data(char *s, double minval=std::numeric_limits<double>::lowest(),  double maxval=std::numeric_limits<double>::max());

    int set_data(double *xdata, double *ydata, double *yerr, int len);

    int set_data(double *xdata, double *ydata, double *yerr, int len, double lmin, double lmax);

    void fit();


    ~bspline_interpolator(){
	//Only if we have read in data
	if(_ndata > 0){
	    free_mem();
	}
    }

    //Print bspline at a certain value. 
    void print_bspline(double xi);

    //Print bspline in a given interval. 
    void print_bspline(double lrange, double rrange, int numbpoints);

    void print_bspline(char *s, double lrange, double rrange, int numbpoints);

    void get_bspline(double x, double *y, double *yerr);


    //nderiv'th derivative
    void get_bspline_deriv(double x, double *y, double *yerr, int nderiv=1);

    double getLrange();

    double getRrange();

    void setOrder(size_t order);

    size_t getOrder();

    void setNcoeffs(size_t ncoeffs);

    size_t getNcoeffs();
};
