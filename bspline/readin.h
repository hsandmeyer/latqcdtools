#include <vector>
#include <string>
#include <iostream>
#include <fstream>
#include <exception>
#include <sstream>
#include <limits>

#ifndef READIN_H
#define READIN_H

using namespace std;
//int readin(char filename[], vector<double> &x, vector<double> &y, vector<double> &yerr);
int readin(char filename[], vector<double> &x, vector<double> &y, vector<double> &yerr, double minval=std::numeric_limits<double>::lowest(), double maxval=std::numeric_limits<double>::max());
#endif
