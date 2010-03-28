/* a heavily modified version of a vector library originally 
   from Graphics Gems */

#ifndef _VECTORS_H_
#define _VECTORS_H_

#include <math.h>
// forward declarations 
template<class T> class vec4;
template<class T> class mat4;

enum {VX, VY, VZ, VW};		    // axes

// 4 element vector

template<class T>
class vec4
{
public:
	T n[4];

	// Constructors

	vec4() {};
	vec4(const T& x, const T& y, const T& z, const T& w) {
		n[VX] = x; n[VY] = y; n[VZ] = z; n[VW] = w;
	};
	explicit vec4(const T& d) {  
		n[VX] = n[VY] = n[VZ] = n[VW] = d; 
	};

	// copy constructor
	vec4(const vec4& v) {
		n[VX] = v.n[VX]; n[VY] = v.n[VY]; 
		n[VZ] = v.n[VZ]; n[VW] = v.n[VW];
	};

        // Assignment operators

	// assignment of a vec4
	vec4& operator	= ( const vec4& v ) {
		n[VX] = v.n[VX]; n[VY] = v.n[VY]; 
		n[VZ] = v.n[VZ]; n[VW] = v.n[VW];
		return *this;
	};

	// In-place update operators

	// incrementation by a vec4
	vec4& operator += ( const vec4& v ) { 
		n[VX] += v.n[VX]; n[VY] += v.n[VY]; 
		n[VZ] += v.n[VZ]; n[VW] += v.n[VW];
		return *this; 
	};

	// decrementation by a vec4
	vec4& operator -= ( const vec4& v ) { 
		n[VX] -= v.n[VX]; n[VY] -= v.n[VY]; 
		n[VZ] -= v.n[VZ]; n[VW] -= v.n[VW];
		return *this; 
	};

	// multiplication by a scalar
	vec4& operator *= ( const T& d ) { 
		n[VX] *= d; n[VY] *= d; n[VZ] *= d; n[VW] *= d; 
		return *this; 
	};

	// division by a constant
	vec4& operator /= ( const T& d ) { 
		n[VX] /= d; n[VY] /= d; 
		n[VZ] /= d; n[VW] /= d; 
		return *this; 
	};

	// indexing
	T& operator [] ( int i) {
		return n[i];
	};

	T mag() {
	  return n[VX]*n[VX] + n[VY]*n[VY] + n[VZ]*n[VZ] + n[VW]*n[VW];
	}
	
	void norm() {
	  T norm = sqrt(mag());
	  n[VX] /= norm;
	  n[VY] /= norm;
	  n[VZ] /= norm;
	  n[VW] /= norm;
	}
};

// vec4 friends

template<class T>
vec4<T> operator - (const vec4<T>& a) { 
	return vec4<T>(-a.n[VX],-a.n[VY],-a.n[VZ],-a.n[VW]); 
}

template<class T>
vec4<T> operator + (const vec4<T>& a, const vec4<T>& b) { 
	return vec4<T>(a.n[VX] + b.n[VX], a.n[VY] + b.n[VY], 
		       a.n[VZ] + b.n[VZ], a.n[VW] + b.n[VW]); 
}

template<class T>
vec4<T> operator - (const vec4<T>& a, const vec4<T>& b) {  
	return vec4<T>(a.n[VX] - b.n[VX], a.n[VY] - b.n[VY], 
		       a.n[VZ] - b.n[VZ], a.n[VW] - b.n[VW]); 
}

template<class T, class U>
vec4<T> operator * (const vec4<T>& a, const U& d) { 
	return vec4<T>(d*a.n[VX], d*a.n[VY], d*a.n[VZ], d*a.n[VW] ); 
}

template<class T, class U>
vec4<T> operator * (const U& d, const vec4<T>& a) { 
	return a*d; 
}

template<class T>
vec4<T> operator * (const mat4<T>& a, const vec4<T>& v) {
    #define ROWCOL(i) a.v[i].n[0]*v.n[VX] + a.v[i].n[1]*v.n[VY] \
    + a.v[i].n[2]*v.n[VZ] + a.v[i].n[3]*v.n[VW]
    return vec4<T>(ROWCOL(0), ROWCOL(1), ROWCOL(2), ROWCOL(3));
    #undef ROWCOL
}

template<class T>
vec4<T> operator * (const vec4<T>& v, mat4<T>& a) { 
	return a.transpose() * v; 
}

template<class T>
T operator * (const vec4<T>& a, const vec4<T>& b) { 
	return (a.n[VX]*b.n[VX] + a.n[VY]*b.n[VY] + 
		a.n[VZ]*b.n[VZ] + a.n[VW]*b.n[VW]);
}

template<class T, class U>
vec4<T> operator / (const vec4<T>& a, const U& d) { 
	return vec4<T>(a.n[VX]/d, a.n[VY]/d, a.n[VZ]/d, a.n[VW]/d);
}

template<class T>
bool operator == (const vec4<T>& a, const vec4<T>& b) { 
	return (a.n[VX] == b.n[VX]) && (a.n[VY] == b.n[VY]) && 
		(a.n[VZ] == b.n[VZ]) && (a.n[VW] == b.n[VW]); 
}

template<class T>
bool operator != (const vec4<T>& a, const vec4<T>& b) { 
	return !(a == b); 
}

template<class T>
void swap(vec4<T>& a, vec4<T>& b) { 
	vec4<T> tmp(a); a = b; b = tmp; 
}

template<class T>
vec4<T> prod(const vec4<T>& a, const vec4<T>& b) { 
	return vec4<T>(a.n[VX] * b.n[VX], a.n[VY] * b.n[VY], 
		       a.n[VZ] * b.n[VZ], a.n[VW] * b.n[VW]); 
}

// 4 x 4 matrix

template<class T>
class mat4
{
protected:



public:
	vec4<T> v[4];

        // Constructors

	mat4() { };
	mat4(const vec4<T>& v0, const vec4<T>& v1, 
	     const vec4<T>& v2, const vec4<T>& v3) {
		v[0] = v0; v[1] = v1; v[2] = v2; v[3] = v3;
	};

	explicit mat4(const T& d) {
		v[0] = v[1] = v[2] = v[3] = vec4<T>(d);
	};

	// copy constructor
	mat4(const mat4& m) {
		v[0] = m.v[0]; v[1] = m.v[1]; v[2] = m.v[2]; v[3] = m.v[3];
	};
	
        // Assignment operators
	
	mat4& operator	= ( const mat4& m ) { 
		v[0] = m.v[0]; v[1] = m.v[1]; v[2] = m.v[2]; v[3] = m.v[3];
		return *this; 
	};	    

	// In-place update operators

	// incrementation by a mat4
	mat4& operator += ( const mat4& m ) { 
		v[0] += m.v[0]; v[1] += m.v[1]; v[2] += m.v[2]; v[3] += m.v[3];
		return *this; 
	};

	// decrementation by a mat4
	mat4& operator -= ( const mat4& m ) { 
		v[0] -= m.v[0]; v[1] -= m.v[1]; v[2] -= m.v[2]; v[3] -= m.v[3];
		return *this; 
	};

	// multiplication by a scalar
	mat4& operator *= ( const T& d ) { 
		v[0] *= d; v[1] *= d; v[2] *= d; v[3] *= d; return *this;
	};

	// division by a scalar
	mat4& operator /= ( const T& d ) {
		v[0] /= d; v[1] /= d; v[2] /= d; v[3] /= d; return *this;
	};

	// indexing
	vec4<T>& operator [] ( int i) {
		return v[i];
	};		

        // special functions

	mat4 transpose() {
		return mat4(vec4<T>(v[0][0], v[1][0], v[2][0], v[3][0]),
			    vec4<T>(v[0][1], v[1][1], v[2][1], v[3][1]),
			    vec4<T>(v[0][2], v[1][2], v[2][2], v[3][2]),
			    vec4<T>(v[0][3], v[1][3], v[2][3], v[3][3]));

	};
#if 0
	mat4 inverse() {
		// As a evolves from original mat into identity, 
		// b evolves from identity into inverse(a) 
		mat4 a(*this), b(identity3D());   
		int i, j, i1;

		// Loop over cols of a from left to right, 
                // eliminating above and below diag
		for (j=0; j<4; j++) {
			// Find largest pivot in column j among rows j..3
			i1 = j;		    // Row with largest pivot candidate
			for (i=j+1; i<4; i++) {
				if (fabs(a.v[i].n[j]) > fabs(a.v[i1].n[j]))
					i1 = i;
			}

			// Swap rows i1 and j in a and b to put pivot on diagonal
			swap(a.v[i1], a.v[j]);
			swap(b.v[i1], b.v[j]);

			// Scale row j to have a unit diagonal
			if (a.v[j].n[j]==0.)
				VECTOR_ERROR("mat4::inverse: singular matrix; can't invert\n");
			b.v[j] /= a.v[j].n[j];
			a.v[j] /= a.v[j].n[j];

			// Eliminate off-diagonal elems in col j of a, doing identical ops to b
			for (i=0; i<4; i++)
				if (i!=j) {
					b.v[i] -= a.v[i].n[j]*b.v[j];
					a.v[i] -= a.v[i].n[j]*a.v[j];
				}
		}
		return b;
		
	};				
#endif

};

// mat4 friends

template<class T>
mat4<T> operator - (const mat4<T>& a) { 
	return mat4<T>(-a.v[0], -a.v[1], -a.v[2], -a.v[3]); 
}

template<class T>
mat4<T> operator + (const mat4<T>& a, const mat4<T>& b) { 
	return mat4<T>(a.v[0] + b.v[0], a.v[1] + b.v[1], 
		       a.v[2] + b.v[2],  a.v[3] + b.v[3]);
}

template<class T>
mat4<T> operator - (const mat4<T>& a, const mat4<T>& b) { 
	return mat4<T>(a.v[0] - b.v[0], a.v[1] - b.v[1], 
		       a.v[2] - b.v[2], a.v[3] - b.v[3]); 
}

template<class T>
mat4<T> operator * (const mat4<T>& ca, const mat4<T>& cb) {
	mat4<T>& a = const_cast<mat4<T>&>(ca);
	mat4<T>& b = const_cast<mat4<T>&>(cb);
    #define ROWCOL(i, j) a.v[i].n[0]*b.v[0].n[j] + a.v[i].n[1]*b.v[1].n[j] + \
    a.v[i].n[2]*b.v[2].n[j] + a.v[i].n[3]*b.v[3].n[j]
    return mat4<T>(
    vec4<T>(ROWCOL(0,0), ROWCOL(0,1), ROWCOL(0,2), ROWCOL(0,3)),
    vec4<T>(ROWCOL(1,0), ROWCOL(1,1), ROWCOL(1,2), ROWCOL(1,3)),
    vec4<T>(ROWCOL(2,0), ROWCOL(2,1), ROWCOL(2,2), ROWCOL(2,3)),
    vec4<T>(ROWCOL(3,0), ROWCOL(3,1), ROWCOL(3,2), ROWCOL(3,3))
    );
    #undef ROWCOL
}

template<class T, class U>
mat4<T> operator * (const mat4<T>& a, const U& d) { 
	return mat4<T>(a.v[0] * d, a.v[1] * d, a.v[2] * d, a.v[3] * d); 
}

template<class T, class U>
mat4<T> operator * (const U& d, const mat4<T>& a) { 
	return a*d; 
}

template<class T, class U>
mat4<T> operator / (const mat4<T>& a, const U& d) { 
	return mat4<T>(a.v[0] / d, a.v[1] / d, a.v[2] / d, a.v[3] / d); 
}

template<class T>
bool operator == (const mat4<T>& a, const mat4<T>& b) { 
	return ((a.v[0] == b.v[0]) && (a.v[1] == b.v[1]) && 
		(a.v[2] == b.v[2]) && (a.v[3] == b.v[3])); 
}

template<class T>
bool operator != (const mat4<T>& a, const mat4<T>& b) { 
	return !(a == b); 
}

template<class T>
void swap(mat4<T>& a, mat4<T>& b) { 
	mat4<T> tmp(a); a = b; b = tmp; 
}

/****************************************************************
*								*
*	       2D functions and 3D functions			*
*								*
****************************************************************/

template<class T>
mat4<T> identity3D(T size = 1.0, T zero=0.0)
{
	return mat4<T>(
		vec4<T>(size,zero,zero,zero),
		vec4<T>(zero,size,zero,zero),
		vec4<T>(zero,zero,size,zero),
		vec4<T>(zero,zero,zero,size));
}

template<class T>
mat4<T> perspective3D(const T& d);


// rotations about a plane in 4D; used for Mandelbrot weirdness
template<class T>
mat4<T> rotXY(const T& theta, T one=1.0, T zero=0.0)
{
    T c = cos((T)theta), s = sin((T)theta);
    return mat4<T>(
        vec4<T>(   c,  -s,zero,zero),
        vec4<T>(   s,   c,zero,zero),
        vec4<T>(zero,zero, one,zero),
        vec4<T>(zero,zero,zero, one));
}

template<class T>
mat4<T> rotXZ(const T& theta, T one=1.0, T zero=0.0)
{
    T c = cos(theta), s = sin(theta);
    return mat4<T>(
        vec4<T>(   c,zero,   s,zero),
        vec4<T>(zero, one,zero,zero),
        vec4<T>(  -s,zero,   c,zero),
        vec4<T>(zero,zero,zero, one));
}

template<class T>
mat4<T> rotXW(const T& theta, T one=1.0, T zero=0.0)
{
    T c = cos(theta), s = sin(theta);
    return mat4<T>(
        vec4<T>(   c,zero,zero,   s),
        vec4<T>(zero, one,zero,zero),
        vec4<T>(zero,zero, one,zero),
        vec4<T>(  -s,zero,zero,   c));
}

template<class T>
mat4<T> rotYZ(const T& theta, T one=1.0, T zero=0.0)
{
    T c = cos(theta), s = sin(theta);
    return mat4<T>(
        vec4<T>( one,zero,zero,zero),
        vec4<T>(zero,   c,  -s,zero),
        vec4<T>(zero,   s,   c,zero),
        vec4<T>(zero,zero,zero, one));
}

template<class T>
mat4<T> rotYW(const T& theta, T one=1.0, T zero=0.0)
{
    T c = cos(theta), s = sin(theta);
    return mat4<T>(
        vec4<T>( one,zero,zero,zero),
        vec4<T>(zero,   c,zero,   s),
        vec4<T>(zero,zero, one,zero),
        vec4<T>(zero,  -s,zero,   c));
}

template<class T>
mat4<T> rotZW(const T& theta, T one=1.0, T zero=0.0)
{
    T c = cos(theta), s = sin(theta);
    return mat4<T>(
        vec4<T>( one,zero,zero,zero),
        vec4<T>(zero, one,zero,zero),
        vec4<T>(zero,zero,   c,  -s),
        vec4<T>(zero,zero,   s,   c));
}

typedef double d;
typedef vec4<d> dvec4;
typedef mat4<d> dmat4;

#endif 
