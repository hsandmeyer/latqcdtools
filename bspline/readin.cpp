#include "readin.h"

using namespace std;
int readin(char filename[], vector<double> &x, vector<double> &y, vector<double> &yerr, double minval, double maxval){
  int i;        
  ifstream inf(filename);
  
  if(!inf.is_open()){
    cout << "readin error: Cannot open file '" << filename << "'!\n";
    throw -1;
  }   

  i = 0;
  double xtmp, ytmp, yerrtmp;
  string line;
  while(getline(inf, line)){
    istringstream iss(line);
    if(!(iss >> xtmp >> ytmp >> yerrtmp)){
      cout << "Readin error: Error while reading data in line " << i + 1 << "!\n";
      break;
    }
    //cerr <<  xtmp  << ' ' <<  ytmp  << ' ' <<  yerrtmp  << ' ' <<  endl;
    if (xtmp < maxval && xtmp >= minval){
      x.push_back(xtmp);
      y.push_back(ytmp);
      yerr.push_back(yerrtmp);
      i++;
    }
  }

  return(i);
}

