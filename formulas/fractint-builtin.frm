comment {

These formulas attempt to replicate the functionality of the 'builtin'
formulas in Fractint - these are calculated using special-case C code
in Fractint, rather than using the formula interpreter, but in
Gnofract 4D we us the same compiler for all fractals. This makes
things simpler but means we don't support some of the special cases
like cellular automata.

In many cases these versions generalize the Fractint behavior.

}

; ant not supported

; barnsleyj1-3,barnsleym1-3: see Barnsley Type 1 - 3 in gf4d.frm

; bifurcation types not supported. These include:
; bif+sinpi, bif=sinpi, biflambda, bifmay, bifstewart, bifurcation 

; cellular not supported

; chip (orbit type) not supported

; circle not supported

; also includes cmplxmarksmand
cmplxmarksjul {
init:
	z = #zwpixel
loop:
	z = (#pixel ^ (@exp - 1) )* z*z + #pixel
bailout:
	@bailfunc(z) < @bailout
default:
float param bailout
	default = 4.0
endparam
complex param exp
	default = 1.0
endparam
float func bailfunc
	default = cmag
endfunc
}

; complexbasin not supported

; complexnewton: see gf4d.frm:newton

; diffusion not supported

; dynamic not supported

fn(z)+fn(pix) {
; to my mind this looks better with just z = #zwpixel as init, 
; but this is for fractint compat
init:
	z = #zwpixel + #pixel
loop:
	z = @fn1(z) + @factor * @fn2(#pixel)
bailout:
	@bailfunc(z) < @bailout
default:
float param bailout
	default = 64.0
endparam
complex param factor
	default = (1.0, 0.0)
endparam
complex func fn1
	default = sin
endfunc
complex func fn2
	default = sqr
endfunc
float func bailfunc
	default = cmag
endfunc
}

fn(z*z) {
init:
	z = #pixel
loop:
	z = @fn1(z*z) + #zwpixel
bailout:
	@bailfunc(z) < @bailout
default:
float param bailout
	default = 4.0
endparam
complex func fn1
	default = sin
endfunc
float func bailfunc
	default = cmag
endfunc
}

fn*fn {
init:
	z = #pixel
loop:
	z = @fn1(z) * @fn2(z) + #zwpixel
bailout:
	@bailfunc(z) < @bailout
default:
float param bailout
	default = 64.0
endparam
complex func fn1
	default = sin
endfunc
complex func fn2
	default = sqr
endfunc
float func bailfunc
	default = cmag
endfunc
}

fn*z+z {
init:
	z = #pixel
loop:
	z = @p1*@fn1(z)*z + @p2*z + #zwpixel
bailout:
	@bailfunc(z) < @bailout
default:
float param bailout
	default = 64.0
endparam
complex func fn1
	default = sin
endfunc
complex func fn2
	default = sqr
endfunc
float func bailfunc
	default = cmag
endfunc
param p1
	default= (1.0,0.0)
endparam
param p2
	default= (1.0,0.0)
endparam

}

fn+fn {
init:
	z = #pixel
loop:
	z2 = z
	z = @fn1(z2) + @fn2(z2) + #zwpixel
bailout:
	@bailfunc(z) < @bailout
default:
float param bailout
	default = 64.0
endparam
complex func fn1
	default = sin
endfunc
complex func fn2
	default = sqr
endfunc
float func bailfunc
	default = cmag
endfunc
}

; 'formula' is not needed by Gnofract 4D - that's what all of these are

; frothybasin not supported yet - need coloring per attractor

; gingerbreadman not supported - orbit type

; halley not supported - orbit type

; henon, hopalong not supported - orbit types

;hypercomplex, hypercomplexj - see gf4d:HyperMandel and HyperJulia

;icons, icons3d, ifs, ifs3d - orbit type

julfn+exp {
init:
	z = #pixel
loop:
	z = @fn1(z) + exp(z) + @c
bailout:
	@bailfunc(z) < @bailout
default:
float param bailout
	default = 4.0
endparam
float func bailfunc
	default = cmag
endfunc
complex param c
	default = (0, 0)
endparam
complex func fn1
	default = sin
endfunc
}

julfn+zsqrd {
init:
	z = #pixel
loop:
	z = @fn1(z) + sqr(z) + @c
bailout:
	@bailfunc(z) < @bailout
default:
float param bailout
	default = 4.0
endparam
float func bailfunc
	default = cmag
endfunc
complex func fn1
	default = sin
endfunc
complex param c
	default = (-0.5, 0.5)
endparam
}

; julia - see gf4d:Mandelbrot

julia(fn||fn) {
init:
	z = #pixel
loop:
	if |z| < @shift
		z = @fn1(z) + @c
	else
		z = @fn2(z) + @c
	endif
bailout:
	@bailfunc(z) < @bailout
default:
float param bailout
	default = 64.0
endparam
float func bailfunc
	default = cmag
endfunc
float param shift
	default= 8.0
endparam
complex func fn1
	default = sin
endfunc
complex param c
	default = (0, 0)
endparam
}

; julia4 - see gf4d:manzpower
