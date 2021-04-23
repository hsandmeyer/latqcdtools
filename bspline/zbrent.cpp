#include "zbrent.h"

#define SIGN(a,b) ((b) >= 0.0 ? fabs(a) : -fabs(a))

/***************************************************************
  Die Funktion zbrent liefert die Nullstelle der Funktion func
  im Intervall [x1,x2] mit einer Genauigkeit von tol.
 ****************************************************************/
double zbrent(double func(const double), const double x1, const double x2, const double tol)
{
    const int ITMAX=100;
    const double EPSILON=3.0e-14;
    int iter;
    double a=x1,b=x2,c=x2,d,e,min1,min2;
    double fa=func(a),fb=func(b),fc,p,q,r,s,tol1,xm;

    if ((fa > 0.0 && fb > 0.0) || (fa < 0.0 && fb < 0.0))
    {
	printf("Root must be bracketed in zbrent");
	exit(1);
    }

    fc=fb;
    for (iter=0;iter<ITMAX;iter++) {
	if ((fb > 0.0 && fc > 0.0) || (fb < 0.0 && fc < 0.0)) {
	    c=a;
	    fc=fa;
	    e=d=b-a;
	}
	if (fabs(fc) < fabs(fb)) {
	    a=b;
	    b=c;
	    c=a;
	    fa=fb;
	    fb=fc;
	    fc=fa;
	}
	tol1=2.0*EPSILON*fabs(b)+0.5*tol;
	xm=0.5*(c-b);
	if (fabs(xm) <= tol1 || fb == 0.0) return b;
	if (fabs(e) >= tol1 && fabs(fa) > fabs(fb)) {
	    s=fb/fa;
	    if (a == c) {
		p=2.0*xm*s;
		q=1.0-s;
	    } else {
		q=fa/fc;
		r=fb/fc;
		p=s*(2.0*xm*q*(q-r)-(b-a)*(r-1.0));
		q=(q-1.0)*(r-1.0)*(s-1.0);
	    }
	    if (p > 0.0) q = -q;
	    p=fabs(p);
	    min1=3.0*xm*q-fabs(tol1*q);
	    min2=fabs(e*q);
	    if (2.0*p < (min1 < min2 ? min1 : min2)) {
		e=d;
		d=p/q;
	    } else {
		d=xm;
		e=d;
	    }
	} else {
	    d=xm;
	    e=d;
	}
	a=b;
	fa=fb;
	if (fabs(d) > tol1)
	    b += d;
	else
	    b += SIGN(tol1,xm);
	fb=func(b);
	//printf("%d %lf\n", iter, b);
    }
    printf("Maximum number of iterations exceeded in zbrent");
    exit(1);
    return 0.0;
}
