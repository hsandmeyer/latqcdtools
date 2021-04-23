#include "bspline.h"

//Interpolates a given data set
int main (int argc, char ** argv){
    if ( argc < 2 || argc > 4){
	cout << "Usage: " << argv[0] << "[order ncoeffs] data_file" << endl;
	return -1;
    }
    bspline_interpolator intpol;
    int order = 10;
    int ncoeffs = 20;
    if ( argc >= 3){
	order=atoi(argv[1]);
    }
    if ( argc >= 4){
	ncoeffs=atoi(argv[2]);
    }

    intpol.setOrder(order);
    intpol.setNcoeffs(ncoeffs);
    intpol.read_data(argv[argc-1]);
    intpol.fit();
    double lrange=intpol.getLrange();
    double rrange=intpol.getRrange();
    intpol.print_bspline(lrange, rrange, 1000);

    return 0;
}
