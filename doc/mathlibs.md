
# Notes on Math Libraries

I went through the list of all arbitrary precision math libs at https://en.wikipedia.org/wiki/List_of_arbitrary-precision_arithmetic_software to see which might work best for Gnofract 4D.

**Criteria**:
- Fast
- Supports floating point
- Target numbers up to 4000 bits (?)
- Need trig and other elementary functions


**Library** | **Suitable** | **Notes**
--- | --- | ---
[Boost](https://www.boost.org/doc/libs/1_73_0/libs/multiprecision/doc/html/boost_multiprecision/intro.html) | Investigate | C++ wrapper/front-end for several libs (" GMP, MPFR, MPIR, MPC, TomMath")
[TTMath](https://www.ttmath.org/) | Not now | Appears unmaintained 1person project
[LibBF](https://bellard.org/libbf/benchmark.html) | No | 'slower than GMP for less than 1e9 digits'
[GMP]() | Maybe | For floats, provides mpf but suggests using mpfr instead
[MPFR](https://www.mpfr.org/) | Yes | We have a sample already
[CLN](https://ginac.de/CLN/cln.html) | Maybe | Says 'using GNU MP (internally) can provide quite a boost'
[ARPREC](http://crd-legacy.lbl.gov/~dhbailey/mpdist/) | No | Appears FORTRAN-focused
[MAPM](https://github.com/LuaDist/mapm) | No | Appears unmaintained
[CORE](https://cs.nyu.edu/exact/core_pages/index.html) | No | Academically-focused, all about exact computation
[LEDA](https://www.algorithmic-solutions.com/index.php/products/leda-for-c)  | No | Proprietary
[CGAL](https://www.cgal.org/) | No | Seems mostly focused on geometry, couldn't even find arbitrary precision math on web site
[MPIR](http://mpir.org/#about) | Yes | GMP Fork. Info seems a bit sparse.
[FLINT](http://www.flintlib.org/) | Maybe | Looks like it uses MPFR internally
[Arb](http://arblib.org/) | No | Believe the 'ball arithmetic' approach will be slower






