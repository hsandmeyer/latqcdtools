#include <math.h>
#include <stdlib.h>
#include <stdio.h>
#ifndef ZBRENT_H
#define ZBRENT_H
#define SIGN(a,b) ((b) >= 0.0 ? fabs(a) : -fabs(a))

/***************************************************************
Die Funktion zbrent liefert die Nullstelle der Funktion func
im Intervall [x1,x2] mit einer Genauigkeit von tol.
****************************************************************/
double zbrent(double func(const double), const double x1, const double x2, const double tol);
#endif
