#include "bspline.h"
#include "zbrent.h"
#define c0 1.65

bspline_interpolator intpol;
double lrange;
double rrange;

double diff_err_up(double x){
    
  double ytmp;
  double yerrtmp;
  if ( x >=rrange ) {
    intpol.get_bspline_deriv(rrange, &ytmp, &yerrtmp, 1);
    return(x*x*ytmp - c0);
  }
  if ( x <=lrange ) {
    intpol.get_bspline_deriv(lrange, &ytmp, &yerrtmp, 1);
    return(x*x*ytmp - c0);
  }
  intpol.get_bspline_deriv(x, &ytmp, &yerrtmp, 1);
  return(x*x*(ytmp+yerrtmp) - c0);
}

double diff_err_dn(double x){
    
  double ytmp;
  double yerrtmp;
  if ( x >=rrange ) {
    intpol.get_bspline_deriv(rrange, &ytmp, &yerrtmp, 1);
    return(x*x*ytmp - c0);
  }
  if ( x <=lrange ) {
    intpol.get_bspline_deriv(lrange, &ytmp, &yerrtmp, 1);
    return(x*x*ytmp - c0);
  }
  intpol.get_bspline_deriv(x, &ytmp, &yerrtmp, 1);
  return(x*x*(ytmp-yerrtmp) - c0);
}

double diff(double x){
    
  double ytmp;
  double yerrtmp;
  if ( x >=rrange ) {
    intpol.get_bspline_deriv(rrange, &ytmp, &yerrtmp, 1);
    return(x*x*ytmp - c0);
  }
  if ( x <=lrange ) {
    intpol.get_bspline_deriv(lrange, &ytmp, &yerrtmp, 1);
    return(x*x*ytmp - c0);
  }
  intpol.get_bspline_deriv(x, &ytmp, &yerrtmp, 1);
  return(x*x*ytmp - c0);
}

//Interpolates a given data set
int main (int argc, char ** argv){
  if ( argc < 2 || argc > 6){
    cout << "Usage: " << argv[0] << " data_file [order ncoeff] [minval maxval]" << endl;
    return -1;
  }
  intpol.setOrder(4);
  intpol.setNcoeffs(15);
  if (argc >= 3){
    intpol.setOrder(atoi(argv[2]));
  }
  if (argc >= 4){
    intpol.setOrder(atoi(argv[2]));
    intpol.setNcoeffs(atoi(argv[3]));
  }
  cout << "Read data..." << endl;
  if(argc == 6){
    intpol.read_data(argv[1], atof(argv[4]), atof(argv[5]));
  }else{
    intpol.read_data(argv[1]);
  }
  cout << "Fit..." << endl;
  intpol.fit();
  lrange=intpol.getLrange();
  rrange=intpol.getRrange();
  cout << "Print output..." << endl;
  intpol.print_bspline((char*)"intpol_r0.txt", lrange, rrange, 1000);
  cout << "Find r0" << endl;
  double r0 = zbrent(diff, lrange, rrange, 0.0000001);
  double r0_err_up = std::abs(zbrent(diff_err_up, lrange, rrange, 0.0000001)-r0);
  double r0_err_dn = std::abs(r0-zbrent(diff_err_dn, lrange, rrange, 0.0000001));
  double r0_err;
  if (r0_err_up > r0_err_dn){
    r0_err=r0_err_up;
  }else{
    r0_err=r0_err_dn;
  }
  cout << "r0 = " << r0 << " +- " << r0_err << endl;
  ofstream ofs("r0_spline.txt");
  ofs << "r_0=" << r0 << endl;
  ofs << "r_0_err=" << r0_err << endl;
  ofs << "order=" << intpol.getOrder() << endl;
  ofs << "Ncoeffs=" << intpol.getNcoeffs() << endl;
  ofs << "lrange=" << intpol.getLrange() << endl;
  ofs << "rrange=" << intpol.getRrange() << endl;
  ofs.close();

  return 0;
}
