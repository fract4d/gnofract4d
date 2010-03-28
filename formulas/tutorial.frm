MyFormula1 {
; First example formula - this produces a variant on the Mandelbrot set
init:
    z = 0
    c = #pixel
loop:
    z = z*z*c + c*c
bailout:
    |z| < 4.0
}

MyFormula2 {
; Second example - introduce 4D
init:
    z = #zwpixel ; take initial value from 4D position
    c = #pixel
loop:
    z = z*z*c + c*c
bailout:
    |z| < 4.0
}

MyFormula3 {
; Third example - add a parameter
init:
    z = #zwpixel
    c = #pixel
loop:
    z = @myfunc(z*z*c) + @factor * z + c*c
bailout:
    |z| < 4
default:
param factor
	default = (1.0,0.5)
endparam
}
