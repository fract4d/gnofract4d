comment {

These formulas are based on those created by Tad Boniecki for Stephen
Ferguson's Sterling fractal program.  I can't guarantee the Gnofract
4D versions are exactly the same, I don't totally understand
Sterling's formula language. But they are interesting!

The originals can be found at http://www.soler7.com/Fractals/Sterling2Formulae.html
}

Formula_00 {
; a Nova variant
init:
	z = #pixel
loop:
	last = z
	
	zsin = sin(z)
	zcos = cos(z)
	z = z - (zsin * log(z) - tan(z))/ (z * (z * zcos - 2)) * #pixel
bailout:  
	|last - z| > @epsilon
default:
float param epsilon
	default = 0.01
endparam
magnitude=24
xyangle=-1.57
}

Formula_01 {
; a Nova variant
init:
	z = #pixel
loop:
	last = z
	
	z2 = z*z
        z3 = z2*z
        z = z-(z3*sin(z) - 1)/(7*z2*cos(z) - 1)+ #pixel
bailout:  
	|last - z| > @epsilon
default:
float param epsilon
	default = 0.01
endparam
magnitude=24
xyangle=-1.57
}

Formula_02 {
init:
	z = #pixel
; very similar to #6
loop:
	last = z  
        z2 = z*z
        z3 = z2*z
        z4 = z2*z2
        z5 = z4*z
        z6 = z5*z
        z7 = z6*z
        z8 = z7*z
        ;almost the old 49 for 3165 "no 1-3"
        z = z-(sin(z)/(1e-15+cos(z)))*(z8-z6-sin(z)-z-1)/(8*z7-6*z5-cos(z) - #pixel) 
bailout:  
	|last - z| > @epsilon
default:
float param epsilon
	default = 0.01
endparam
magnitude=24
xyangle=-1.57

}

Formula_03 {
init:
	z = #pixel
loop:
	last = z
        z2 = z*z
        z3 = z2*z
        z4 = z3*z
        z5 = z4*z
        z = last - ((last*sin(last)) - z3 + #pixel/(z5*cos(z)))/(#pixel/z5 + sin(z)*cos(z) - 100*z5)
        z = z - last*((z4 - z*sin(last) - #pixel)/(4*z3 - 3*z2 - 2*last -  last*cos(last) - #pixel))
        z = #pixel/z
        z = z*z - z
bailout:  
	|last - z| > @epsilon
default:
float param epsilon
	default = 0.01
endparam
magnitude=24
xyangle=-1.57


}
Formula_04 {
init:
	z = #pixel
loop:
	last = z
        z2 = z*z
        z3 = z2*z
        z4 = z2*z2
        z5 = z4*z
 
        ; a good one
        z = z - ((z5 - z4 + z3*sin(z) + #pixel)/(z4 + z3 - z2*cos(z) + #pixel))
bailout:
	t = |last - z |
	
	t > @epsilon && t < @bailout
default:
float param epsilon
	default = 0.01
endparam
float param bailout
	default = 4e10
endparam
magnitude=24
xyangle=-1.57
}
 
Formula_05 {
; Twister weed method
init:
	z = #pixel
	c2 = exp(z)
loop:

	last = z
     
	z2 = z*z
        z = z -(c2*z2*z2-1)/(z*z2*cos(z) - z*#pixel) + #pixel
bailout:
	t = |last - z |
	
	t > @epsilon && t < @bailout
default:
float param epsilon
	default = 0.01
endparam
float param bailout
	default = 4e10
endparam
magnitude=24
xyangle=-1.57
}


Formula_06 {
init:
	z = #pixel
loop:
	last = z
        z2 = z*z
        z3 = z2*z
        z4 = z2*z2
        z5 = z4*z
        z6 = z5*z
        z7 = z6*z
        z8 = z7*z
	zsin = sin(z)
	zcos = cos(z)

	if @mode == 1
	   ; almost the old 49 for 3165 "no 1-3"
           z = z-(zsin/(1e-15+zcos))*(z8-z6-zsin-z-1)/(8*z7-6*z5-zcos -#pixel)
	elseif @mode == 2
           ; current #8 - same red/blue flame as the above when enlarged
           z = z-(zsin/(1e-15+zcos))*(z8-zsin-z*#pixel)/(8*z7-zcos- #pixel)
 	else 
             z = z-(zsin/(1e-15+zcos))*(z8-z6-zsin-z-1)/(8*z7-6*z5-zcos) 
	endif
bailout:
	t = |last - z |
	
	t > @epsilon && t < @bailout
default:
float param epsilon
	default = 0.01
endparam
float param bailout
	default = 4e10
endparam
int param mode
    default = 0
endparam
magnitude=24
xyangle=-1.57
}

Formula_07 {
  ;Phoenix
  ;Nova variation method
init:
	z = #pixel
	z = sin(z)
  
loop:
	last = z
        z2 = z*z
        z3 = z2*z
        z4 = z2*z2
        zsin = sin(z) 
	zcos = cos(z)
        z = z -(#pixel*exp(z)*z4-z)*(z3 - zsin*log(z))/(z2*zcos + zsin*zsin*zsin)+#pixel
bailout:
	t = |last - z |
	
	t > @epsilon && t < @bailout
default:
float param epsilon
	default = 0.01
endparam
float param bailout
	default = 4e10
endparam
magnitude=24
xyangle=-1.57
}


Formula_08 {
; variant of old #49, 3152 to 3163
init:
	z = #pixel
loop:
	last = z 
        z2 = z*z
        z3 = z2*z
        z4 = z2*z2
        z5 = z4*z
        z6 = z5*z
        z7 = z6*z
        z8 = z7*z
	zsin = sin(z)
	zcos = cos(z) 
        z = z-(zsin/(1e-15+zcos))*(z8-zsin-z*#pixel)/(8*z7-zcos-#pixel)  
bailout:
	t = |last - z |
	
	t > @epsilon && t < @bailout
default:
float param epsilon
	default = 0.01
endparam
float param bailout
	default = 4e10
endparam
magnitude=24
xyangle=-1.57
}

Formula_09 {
; Nova variation method
init:
	z = #pixel
	z = sin(z)
loop:
	last = z
        z2 = z*z
        z3 = z2*z
        z4 = z2*z2
	zsin = sin(z)
	zcos = cos(z)

        ; alternative: z = z-(z4-z)/(4*z3-z)+ c  
    	z = z-(z3 - zsin*log(z))/(z2*zcos + zsin*zsin*zsin)+ #pixel
bailout:
	t = |last - z |
	
	t > @epsilon && t < @bailout
default:
float param epsilon
	default = 0.01
endparam
float param bailout
	default = 4e10
endparam
magnitude=24
xyangle=-1.57
}
 
Formula_10 {
; Nova variation method
init:
	z = #pixel
loop:
	last = z
	zsin = sin(z)
	zcos = cos(z)
        z2 = z*z
        z3 = z2*z
    	z = z-(z3*zsin-1)/(3*z2*zcos - zsin*zsin)+ #pixel
bailout:
	t = |last - z |
	
	t > @epsilon && t < @bailout
default:
float param epsilon
	default = 0.01
endparam
float param bailout
	default = 4e10
endparam
magnitude=24
xyangle=-1.57
}

Formula_11 {
init:
	z = -#pixel/3
	c = #pixel
loop:
	last = z
    z2 = z
    z1 = z*z
    zsin = sin(z)
    zcos = cos(z)
   
    z = z - (c*exp(z)*zsin * z1*log(z))/(z*z + c * zcos)
bailout:
	t = |last - z |
	
	t > @epsilon && t < @bailout
default:
float param epsilon
	default = 0.01
endparam
float param bailout
	default = 4e10
endparam
magnitude=24
xyangle=-1.57
}
 
Formula_18{
init:
	z = -#pixel/3
	c = #pixel
loop:
	last = z
    z2 = z
    z1 = z*z
    zsin = sin(z)
    zcos = cos(z)
   
    z= z - (c*exp(z)*zsin - z1*log(z))/(z*z + c*z - zcos)
bailout:
	t = |last - z |
	
	t > @epsilon && t < @bailout
default:
float param epsilon
	default = 0.01
endparam
float param bailout
	default = 4e10
endparam
magnitude=24
xyangle=-1.57
}

; can't be translated, don't know what dstrands is
;Formula_19
;{
;init:
;	z = -#pixel/3
;	c = #pixel
;loop:
;	last = z
;    z2 = z;  
;           
;            //ztan = tan(z)/bailout
;            zsin = sin(z); zcos = cos(z)
;            zcos = (1e-15+zcos)/v->dStrands
;            zsin = (1e-15+zsin)/v->dStrands
;   
;            z=z-(z*z*z+ c*exp(z) - z - z*log(z))/(3*z*z+2*c*z-zcos)
;   
;            zd = z-z2
;        temp = sum_sqrs_zd()
;  }
;      __real__ v->z = __real__ z
;      __imag__ v->z = __imag__ z
;  v->pXTemp[v->Iteration] = __real__ v->z
;      v->pYTemp[v->Iteration] = __imag__ v->z
;}

; OK 2599 - 2619
Formula_20{
;  /*
;  Solve the roots of the function.
;  Initialize z to one of the roots.
;  Apply Newton's method for solving roots.
;  f(z) = z - z/z'
; 
;  z   = z*z*z*z - z*z*z*c - z - c;  ; the function
;  z'  = 4*z*z*z - 3*z*z*c - 1;      ; 1st derivative
;  z'' = 12*z*z - 6*z*c;             ; 2nd derivative
; 
;  12*z*z = 6*z*c
;  z   = (6*z*c)/(12*z);             ; solve for z
;  z   = c/2
; 
;  */
 init:
	z = #pixel/2
	c = #pixel
loop:
	last =z  
    z2 = z
    z1 = z*z
 
            zsin = sin(z)
	    zcos = cos(z)
            ;zcos = (1e-15+zcos)/v->dStrands
            ;zsin = (1e-15+zsin)/v->dStrands
   
            z=z-(z1*c*exp(z) - z1*z*c - z - z*log(z))/(4*z*z1 - 3*z1*c - zcos)
bailout:
	t = |last - z |
	
	t > @epsilon && t < @bailout
default:
float param epsilon
	default = 0.01
endparam
float param bailout
	default = 4e10
endparam
magnitude=24
xyangle=-1.57
}
 

 
; OK 2584 - 2598
Formula_21{  
;  /*
;  Solve the roots of the function.
;  Initialize z to one of the roots.
;  Apply Newton's method for solving roots.
;  f(z) = z - z/z'
; 
;  z   = z*z*z*c + z*z + z + c;  ; the function
;  z'  = 3*z*z*c + 2*z + 1;      ; 1st derivative
;  z'' = 6*z*c   + 2;            ; 2nd derivative
; 
;  6*z*c = -2
;  z     = -2/(6*c);             ; solve for z
;  z     = -1/(3*c)
; 
;  */

init:
	z = #pixel
	c = #pixel 
        z = -1/(3*z)

loop:
	last = z

    z2 = z
    z1 = z*z
            zsin = sin(z)
	    zcos = cos(z)
    z =z-(z1*c + c*exp(z) + tan(z) - zcos)/(z1*z1*c + z*log(z) + c - zsin)

bailout:
	t = |last - z |
	
	t > @epsilon && t < @bailout
default:
float param epsilon
	default = 0.01
endparam
float param bailout
	default = 4e10
endparam
magnitude=24
xyangle=-1.57
}

; OK 2550 to 2583
Formula_22{  
; looks absolutely nothing like the sterling2 'formula_22' - no idea why
init:
	z = #pixel
	c = #pixel 
loop:
	last = z
    z2 = z
    z1 = z*z
    z  = z2
 
    zsin = sin(z)
    zcos = cos(z)
   
    z  = z-(z1*z*c * c * exp(z)*zsin)/(zsin + 2*zcos)

bailout:
	t = |last - z |
	
	t > @epsilon && t < @bailout
default:
float param epsilon
	default = 0.01
endparam
float param bailout
	default = 4e10
endparam
magnitude=24
xyangle=-1.57
}
 
; OK 2511 - 2542
Formula_23{
init:
z = #pixel
c = #pixel 
  z = -.5/z

loop:
	last = z
    z2 = z
    z1 = z*z
 
            ;ztan = tan(z)
            zsin = sin(z)
	    zcos = cos(z)
            ;zcos = (1e-15+zcos)/v->dStrands
            ;zsin = (1e-15+zsin)/v->dStrands
    
    z  = z-(z1*z1*c + z1*z + z + c - zsin)/(4*z1*z*c + 3*exp(z) - zcos)

bailout:
	t = |last - z |
	
	t > @epsilon && t < @bailout
default:
float param epsilon
	default = 0.01
endparam
float param bailout
	default = 4e10
endparam
magnitude=24
xyangle=-1.57
}

; OK 2479 - 2510
Formula_24{  ; testing
;  /*
;  Solve the roots of the function.
;  Initialize z to one of the roots.
;  Apply Newton's method for solving roots.
;  f(z) = z - z/z'
; 
;  z   = z*z*z + z*z*c + c;  ; the function
;  z'  = 3*z*z + 2*z*c    ;  ; 1st derivative
;  z'' = 6*z + 2*c        ;  ; 2nd derivative
; 
;      6*z = -2*c
;  z     = -2*c/6
; 
;  */
init: 
z = #pixel
c = #pixel 
  z = -z/3
 
loop:
	last = z
    z2 = z
    z1 = z*z
 
            ;ztan = tan(z)
            zsin = sin(z)	
	    zcos = cos(z)
            ;zcos = (1e-15+zcos)/v->dStrands
            ;zsin = (1e-15+zsin)/v->dStrands
   
    z  = z - (z1*exp(z) + z1*c + c - zsin)/(3*z1 + 2*z*c - zcos)

bailout:
	t = |last - z |
	
	t > @epsilon && t < @bailout
default:
float param epsilon
	default = 0.01
endparam
float param bailout
	default = 4e10
endparam
magnitude=24
xyangle=-1.57
}
 
; OK 2449 - 2478
Formula_25{  ; testing
init:
	z = #pixel
	c = #pixel

loop:
	last = z 
            z1 = z
            z2 = z*z
            z3 = z2*z
            z4 = z2*z2
            z5 = z4*z
            z6 = z5*z
            z7 = z6*z
            z8 = z7*z
            zsin = sin(z)
	    zcos = cos(z)
            z = z + (z5*zsin - c*z4*zcos)/((z5*log(z) + tan(z)) * tan(z))

bailout:
	t = |last - z |
	
	t > @epsilon && t < @bailout
default:
float param epsilon
	default = 0.01
endparam
float param bailout
	default = 4e10
endparam
magnitude=24
xyangle=-1.57
}

; OK 2434 - 2448
Formula_26{  ; testing
init:
	z = c = #pixel
loop:
	last = z

            z1 = z
            z2 = z*z
            z3 = z2*z
            z4 = z2*z2
            z5 = z4*z
            z6 = z5*z
            z7 = z6*z
            z8 = z7*z
            zsin = sin(z)
	    zcos = cos(z)
            z = z + exp(z) * (z5*zsin - c*z4*zcos)/((z5*log(z) + tan(z)) * tan(z))

bailout:
	t = |last - z |
	
	t > @epsilon && t < @bailout
default:
float param epsilon
	default = 0.01
endparam
float param bailout
	default = 4e10
endparam
magnitude=24
xyangle=-1.57
}

; OK but not too hot 2421 - 2433
Formula_27{  ; testing
; looks nothing like the sterling2 function, not clear why not

;  /*
;  Solve the roots of the function.
;  Initialize z to one of the roots.
;  Apply Newton's method for solving roots.
;  f(z) = z - z/z'
; 
;  z   = z*z*z*z*z*z*z + z*z*z*z*z*z*c + c;  ; the function
;  z'  = 7*z*z*z*z*z*z + 6*z*z*z*z*z*c    ;  ; 1st derivative
;  z'' = 42*z*z*z*z*z  + 30*z*z*z*z*c     ;  ; 2nd derivative
; 
;      42*z*z*z*z*z = -30*z*z*z*z*c
;  z            = -(30*z*z*z*z*c)/(42*z*z*z*z)
;  z            = -(15*c)/21
;  z            = -(5*c)/7
; 
;  */
 
init: 
z = #pixel
  c = #pixel 
  z = -(5*z)/7
 
loop:
	last = z
    z1 = z
    z2 = z1*z1
    z4 = z2*z2
    z5 = z4*z1
 
            zsin = sin(z)
	    zcos = cos(z)
            ;zcos = (1e-15+zcos)/v->dStrands
            ;zsin = (1e-15+zsin)/v->dStrands
   
            z  = (7*z5*z1 + 6*z5*c - zcos)  
            z  = z1-(z5*z2 + z5*z1*c + c - zsin)/z
            z = z + tan(z) * (z5*zsin - z4*zcos)/(z5 + tan(z)) * zsin * zcos * tan(z)

bailout:
	t = |last - z |
	
	t > @epsilon && t < @bailout
default:
float param epsilon
	default = 0.01
endparam
float param bailout
	default = 4e10
endparam
magnitude=24
xyangle=-1.57
}
 
; OK 2405 to 2420
Formula_28{  ; 9th order Newton Mset
;  /*
;  Solve the roots of the function.
;  Initialize z to one of the roots.
;  Apply Newton's method for solving roots.
;  f(z) = z - z/z'
; 
;  z   = z*z*z*z*z*z*z*z*z + z*z*z*z*z*z*z*z*c + c;  ; the function
;  z'  = 9*z*z*z*z*z*z*z*z + 8*z*z*z*z*z*z*z*c    ;  ; 1st derivative
;  z'' = 72*z*z*z*z*z*z*z  + 56*z*z*z*z*z*z*c     ;  ; 2nd derivative
; 
;      72*z*z*z*z*z*z*z = -56*z*z*z*z*z*z*c
;  z                = -(56*z*z*z*z*z*z*c)/(72*z*z*z*z*z*z)
;  z                = -(7*c)/9
; 
;  */

init: 
  z = #pixel
  c = #pixel 
  z = -(7*z)/9
 
loop:
	last = z
    z1 = z
    z2 = z*z
    z4 = z2*z2
    z5 = z2*z2*z
    z8 = z4*z4
 
            zsin = sin(z)
	    zcos = cos(z)
            ;zcos = (1e-15+zcos)/v->dStrands
            ;zsin = (1e-15+zsin)/v->dStrands
   
    ;z  = z-(z5*z4 + z8*c + c - zsin)/(9*z8 + 8*z5*z2*c - zcos)
    z = z - zsin/(log(z)*z8 + (exp(z) + c*z - zcos))

bailout:
	t = |last - z |
	
	t > @epsilon && t < @bailout
default:
float param epsilon
	default = 0.01
endparam
float param bailout
	default = 4e10
endparam
magnitude=24
xyangle=-1.57
}
 
; OK 2386 to 2404
Formula_29{  ; 13th order Newton Mset
;  /*
;  Solve the roots of the function.
;  Initialize z to one of the roots.
;  Apply Newton's method for solving roots.
;  f(z) = z - z/z'
; 
;  z   = z^13         + (z^12)*c + c;    ; the function
;  z'  = 13*(z^12)    + 12*(z^11)*c;     ; 1st derivative
;  z'' = 12*13*(z^11) + 11*12*(z^10)*c;  ; 2nd derivative
; 
;  12*13*(z^11) = -11*12*(z^10)*c
;  z            = -(11*12*(z^10)*c)/(12*13*(z^10))
;               = -(11*12*c)/(12*13)
;               = -11*c/13
; 
;  */
init: 
z = #pixel
c = #pixel 
  z = -(11*z)/13

loop:
	last = z 
    z1 = z
    z2 = z*z
    z4 = z2*z2
    z5 = z2*z2*z
    z8 = z4*z2
    z8 = z4
 
            zsin = sin(z)
	    zcos = cos(z)
            ;zcos = (1e-15+zcos)/v->dStrands
            ;zsin = (1e-15+zsin)/v->dStrands
   
    z = z - (log(z)*z8 + (exp(z) + c*z - zcos))/zsin

bailout:
	t = |last - z |
	
	t > @epsilon && t < @bailout
default:
float param epsilon
	default = 0.01
endparam
float param bailout
	default = 4e10
endparam
magnitude=24
xyangle=-1.57
}
 
; OK 2364 to 2380
Formula_30{  ; Testing again
init:
z = #pixel
c = #pixel 
      z = -(3*z)/5

loop:
	last = z
    z1 = z
    z2 = z*z
 
            zsin = sin(z)
	    zcos = cos(z)
            ;zcos = (1e-15+zcos)/v->dStrands
            ;zsin = (1e-15+zsin)/v->dStrands
   
    z = z - log(z)*(z2*z2*z + z2*z2*c + z + c - zsin)/(5*z2*exp(z) + 4*z2*z*c + 1 - zcos)

bailout:
	t = |last - z |
	
	t > @epsilon && t < @bailout
default:
float param epsilon
	default = 0.01
endparam
float param bailout
	default = 4e10
endparam
magnitude=24
xyangle=-1.57
}
 
; OK 2311 to 2341
Formula_31{  ; Newton Diamond
;  /*
;  Solve the roots of the function.
;  Initialize z to one of the roots.
;  Apply Newton's method for solving roots.
;  f(z) = z - z/z'
; 
;  z   = z^5      + (z^4)*c   + z + c;  ; the function
;  z'  = 5*(z^4)  + 4*(z^3)*c + 1;      ; 1st derivative
;  z'' = 20*(z^3) + 12*(z^2)*c;         ; 2nd derivative
; 
;  20*(z^3) = -12*(z^2)*c
;  z   = -(12*(z^2)*c)/(20*(z^2));       ; solve for z
;  z   = -(3*c)/5
; 
;  */
init:
z = #pixel
  c = #pixel 
  z = -(3*z)/5

loop:
	last =z
    z1 = z
    z2 = z*z
 
            zsin = sin(z)
	    zcos = cos(z)
            ;zcos = (1e-15+zcos)/v->dStrands
            ;zsin = (1e-15+zsin)/v->dStrands
   
    z = z - log(z)*(z2*z2*z + z2*z2*c + z + c - zsin)/(5*z2*z2 + 4*z2*z*c + 1 - zcos)

bailout:
	t = |last - z |
	
	t > @epsilon && t < @bailout
default:
float param epsilon
	default = 0.01
endparam
float param bailout
	default = 4e10
endparam
magnitude=24
xyangle=-1.57
}
 
; ok 2283 to 2310
Formula_32{  ; Newton Pentagon
;  /*
;  Solve the roots of the function.
;  Initialize z to one of the roots.
;  Apply Newton's method for solving roots.
;  f(z) = z - z/z'
; 
;  z   = z^6      + (z^5)*c   + z + c;  ; the function
;  z'  = 6*(z^5)  + 5*(z^4)*c + 1;      ; 1st derivative
;  z'' = 30*(z^4) + 20*(z^3)*c;         ; 2nd derivative
; 
;  30*(z^4) = -20*(z^3)*c
;  z   = -(20*(z^3)*c)/(30*(z^3));      ; solve for z
;  z   = -(2*c)/3
;  */
init: 
z = #pixel
c = #pixel 
  z = -(2*z)/3
loop:
	last = z
    z1 = z
    z2 = z*z
    z4 = z2*z2
 
            zsin = sin(z)
	    zcos = cos(z)
            ;zcos = (1e-15+zcos)/v->dStrands
            ;zsin = (1e-15+zsin)/v->dStrands
   
    ;z=z-(z4*z2 + z4*z*c + z + c - zsin)/(6*z4*z + 5*z4*c - zcos)
            z = z - z2*exp(z)+ c*zcos

bailout:
	t = |last - z |
	
	t > @epsilon && t < @bailout
default:
float param epsilon
	default = 0.01
endparam
float param bailout
	default = 4e10
endparam
magnitude=24
xyangle=-1.57
}
   
; OK 2270 to 2282
Formula_33{  ; Newton Hexagon
;  /*
;  Solve the roots of the function.
;  Initialize z to one of the roots.
;  Apply Newton's method for solving roots.
;  f(z) = z - z/z'
; 
;  z   = z^7      + (z^6)*c   + z + c;  ; the function
;  z'  = 7*(z^6)  + 6*(z^5)*c + 1;      ; 1st derivative
;  z'' = 42*(z^5) + 30*(z^4)*c;         ; 2nd derivative
; 
;  42*(z^5) = -30*(z^4)*c
;  z   = -(30*(z^4)*c)/(42*(z^4));      ; solve for z
;  z   = -(5*c)/7
; 
;  */
init: 
z = #pixel
c = #pixel 
  z = -(5*z)/7
loop:
	last = z
    z1 = z
    z2 = z*z
    z4 = z2*z2
 
            zsin = sin(z)
	    zcos = cos(z)
            ;zcos = (1e-15+zcos)/v->dStrands
            ;zsin = (1e-15+zsin)/v->dStrands
   
    z = z - (z4*z2*z + z4*z2*c + z*exp(z) + c - zsin)/(7*z4*z2 + 6*z4*z*c + exp(z)* - zcos)
   
            zd = z-z1

bailout:
	t = |last - z |
	
	t > @epsilon && t < @bailout
default:
float param epsilon
	default = 0.01
endparam
float param bailout
	default = 4e10
endparam
magnitude=24
xyangle=-1.57
}

; OK 2257 to 2269
Formula_34{  ; Newton Octagon
;  /*
; 
;  Solve the roots of the function.
;  Initialize z to one of the roots.
;  Apply Newton's method for solving roots.
;  f(z) = z - z/z'
; 
;  z   = z^9      + (z^8)*c   + z + c;  ; the function
;  z'  = 9*(z^8)  + 8*(z^7)*c + 1;      ; 1st derivative
;  z'' = 72*(z^7) + 56*(z^6)*c;         ; 2nd derivative
; 
;  72*(z^7) = -56*(z^6)*c
;  z   = -(56*(z^6)*c)/(72*(z^6));      ; solve for z
;  z   = -(7*c)/9
; 
;  */
init: 
z = #pixel
  c = #pixel 
  z = -(7*z)/9
loop:
	last = z
    z1 = z
    z2 = z*z
    z4 = z2*z2
 
            zsin = sin(z)
	    zcos = cos(z)
            ;zcos = (1e-15+zcos)/v->dStrands
            ;zsin = (1e-15+zsin)/v->dStrands
       
            z=z- exp(z)*(z4*z4*z + z4*z4*c + z + c - zsin)/(9*z4*z4 + 8*z4*z2*z*c + 1 - zcos)

bailout:
	t = |last - z |
	
	t > @epsilon && t < @bailout
default:
float param epsilon
	default = 0.01
endparam
float param bailout
	default = 4e10
endparam
magnitude=24
xyangle=-1.57
}

; keep 3147 to 3151
Formula_35{  ; Testing
init:
	z = #pixel
	c = #pixel

loop:
	last = z
            z1 = z
            z2 = z*z
            z3 = z2*z
            z4 = z2*z2
            z5 = z4*z
            z6 = z5*z
            z7 = z6*z
            z8 = z7*z
            zsin = sin(z)
	    zcos = cos(z)
 
            z = z-(zsin/(1e-15+zcos))*(z7-zsin-z*c-1)/(8*z7-zcos-c)  

bailout:
	t = |last - z |
	
	t > @epsilon && t < @bailout
default:
float param epsilon
	default = 0.01
endparam
float param bailout
	default = 4e10
endparam
magnitude=24
xyangle=-1.57
}
 
; keep 2207 to 2241
Formula_36{
init:
	z = #pixel
	c = #pixel
loop:
	last = z
            z1 = z
            z2 = z*z
            z3 = z2*z
            z4 = z2*z2
            z5 = z4*z
            z6 = z5*z
            z7 = z6*z
            z8 = z7*z
            zsin = sin(z)
	    zcos = cos(z)
            c2 = exp(z)
 
            z = z-(z5-z3-z2*zsin-c2*zsin)/(5*z3-z*z2-z2*zcos-1-zcos)+ c  

bailout:
	t = |last - z |
	
	t > @epsilon && t < @bailout
default:
float param epsilon
	default = 0.01
endparam
float param bailout
	default = 4e10
endparam
magnitude=24
xyangle=-1.57
}
 
; OK 2193-2206
Formula_37{
init:
	z= c = #pixel
loop:
	last = z
	z1 = z
            z2 = z*z
            z3 = z2*z
            z4 = z2*z2
            z5 = z4*z
            z6 = z5*z
            z7 = z6*z
            z8 = z7*z
            zsin = sin(z)
	    zcos = cos(z)
            z = z + (tan(z)*tan(z) - z4 + 7*c )/((z*zsin * zcos - z5)*tan(z))

bailout:
	t = |last - z |
	
	t > @epsilon && t < @bailout
default:
float param epsilon
	default = 0.01
endparam
float param bailout
	default = 4e10
endparam
magnitude=24
xyangle=-1.57
}

; OK 2184 to 2192
Formula_38{
init:
	z = c = #pixel
loop:
	last = z
	z1 = z
            z2 = z*z
            z3 = z2*z
            z4 = z2*z2
            z5 = z4*z
            z6 = z5*z
            z7 = z6*z
            z8 = z7*z
            zsin = sin(z)
	    zcos = cos(z)
            z = z - (z7*zcos - z4)/(z2*zsin -1 ) + c

bailout:
	t = |last - z |
	
	t > @epsilon && t < @bailout
default:
float param epsilon
	default = 0.01
endparam
float param bailout
	default = 4e10
endparam
magnitude=24
xyangle=-1.57
}
 
; keep 2149 - 2171
Formula_39{
init:
	z = c = #pixel
loop:
	last = z
            z1 = z
            z2 = z*z
            z3 = z2*z
            z4 = z2*z2
            z5 = z4*z
            z6 = z5*z
            z7 = z6*z
            z8 = z7*z
            zsin = sin(z)
	    zcos = cos(z)
   
            z = z-(z3-z2-z*zsin)/(z3-z2-z*zcos)+ c   

bailout:
	t = |last - z |
	
	t > @epsilon && t < @bailout
default:
float param epsilon
	default = 0.01
endparam
float param bailout
	default = 4e10
endparam
magnitude=24
xyangle=-1.57
}
           
; keep 2137 - 2148
Formula_40{
init:
	z = c = #pixel
loop:
	last = z
            z1 = z
            z2 = z*z
            z3 = z2*z
            z4 = z2*z2
            z5 = z4*z
            z6 = z5*z
            z7 = z6*z
            z8 = z7*z
            zsin = sin(z)
	    zcos = cos(z)
 
            z = z - (z - c)*(z + c)*(z*z + c)*c

bailout:
	t = |last - z |
	
	t > @epsilon && t < @bailout
default:
float param epsilon
	default = 0.01
endparam
float param bailout
	default = 4e10
endparam
magnitude=24
xyangle=-1.57
}
 
; keep 2123-2134
Formula_41{
init:
	z = c = #pixel
loop:
	last = z1 = z
            z2 = z*z
            z3 = z2*z
            z4 = z2*z2
            z5 = z4*z
            z6 = z5*z
            z7 = z6*z
            z8 = z7*z
            zsin = sin(z)
	    zcos = cos(z)
            z = z-(zsin/(1e-15+zsin))*(z8-z5*zsin-z*c-1)/(8*z7-6*z5-zcos-c)*(z5-z4*zsin-zsin*z*c-z);   
 
; was    z = z-(z5-z4*zsin-zsin*z*c-z)/(5*z4-5*z4*zcos-zcos*z*c-1);   

bailout:
	t = |last - z |
	
	t > @epsilon && t < @bailout
default:
float param epsilon
	default = 0.01
endparam
float param bailout
	default = 4e10
endparam
magnitude=24
xyangle=-1.57
}
 
; OK but weak 3123 - 3135
Formula_42{
init:
	z = c = #pixel
loop:
	last = z
            z2 = z*z
            z3 = z2*z
            z4 = z2*z2
            z5 = z4*z
            z6 = z5*z
            z7 = z6*z
            z8 = z7*z
            zsin = sin(z)
	    zcos = cos(z)
            z = z-(z3*zsin * zcos * zcos - c)/(z*exp(z) - zsin + z2);      ; change this

bailout:
	t = |last - z |
	
	t > @epsilon && t < @bailout
default:
float param epsilon
	default = 0.01
endparam
float param bailout
	default = 4e10
endparam
magnitude=24
xyangle=-1.57
}
 
; Similar to original 3087 - 3095
Formula_43{
init:
	z = c = #pixel

loop:
	last = z 
            z1 = z
            z2 = z*z
            z3 = z2*z
            z4 = z2*z2
            z5 = z4*z
            z6 = z5*z
            z7 = z6*z
            z8 = z7*z
            zsin = sin(z)
	    zcos = cos(z)
 
    z = z-(z5*zsin-z3*zsin-zsin*z*c-z)/(5*z4*zcos-z4*zcos-zcos*z2*c-1);       

bailout:
	t = |last - z |
	
	t > @epsilon && t < @bailout
default:
float param epsilon
	default = 0.01
endparam
float param bailout
	default = 4e10
endparam
magnitude=24
xyangle=-1.57
}
 
; keep 2050 - 2070
Formula_44{
init:
	z = c = #pixel

loop:
	last = z 
            z1 = z

            z2 = z*z
            z3 = z2*z
            z4 = z2*z2
            z5 = z4*z
            z6 = z5*z
            z7 = z6*z
            z8 = z7*z
            zsin = sin(z)
	zcos = cos(z)
   
; was      z = z-(z6-z5-z5*zsin-z4*zsin*c-zsin*z*c-z)/(6*z5-5*z4-z5*zcos-z4*zcos*c-zcos*z*c-1);   
 
            z = z-(z5*zsin-z4*zsin-z3*zsin-z2*zsin*c)/(4*z3*zcos-3*z2*zcos-z2*zcos*c);   

bailout:
	t = |last - z |
	
	t > @epsilon && t < @bailout
default:
float param epsilon
	default = 0.01
endparam
float param bailout
	default = 4e10
endparam
magnitude=24
xyangle=-1.57
}
 
; keep 2032-2049
Formula_45{
init:
	z = c = #pixel

loop:
	last = z 
            z1 = z
            z2 = z*z
            z3 = z2*z
            z4 = z2*z2
            z5 = z4*z
            z6 = z5*z
            z7 = z6*z
            z8 = z7*z
            zsin = sin(z)
	    zcos = cos(z)
 
            z = (z -(z*zsin * zcos - z5)*tan(z))/(zsin*z5 -zcos*(z2-zsin))

bailout:
	t = |last - z |
	
	t > @epsilon && t < @bailout
default:
float param epsilon
	default = 0.01
endparam
float param bailout
	default = 4e10
endparam
magnitude=24
xyangle=-1.57
}
 
; keep 1986 - 2028
Formula_46{
init:
	z = c = #pixel

loop:
	last = z 
            z1 = z
            z2 = z*z
            z3 = z2*z
            z4 = z2*z2
            z5 = z4*z
            z6 = z5*z
            z7 = z6*z
            z8 = z7*z
            zsin = sin(z)
	    zcos = cos(z)
 
            z = z-(z8+z6+z5-z5*zsin-z4*zcos*c-z)/(8*z7-6*z5-5*z4-z5*zcos*zcos-z4*zcos-1);   

bailout:
	t = |last - z |
	
	t > @epsilon && t < @bailout
default:
float param epsilon
	default = 0.01
endparam
float param bailout
	default = 4e10
endparam
magnitude=24
xyangle=-1.57
}

 
; keep 1957 - 1985
Formula_47{
init:
	z = c = #pixel

loop:
	last = z 
            z1 = z
            z2 = z*z
            z3 = z2*z
            z4 = z2*z2
            z5 = z4*z
            z6 = z5*z
            z7 = z6*z
            z8 = z7*z
            zsin = sin(z)
	    zcos = cos(z)
   
            z = z - (c + tan(z) + zcos*zsin)/(tan(z) + z4*zsin - z5)

bailout:
	t = |last - z |
	
	t > @epsilon && t < @bailout
default:
float param epsilon
	default = 0.01
endparam
float param bailout
	default = 4e10
endparam
magnitude=24
xyangle=-1.57
}
 
; 1921 - 1930 keep
Formula_48{
init:
	z = c = #pixel

loop:
	last = z 
            z1 = z
            z2 = z*z
            z3 = z2*z
            z4 = z2*z2
            z5 = z4*z
            z6 = z5*z
            z7 = z6*z
            z8 = z7*z
            zsin = sin(z)
	    zcos = cos(z)
 
            z = (z -(z*zsin * zcos - z5)*tan(z)/(tan(z)*tan(z) - z4 + 7*c))

bailout:
	t = |last - z |
	
	t > @epsilon && t < @bailout
default:
float param epsilon
	default = 0.01
endparam
float param bailout
	default = 4e10
endparam
magnitude=24
xyangle=-1.57
}
 
; modified 20 June 2007 produced # 1696 - 1713; to keep
Formula_49{
init:
	z = c = #pixel

loop:
	last = z 
            z1 = z
            z2 = z*z
            z3 = z2*z
            z4 = z2*z2
            z5 = z4*z
            z6 = z5*z
            z7 = z6*z
            z8 = z7*z
            zsin = sin(z)
	    zcos = cos(z)
 
            z = z-(zsin/(1e-15+zcos*zsin + c))*(z8-z6-zsin-z*c-1)/(8*z7-6*z5-zcos-c);   
; was         z = z-(zsin/(1e-15+zcos))*(z8-z6-zsin-z*c-1)/(8*z7-6*z5-zcos-c);   

bailout:
	t = |last - z |
	
	t > @epsilon && t < @bailout
default:
float param epsilon
	default = 0.01
endparam
float param bailout
	default = 4e10
endparam
magnitude=24
xyangle=-1.57
}
 
; modified June 2007; another version of #49; made # 1714 - 1733; To keep
Formula_50{
init:
	z = c = #pixel

loop:
	last = z 
            z1 = z

            z2 = z*z
            z3 = z2*z
            z4 = z2*z2
            z5 = z4*z
            z6 = z5*z
            z7 = z6*z
            z8 = z7*z
            zsin = sin(z)
	    zcos = cos(z)
 
; was      z = z-(z4-z3-z3-z2*zsin*c)/(4*z3-3*z2-z2*zcos*c);   
            z = z-(zsin/(1e-15+7*zcos*zsin + c))*(4*z8-z6-zsin-z*c-1)/(z7-6*z5-zcos-c);   

bailout:
	t = |last - z |
	
	t > @epsilon && t < @bailout
default:
float param epsilon
	default = 0.01
endparam
float param bailout
	default = 4e10
endparam
magnitude=24
xyangle=-1.57
}
 
; entirely new formula 27/6/7; used for # 1737 - 1778; to keep
Formula_51{
init:
	z = c = #pixel

loop:
	last = z 
            z1 = z

            z2 = z*z
            z3 = z2*z
            z4 = z2*z2
            z5 = z4*z
            z6 = z5*z
            z7 = z6*z
            z8 = z7*z
            zsin = sin(z)
	    zcos = cos(z)
 
; was      z = z-(z4*zsin-z3*zsin-z3*zsin-z2*zsin*c)/(4*z3-3*z2-z2*zcos*c);   
            z = z - c*(z8*zsin - z5 + z4*zcos)/(z6 - 27*z7 + z*c)

bailout:
	t = |last - z |
	
	t > @epsilon && t < @bailout
default:
float param epsilon
	default = 0.01
endparam
float param bailout
	default = 4e10
endparam
magnitude=24
xyangle=-1.57
}
 
; entirely new formula 10/7/7; used for # 1800 - 1828; to keep
Formula_52{
init:
	z = c = #pixel

loop:
	last = z 
            z1 = z

            z2 = z*z
            z3 = z2*z
            z4 = z2*z2
            z5 = z4*z
            z6 = z5*z
            z7 = z6*z
            z8 = z7*z
            zsin = sin(z)
	    zcos = cos(z)
 
; was      z = z-(z4*zsin-z3*zsin-z3*zsin-z2*zsin*c)/(4*z3*zcos-3*z2*zcos-z2*zcos*c);   
            z = z - c*(z*tan(z) - z4*zcos)/(zsin*z5 -zcos*(z2-zsin))

bailout:
	t = |last - z |
	
	t > @epsilon && t < @bailout
default:
float param epsilon
	default = 0.01
endparam
float param bailout
	default = 4e10
endparam
magnitude=24
xyangle=-1.57
}
 
; partially tested variant of new 52 22/7/7; 1837 - 1839 keep
Formula_53{
init:
	z = c = #pixel

loop:
	last = z 
            z1 = z
            z2 = z*z
            z3 = z2*z
            z4 = z2*z2
            z5 = z4*z
            z6 = z5*z
            z7 = z6*z
            z8 = z7*z
            zsin = sin(z)
	    zcos = cos(z)
 
; was         z = z-(z3*zsin-z2*zsin*c-1)/(3*z2*zcos-2*z*zcos*c);   
            z = z + tan(z)*tan(z)

bailout:
	t = |last - z |
	
	t > @epsilon && t < @bailout
default:
float param epsilon
	default = 0.01
endparam
float param bailout
	default = 4e10
endparam
magnitude=24
xyangle=-1.57
}

; 1847 - 1860
Formula_54{
init:
	z = c = #pixel

loop:
	last = z 
            z1 = z
            z2 = z*z
            z3 = z2*z
            z4 = z2*z2
            z5 = z4*z
            z6 = z5*z
            z7 = z6*z
            z8 = z7*z
            zsin = sin(z)
	    zcos = cos(z)
 
            z = z + tan(z)*tan(z) * (z + z*tan(z)) * z2*zsin * z3*zcos * z8*tan(z)/(z5*zsin - z4)

bailout:
	t = |last - z |
	
	t > @epsilon && t < @bailout
default:
float param epsilon
	default = 0.01
endparam
float param bailout
	default = 4e10
endparam
magnitude=24
xyangle=-1.57
}

; 1862 - 1903
Formula_55{
init:
	z = c = #pixel

loop:
	last = z 
            z1 = z
            z2 = z*z
            z3 = z2*z
            z4 = z2*z2
            z5 = z4*z
            z6 = z5*z
            z7 = z6*z
            z8 = z7*z
            zsin = sin(z)
	    zcos = cos(z)
            z = z + tan(z) * (z5 + tan(z)) * zsin * zcos * tan(z)/(z5*zsin - z4*zcos)

bailout:
	t = |last - z |
	
	t > @epsilon && t < @bailout
default:
float param epsilon
	default = 0.01
endparam
float param bailout
	default = 4e10
endparam
magnitude=24
xyangle=-1.57
}
 

