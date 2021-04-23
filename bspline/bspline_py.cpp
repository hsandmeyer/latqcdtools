#include "bspline.h"

using namespace std;
extern "C" void bspline_interpolate(double *xdata, double *ydata, double *yerr, int len, double* x_out, double *out_y, double *out_yerr, int len_out, int order, int ncoeffs){
    bspline_interpolator intpol;
    intpol.setOrder(order);
    intpol.setNcoeffs(ncoeffs);
    double xmin;
    double xmax;
    if (x_out[0] < xdata[0]){
	xmin = x_out[0];
    }else{
	xmin = xdata[0];
    }
    if (x_out[len_out - 1] > xdata[len - 1]){
	xmax = x_out[len_out - 1];
    }else{
	xmax = xdata[len - 1];
    }
    intpol.set_data(xdata, ydata, yerr, len, xmin, xmax);
    intpol.fit();
    for (int i = 0; i < len_out; i++){
	//cout << x_out[i] << " " << out_yerr[i] << endl;
	intpol.get_bspline(x_out[i], &out_y[i], &out_yerr[i]);
    }
}
