
#include "bspline.h"
#include "zbrent.h"
#define c1 1.00

bspline_interpolator intpol;
double lrange;
double rrange;

double diff_err_up(double x){
    
  double ytmp;
  double yerrtmp;
  if ( x >=rrange ) {
    intpol.get_bspline_deriv(rrange, &ytmp, &yerrtmp, 1);
    return(x*x*ytmp - c1);
  }
  if ( x <=lrange ) {
    intpol.get_bspline_deriv(lrange, &ytmp, &yerrtmp, 1);
    return(x*x*ytmp - c1);
  }
  intpol.get_bspline_deriv(x, &ytmp, &yerrtmp, 1);
  return(x*x*(ytmp+yerrtmp) - c1);
}

double diff_err_dn(double x){
    
  double ytmp;
  double yerrtmp;
  if ( x >=rrange ) {
    intpol.get_bspline_deriv(rrange, &ytmp, &yerrtmp, 1);
    return(x*x*ytmp - c1);
  }
  if ( x <=lrange ) {
    intpol.get_bspline_deriv(lrange, &ytmp, &yerrtmp, 1);
    return(x*x*ytmp - c1);
  }
  intpol.get_bspline_deriv(x, &ytmp, &yerrtmp, 1);
  return(x*x*(ytmp-yerrtmp) - c1);
}

double diff(double x){
    
  double ytmp;
  double yerrtmp;
  if ( x >=rrange ) {
    intpol.get_bspline_deriv(rrange, &ytmp, &yerrtmp, 1);
    return(x*x*ytmp - c1);
  }
  if ( x <=lrange ) {
    intpol.get_bspline_deriv(lrange, &ytmp, &yerrtmp, 1);
    return(x*x*ytmp - c1);
  }
  intpol.get_bspline_deriv(x, &ytmp, &yerrtmp, 1);
  return(x*x*ytmp - c1);
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
  intpol.print_bspline((char*) "intpol_r1.txt", lrange, rrange, 1000);
  cout << "Find r1" << endl;
  double r1 = zbrent(diff, lrange, rrange, 0.0000001);
  double r1_err_up = std::abs(zbrent(diff_err_up, lrange, rrange, 0.0000001)-r1);
  double r1_err_dn = std::abs(r1-zbrent(diff_err_dn, lrange, rrange, 0.0000001));
  double r1_err;
  if (r1_err_up > r1_err_dn){
    r1_err=r1_err_up;
  }else{
    r1_err=r1_err_dn;
  }
  cout << "r1 = " << r1 << " +- " << r1_err << endl;
  ofstream ofs("r1_spline.txt");
  ofs << "r_1=" << r1 << endl;
  ofs << "r_1_err=" << r1_err << endl;
  ofs << "order=" << intpol.getOrder() << endl;
  ofs << "Ncoeffs=" << intpol.getNcoeffs() << endl;
  ofs << "lrange=" << intpol.getLrange() << endl;
  ofs << "rrange=" << intpol.getRrange() << endl;
  ofs.close();

  return 0;
}
