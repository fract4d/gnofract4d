comment {

 This is a tweaked version of fractint.frm, with most formulas tweaked to 
 take advantage of Gnofract 4D's "4D" options (and hence, to have both
 Mandelbrot and Julia versions in the same formula).

 The formulas at the beginning of this file are from Mark Peterson, who
 built Fractint's fractal interpreter feature.  
 The rest are grouped by contributor.

 Formulas by unidentified authors are grouped at the end.

 All contributions are assumed to belong to the public domain.
 }

{--- MARK PETERSON -------------------------------------------------------}

InvMandel (XAXIS) {; Mark Peterson
  c = z = 1 / pixel:
   z = sqr(z) + c
    |z| <= 4
  }

DeltaLog(XAXIS) {; Mark Peterson
  z = pixel, c = log(pixel):
   z = sqr(z) + c
    |z| <= 4
  }

Newton4(XYAXIS) {; Mark Peterson
  ; Note that floating-point is required to make this compute accurately
  z = pixel, Root = 1:
   z3 = z*z*z
   z4 = z3 * z
   z = (3 * z4 + Root) / (4 * z3)
    .004 <= |z4 - Root|
  }

{--- DON ARCHER ----------------------------------------------------------}

DAFRM01 {;  Don Archer, 1993
  z = pixel :
   z = z ^ (z - 1) * (fn1(z) + pixel)
    |z| <= 4
  }

DAFRM07 {
  z = pixel, c = p1 :
   z = z ^ (z - 1) * fn1(z) + pixel
    |z| <= 4
  }

DAFRM09 {
  z = pixel, c = z + z^ (z - 1):
   tmp = fn1(z)
   real(tmp) = real(tmp) * real(c) - imag(tmp) * imag(c)
   imag(tmp) = real(tmp) * imag(c) - imag(tmp) * real(c)
   z = tmp + pixel + 12
    |z| <= 4
  }

dafrm21 {
  z = pixel:
   x = real(z), y = imag(z)
   x1 = -fn1((x*x*x + y*y*y - 1) - 6*x)*x/(2*x*x*x + y*y*y - 1)
   y1 = -fn2((x*x*x + y*y*y - 1) + 6*x)*y/(2*x*x*x + y*y*y - 1)
   x2 = x1*x1*x1 - y1*y1*y1 + p1 + 5
   y2 = 4*x*y - 18
   z = x2 + flip(y2)
    |z| <= 100
  }

3daMand01 {; Mandelbrot/Zexpe via Lee Skinner
  ; based on 4dFRACT.FRM by Gordon Lamb (CIS: 100272,3541)
  z=real(pixel)+flip(imag(pixel)*p1)
  c=p2+p1*real(pixel)+flip(imag(pixel)):
   z=z^2.71828182845905 + c
    |z|<=100
  }

3daMand02 {; Mandelbrot/Xexpe/Feigenbaum's alpha constant=exponent
  ; based on 4dFRACT.FRM by Gordon Lamb (CIS: 100272,3541)
  z=real(pixel)+flip(imag(pixel)*p1)
  c=p2+p1*real(pixel)+flip(imag(pixel)):
   z=z^2.502907875095 + c
    |z|<=100
  }

{--- RON BARNETT ---------------------------------------------------------}

Julike { ; Ron Barnett, 1993
  ; a Julia function based upon the Ikenaga function
  z = Pixel:
   z = z*z*z + (P1-1)*z - P1
    |z| <= 4
  }

Mask { ; Ron Barnett, 1993
  ; try fn1 = log, fn2 = sinh, fn3 = cosh
  ;P1 = (0,1), P2 = (0,1)
  ;Use floating point
  z = fn1(pixel):
   z = P1*fn2(z)^2 + P2*fn3(z)^2 + pixel
    |z| <= 4
  }

JMask {  ; Ron Barnett, 1993
  z = fn1(pixel):
   z = P1*fn2(z)^2 + P2
    |z| <= 4
  }

PseudoZeePi {; Ron Barnett, 1993
  z = pixel:
   x = 1-z^p1;
   z = z*((1-x)/(1+x))^(1/p1) + p2
    |z| <= 4
  }

ZeePi {  ; Ron Barnett, 1993
  ; This Julia function is based upon Ramanujan's iterative
  ; function for calculating pi
  z = pixel:
   x = (1-z^p1)^(1/p1)
   z = z*(1-x)/(1+x) + p2
    |z| <= 4
  }

IkeNewtMand {; Ron Barnett, 1993
  z = c = pixel:
   zf = z*z*z + (c-1)*z - c
   zd = 3*z*z + c-1
   z = z - p1*zf/zd
    0.001 <= |zf|
  }

Frame-RbtM(XAXIS) {; Ron Barnett, 1993
  ; from Mazes for the Mind by Pickover
  z = c = pixel:
   z = z*z*z/5 + z*z + c
    |z| <= 100
  }

FrRbtGenM {; Ron Barnett, 1993
  z = pixel:
   z = p1*z*z*z + z*z + pixel
    |z| <= 100
  }

FlipLambdaJ { ; Ron Barnett, 1993
  z = pixel:
   z = p1*z*(1-flip(z)*flip(z))
    |z| <= 100
  }

REBRefInd2 {  ; Ron Barnett, 1993
  ; Use floating point
  z = pixel:
   z = (z*z-1)/(z*z+2)*fn1(z)*fn2(z) + p1
    |z| <= 100
  }

GopalsamyFn {
  z = pixel:
   x = real(z), y = imag(z)
   x1 = fn1(x)*fn2(y)
   y1 = fn3(x)*fn4(y)
   x2 = -2*x1*y1 + p1
   y = y1*y1 - x1*x1
   z = x2 + flip(y)
    |z| <= 100
  }

REB004A {; Ron Barnett, 1993
  z = pixel:
   z =p1*fn1(z) + p1*p1*fn2(p2*z) + pixel
    |z| <= 100
  }

REB004K {; Ron Barnett, 1993
  ; floating point required
  z = pixel:
   x = flip(pixel + fn1(3/z - z/4))
   z = x*z + p1
    |z| <= 100
  }

REB004L {; Ron Barnett, 1993
  ; floating point required
  z = pixel:
   x = flip(pixel + fn1(p1/z - z/(p2+1)))
   z = x*z + pixel
    |z| <= 100
  }

REB004M {; Ron Barnett, 1993
  ; floating point required
  z = pixel:
   x = real(z), y = imag(z)
   const = x*x + y*y
   x1 = -fn1(const - 12*x)*x/(4*const)
   y1 = -fn2(const + 12*x)*y/(4*const)
   x2 = x1*x1 - y1*y1 + p1
   y2 = 2*x*y
   z = x2 + flip(y2)
    |z| <= 100
  }

REB005A {; Ron Barnett, 1993
  ; floating point required
  z = pixel:
   x = real(z), y = imag(z)
   const = x*x + y*y
   x1 = -fn1(const - 12*x)*x/(4*const)
   y1 = -fn2(const + 12*y)*y/(4*const)
   x2 = x1*x1 - y1*y1 + p1
   y2 = 2*x1*y1
   z = x2 + flip(y2)
    |z| <= 100
  }

REB005E {; Ron Barnett, 1993
  ; floating point required
  z = pixel:
   x = real(z), y = imag(z)
   const = x*x + y*y
   x1 = -fn1((const - x)*x/const)
   y1 = -fn2((const + y)*y/const)
   x2 = x1*x1 - y1*y1 + p1
   y2 = 2*x1*y1
   z = x2 + flip(y2)
    |z| <= 100
  }

REB005F {; Ron Barnett, 1993
  ; floating point required
  z = pixel:
   x = real(z), y = imag(z)
   const = x*x + y*y
   x1 = -fn1((const - 12*x)*x/(4*const))
   y1 = -fn2((const + 12*y)*y/(4*const))
   x2 = x1*x1 - y1*y1 + p1
   y2 = 2*x1*y1
   z = x2 + flip(y2)
    |z| <= 100
  }

REB005G {; Ron Barnett, 1993
  ; floating point required
  z = pixel:
   x = real(z), y = imag(z)
   const = x*x + y*y
   x1 = -fn1(const + p1*x)*y/const
   y1 = -fn2(const + y)*x/const
   x2 = x1*x1 - y1*y1 + p2
   y2 = 2*x1*y1
   z = x2 + flip(y2)
    |z| <= 100
  }

{--- BRADLEY BEACHAM -----------------------------------------------------}

OK-01 { ;TRY P1 REAL = 10000, FN1 = SQR
  z = 0, c = pixel:
   z = (c^z) + c
   z = fn1(z)
    |z| <= (5 + p1)
  }

OK-04 { ;TRY FN2 = SQR, DIFFERENT FUNCTIONS FOR FN1
  z = 0, c = fn1(pixel):
   z = fn2(z) + c
    |z| <= (5 + p1)
  }

OK-08 {
  z = pixel, c = fn1(pixel):
   z = z^z / fn2(z)
   z = c / z
    |z| <= (5 + p1)
  }

OK-21 {
  z = pixel, c = fn1(pixel):
   z = fn2(z) + c
    fn3(z) <= p1
  }

OK-22 {
  z = v = pixel:
   v = fn1(v) * fn2(z)
   z = fn1(z) / fn2(v)
    |z| <= (5 + p1)
  }

OK-36 { ; DISSECTED MANDELBROT
  ; TO GENERATE "STANDARD" MANDELBROT, SET P1 = 0,0 & ALL FN = IDENT
  z = pixel, cx = fn1(real(z)), cy = fn2(imag(z)), k = 2 + p1:
   zx = real(z), zy = imag(z)
   x = fn3(zx*zx - zy*zy) + cx
   y = fn4(k * zx * zy) + cy
   z = x + flip(y)
    |z| <  (10 + p2)
  }

OK-38 { ; DISSECTED CUBIC MANDELBROT
  ; TO GENERATE "STANDARD" CUBIC MANDELBROT, SET P1 = 0,0 & ALL FN = IDENT
  z = pixel,  cx = fn1(real(pixel)), cy = fn2(imag(pixel)), k = 3 + p1:
   zx = real(z), zy = imag(z)
   x = fn3(zx*zx*zx - k*zx*zy*zy) + cx
   y = fn4(k*zx*zx*zy - zy*zy*zy) + cy
   z =  x + flip(y)
    |z| <  (4 + p2)
  }

OK-42 { ; MUTATION OF FN + FN
  z = pixel, p1x = real(p1)+1, p1y = imag(p1)+1
  p2x = real(p2)+1, p2y = imag(p2)+1:
   zx = real(z), zy = imag(z)
   x = fn1(zx*p1x - zy*p1y) + fn2(zx*p2x - zy*p2y)
   y = fn3(zx*p1y + zy*p1x) + fn4(zx*p2y + zy*p2x)
   z = x + flip(y)
    |z| <= 20
  }

OK-43 { ; DISSECTED SPIDER
  ; TO GENERATE "STANDARD" SPIDER, SET P1 = 0,0 & ALL FN = IDENT
  z = c = pixel, k = 2 + p1:
   zx = real(z), zy = imag(z)
   cx = real(c), cy = imag(c)
   x = fn1(zx*zx - zy*zy) + cx
   y = fn2(k*zx*zy) + cy
   z = x + flip(y)
   c = fn3((cx + flip(cy))/k) + z
    |z| <  (10 + p2)
  }

{--- PIETER BRANDERHORST -------------------------------------------------}

comment {
  The following resulted from a FRACTINT bug. Version 13 incorrectly
  calculated Spider (see above). We fixed the bug, and reverse-engineered
  what it was doing to Spider - so here is the old "spider"
  }

Wineglass(XAXIS) {; Pieter Branderhorst
  c = z = pixel:
   z = z * z + c
   c = (1+flip(imag(c))) * real(c) / 2 + z
    |z| <= 4
  }

{--- JM COLLARD-RICHARD --------------------------------------------------}

comment {
  These are the original "Richard" types sent by Jm Collard-Richard. Their
  generalizations are tacked on to the end of the "Jm" list below, but
  we felt we should keep these around for historical reasons.
  }

Richard1 (XYAXIS) {; Jm Collard-Richard
  z = pixel:
   sq=z*z, z=(sq*sin(sq)+sq)+pixel
    |z|<=50
  }

Richard2 (XYAXIS) {; Jm Collard-Richard
  z = pixel:
   z=1/(sin(z*z+pixel*pixel))
    |z|<=50
  }

Richard3 (XAXIS) {; Jm Collard-Richard
  z = pixel:
   sh=sinh(z), z=(1/(sh*sh))+pixel
    |z|<=50
  }

Richard4 (XAXIS) {; Jm Collard-Richard
  z = pixel:
   z2=z*z, z=(1/(z2*cos(z2)+z2))+pixel
    |z|<=50
  }

Richard5 (XAXIS) {; Jm Collard-Richard
  z = pixel:
   z=sin(z*sinh(z))+pixel
    |z|<=50
  }

Richard6 (XYAXIS) {; Jm Collard-Richard
  z = pixel:
   z=sin(sinh(z))+pixel
    |z|<=50
  }

Richard7 (XAXIS) {; Jm Collard-Richard
  z=pixel:
   z=log(z)*pixel
    |z|<=50
  }

Richard8 (XYAXIS) {; Jm Collard-Richard
  ; This was used for the "Fractal Creations" cover
  z=pixel,sinp = sin(pixel):
   z=sin(z)+sinp
    |z|<=50
  }

Richard9 (XAXIS) {; Jm Collard-Richard
  z=pixel:
   sqrz=z*z, z=sqrz + 1/sqrz + pixel
    |z|<=4
  }

Richard10(XYAXIS) {; Jm Collard-Richard
  z=pixel:
   z=1/sin(1/(z*z))
    |z|<=50
  }

Richard11(XYAXIS) {; Jm Collard-Richard
  z=pixel:
   z=1/sinh(1/(z*z))
    |z|<=50
  }

comment {
  These types are generalizations of types sent to us by the French
  mathematician Jm Collard-Richard. If we hadn't generalized them
  there would be --ahhh-- quite a few. With 26 possible values for
  each fn variable, Jm_03, for example, has 456,976 variations!
  }

Jm_01 {; generalized Jm Collard-Richard type
  z=#zwpixel+#pixel,t=p1+4:
   z=(fn1(fn2(z^pixel)))*pixel
    |z|<=t
  }

Jm_02 {; generalized Jm Collard-Richard type
  z=#zwpixel+#pixel,t=p1+4:
   z=(z^pixel)*fn1(z^pixel)
    |z|<=t
  }

Jm_03 {; generalized Jm Collard-Richard type
  z=#zwpixel+#pixel,t=p1+4:
   z=fn1((fn2(z)*pixel)*fn3(fn4(z)*pixel))*pixel
    |z|<=t
  }

Jm_03a {; generalized Jm Collard-Richard type
  z=#zwpixel,t=@bailout:
   z=fn1((fn2(z)*#pixel)*fn3(fn4(z)*#pixel))+#pixel
    |z|<=t
default:
float param bailout
	default = 4.0
endparam
  }

Jm_04 {; generalized Jm Collard-Richard type
  z=#zwpixel+#pixel,t=p1+4:
   z=fn1((fn2(z)*pixel)*fn3(fn4(z)*pixel))
    |z|<=t
  }

Jm_05 {; generalized Jm Collard-Richard type
  z=#zwpixel+#pixel,t=p1+4:
   z=fn1(fn2((z^pixel)))
    |z|<=t
  }

Jm_06 {; generalized Jm Collard-Richard type
  z=#zwpixel+#pixel,t=p1+4:
   z=fn1(fn2(fn3((z^z)*pixel)))
    |z|<=t
  }

Jm_07 {; generalized Jm Collard-Richard type
  z=#zwpixel+#pixel,t=p1+4:
   z=fn1(fn2(fn3((z^z)*pixel)))*pixel
    |z|<=t
  }

Jm_08 {; generalized Jm Collard-Richard type
  z=#zwpixel,t=p1+4:
   z=fn1(fn2(fn3((z^z)*pixel)))+pixel
    |z|<=t
  }

Jm_09 {; generalized Jm Collard-Richard type
  z=#zwpixel,t=p1+4:
   z=fn1(fn2(fn3(fn4(z))))+pixel
    |z|<=t
  }

Jm_10 {; generalized Jm Collard-Richard type
  z=#zwpixel+#pixel,t=p1+4:
   z=fn1(fn2(fn3(fn4(z)*pixel)))
    |z|<=t
  }

Jm_11 {; generalized Jm Collard-Richard type
  z=#zwpixel+#pixel,t=p1+4:
   z=fn1(fn2(fn3(fn4(z)*pixel)))*pixel
    |z|<=t
  }

Jm_11a {; generalized Jm Collard-Richard type
  z=#zwpixel,t=p1+4:
   z=fn1(fn2(fn3(fn4(z)*pixel)))+pixel
    |z|<=t
  }

Jm_12 {; generalized Jm Collard-Richard type
  z=#zwpixel+#pixel,t=p1+4:
   z=fn1(fn2(fn3(z)*pixel))
    |z|<=t
  }

Jm_13 {; generalized Jm Collard-Richard type
  z=#zwpixel+#pixel,t=p1+4:
   z=fn1(fn2(fn3(z)*pixel))*pixel
    |z|<=t
  }

Jm_14 {; generalized Jm Collard-Richard type
  z=#zwpixel,t=p1+4:
   z=fn1(fn2(fn3(z)*pixel))+pixel
    |z|<=t
  }

Jm_15 {; generalized Jm Collard-Richard type
  z=#zwpixel+#pixel,t=p1+4:
   f2=fn2(z),z=fn1(f2)*fn3(fn4(f2))*pixel
    |z|<=t
  }

Jm_16 {; generalized Jm Collard-Richard type
  z=#zwpixel,t=p1+4:
   f2=fn2(z),z=fn1(f2)*fn3(fn4(f2))+pixel
    |z|<=t
  }

Jm_17 {; generalized Jm Collard-Richard type
  z=#zwpixel+#pixel,t=p1+4:
   z=fn1(z)*pixel*fn2(fn3(z))
    |z|<=t
  }

Jm_18 {; generalized Jm Collard-Richard type
  z=#zwpixel+#pixel,t=p1+4:
   z=fn1(z)*pixel*fn2(fn3(z)*pixel)
    |z|<=t
  }

Jm_19 {; generalized Jm Collard-Richard type
  z=#zwpixel,t=p1+4:
   z=fn1(z)*pixel*fn2(fn3(z)+pixel)
    |z|<=t
  }

Jm_20 {; generalized Jm Collard-Richard type
  z=#zwpixel+#pixel,t=p1+4:
   z=fn1(z^pixel)
    |z|<=t
  }

Jm_21 {; generalized Jm Collard-Richard type
  z=#zwpixel+#pixel,t=p1+4:
   z=fn1(z^pixel)*pixel
    |z|<=t
  }

Jm_22 {; generalized Jm Collard-Richard type
  z=#zwpixel,t=p1+4:
   sq=fn1(z), z=(sq*fn2(sq)+sq)+pixel
    |z|<=t
  }

Jm_23 {; generalized Jm Collard-Richard type
  z=#zwpixel+#pixel,t=p1+4:
   z=fn1(fn2(fn3(z)+pixel*pixel))
    |z|<=t
  }

Jm_24 {; generalized Jm Collard-Richard type
  z=#zwpixel,t=p1+4:
   z2=fn1(z), z=(fn2(z2*fn3(z2)+z2))+pixel
    |z|<=t
  }

Jm_25 {; generalized Jm Collard-Richard type
  z=#zwpixel,t=p1+4:
   z=fn1(z*fn2(z)) + pixel
    |z|<=t
  }

Jm_26 {; generalized Jm Collard-Richard type
  z=#zwpixel,t=p1+4:
   z=fn1(fn2(z)) + pixel
    |z|<=t
  }

Jm_27 {; generalized Jm Collard-Richard type
  z=#zwpixel,t=p1+4:
   sqrz=fn1(z), z=sqrz + 1/sqrz + pixel
    |z|<=t
  }

Jm_ducks(XAXIS) {; Jm Collard-Richard
  ; Not so ugly at first glance and lot of corners to zoom in.
  ; try this: corners=-1.178372/-0.978384/-0.751678/-0.601683
  z=#zwpixel,tst=p1+4,t=1+pixel:
   z=sqr(z)+t
    |z|<=tst
  }

Gamma(XAXIS) { ; first order gamma function from Prof. Jm
  ; "It's pretty long to generate even on a 486-33 comp but there's a lot
  ; of corners to zoom in and zoom and zoom...beautiful pictures :)"
  z=#zwpixel,twopi=6.283185307179586,r=10:
   z=(twopi*z)^(0.5)*(z^z)*exp(-z)+pixel
    |z|<=r
  }

ZZ(XAXIS) { ; Prof Jm using Newton-Raphson method
  ; use floating point with this one
  z=#pixel,solution=1:
   z1=z^z
   z2=(log(z)+1)*z1
   z=z-(z1-1)/z2
    0.001 <= |solution-z1|
  }

ZZa(XAXIS) { ; Prof Jm using Newton-Raphson method
  ; use floating point with this one
  z=#pixel,solution=1:
   z1=z^(z-1)
   z2=(((z-1)/z)+log(z))*z1
   z=z-((z1-1)/z2)
    .001 <= |solution-z1|
  }

GenInvMand1_N { ; Jm Collard-Richard
  c=z=1/pixel:
   z=fn1(z)*fn2(z)+fn3(fn4(c))
    |z|<=4
  }

{--- W. LEROY DAVIS ------------------------------------------------------}

comment {
  These are from: "AKA MrWizard W. LeRoy Davis;SM-ALC/HRUC"
      davisl@sm-logdis1-aflc.af.mil
  The first 3 are variations of:
         z
     gamma(z) = (z/e) * sqrt(2*pi*z) * R
  }

Sterling(XAXIS) {; davisl
  z = Pixel:
   z = ((z/2.7182818)^z)/sqr(6.2831853*z)
    |z| <= 4
  }

Sterling2(XAXIS) {; davisl
  z = Pixel:
   z = ((z/2.7182818)^z)/sqr(6.2831853*z) + pixel
    |z| <= 4
  }

Sterling3(XAXIS) {; davisl
  z = Pixel:
   z = ((z/2.7182818)^z)/sqr(6.2831853*z) - pixel
    |z| <= 4
  }

PsudoMandel(XAXIS) {; davisl - try center=0,0/magnification=28
  z = Pixel:
   z = ((z/2.7182818)^z)*sqr(6.2831853*z) + pixel
    |z| <= 4
  }

{--- ROB DEN BRAASEM -----------------------------------------------------}

J_TchebychevC3 {
  c = pixel, z = P1:
   z = c*z*(z*z-3)
    |z|<100
  }

J_TchebychevC7 {
  c = pixel, z = P1:
   z = c*z*(z*z*(z*z*(z*z-7)+14)-7)
    |z|<100
  }

J_TchebychevS4 {
  c = pixel, z = P1:
   z = c*(z*z*(z*z-3)+1)
    |z|<100
  }

J_TchebychevS6 {
  c = pixel, z = P1:
   z = c*(z*z*(z*z*(z*z-5)+6)-1)
    |z|<100
  }

J_TchebychevS7 {
  c = pixel, z = P1:
   z = c*z*(z*z*(z*z*(z*z-6)+10)-4)
    |z|<100
  }

J_Laguerre2 {
  c = pixel, z = P1:
   z = (z*(z - 4) +2 ) / 2 + c
    |z| < 100
  }

J_Laguerre3 {
  c = pixel, z = P1:
   z = (z*(z*(-z + 9) -18) + 6 ) / 6 + c
    |z| < 100
  }

J_Lagandre4 {
  c = pixel, z = P1:
   z = (z*z*(35 * z*z - 30) + 3) / 8 + c
    |z| < 100
  }

M_TchebychevT5 {
  c = P1, z = Pixel:
   z = c*(z*(z*z*(16*z*z-20)+5))
    |z|<100
  }

M_TchebychevC5 {
  c = P1, z = Pixel:
   z = c*z*(z*z*(z*z-5)+5)
    |z|<100
  }

M_TchebychevU3 {
  c = P1, z = Pixel:
   z = c*z*(8*z*z-4)
    |z|<100
  }

M_TchebychevS3 {
  c = P1, z = Pixel:
   z = c*z*(z*z-2)
    |z|<100
  }

M_Lagandre2 {
  c = P1, z = Pixel:
   z = (3 * z*z - 1) / 2 + c
    |z| < 100
  }

M_Lagandre6 {
  c = P1, z = Pixel:
   z = (z*z*(z*z*(231 * z*z - 315)  + 105 ) - 5) / 16 + c
    |z| < 100
  }

{--- CHUCK EBBERT & JON HORNER -------------------------------------------}

comment {
  Chaotic Liar formulas for FRACTINT. These formulas reproduce some of the
  pictures in the paper 'Pattern and Chaos: New Images in the Semantics of
  Paradox' by Gary Mar and Patrick Grim of the Department of Philosophy,
  SUNY at Stony Brook. "...what is being graphed within the unit square is
  simply information regarding the semantic behavior for different inputs
  of a pair of English sentences:"
  }

Liar1 { ; by Chuck Ebbert.
  ; X: X is as true as Y
  ; Y: Y is as true as X is false
  ; Calculate new x and y values simultaneously.
  ; y(n+1)=abs((1-x(n) )-y(n) ), x(n+1)=1-abs(y(n)-x(n) )
  z = pixel:
   z = 1 - abs(imag(z)-real(z) ) + flip(1 - abs(1-real(z)-imag(z) ) )
    |z| <= 1
  }

Liar3 { ; by Chuck Ebbert.
  ; X: X is true to P1 times the extent that Y is true
  ; Y: Y is true to the extent that X is false.
  ; Sequential reasoning.  P1 usually 0 to 1.  P1=1 is Liar2 formula.
  ; x(n+1) = 1 - abs(p1*y(n)-x(n) );
  ; y(n+1) = 1 - abs((1-x(n+1) )-y(n) );
  z = pixel:
   x = 1 - abs(imag(z)*real(p1)-real(z) )
   z = flip(1 - abs(1-real(x)-imag(z) ) ) + real(x)
    |z| <= 1
  }

Liar4 { ; by Chuck Ebbert.
  ; X: X is as true as (p1+1) times Y
  ; Y: Y is as true as X is false
  ; Calculate new x and y values simultaneously.
  ; Real part of p1 changes probability.  Use floating point.
  ; y(n+1)=abs((1-x(n) )-y(n) ), x(n+1)=1-abs(y(n)-x(n) )
  z = pixel, p = p1 + 1:
   z = 1-abs(imag(z)*p-real(z))+flip(1-abs(1-real(z)-imag(z)))
    |z| <= 1
  }

F'Liar1 { ; Generalization by Jon Horner of Chuck Ebbert formula.
  ; X: X is as true as Y
  ; Y: Y is as true as X is false
  ; Calculate new x and y values simultaneously.
  ; y(n+1)=abs((1-x(n) )-y(n) ), x(n+1)=1-abs(y(n)-x(n) )
  z = pixel:
   z = 1 - abs(imag(z)-real(z) ) + flip(1 - abs(1-real(z)-imag(z) ) )
    fn1(abs(z))<p1
  }

M-SetInNewton(XAXIS) {; use float=yes
  ; jon horner 100112,1700, 12 feb 93
  z = 0,  c = pixel,  cminusone = c-1:
   oldz = z, nm = 3*c-2*z*cminusone, dn = 3*(3*z*z+cminusone)
   z = nm/dn+2*z/3
    |(z-oldz)|>=|0.01|
  }

F'M-SetInNewtonA(XAXIS) {; use float=yes
  ; jon horner 100112,1700, 12 feb 93
  z = 0,  c = fn1(pixel),  cminusone = c-1:
   oldz = z, nm = p1*c-2*z*cminusone, dn = p1*(3*z*z+cminusone)
   z = nm/dn+2*z/p1
    |(z-oldz)|>=|0.01|
  }

F'M-SetInNewtonC(XAXIS) { ; same as F'M-SetInNewtonB except for bailout
  ; use float=yes, periodicity=no
  ; (3 <= p1 <= ?) and (1e-30 < p2 < .01)
  z=0, c=fn1(pixel), cm1=c-1, cm1x2=cm1*2, twoop1=2/p1, p1xc=c*real(p1):
   z = (p1xc - z*cm1x2 )/( (sqr(z)*3 + cm1 ) * real(p1) ) + z*real(twoop1)
    abs(|z| - real(lastsqr) ) >= p2
  }

{--- SYLVIE GALLET -------------------------------------------------------}

comment {
  This formula uses Newton's formula applied to the real equation :
     F(x,y) = 0 where F(x,y) = (x^3 + y^2 - 1 , y^3 - x^2 + 1)
     starting with (x_0,y_0) = z0 = pixel
  It calculates:
     (x_(n+1),y_(n+1)) = (x_n,y_n) - (F'(x_n,y_n))^-1 * F(x_n,y_n)
     where (F'(x_n,y_n))^-1 is the inverse of the Jacobian matrix of F.
  }

Newton_real { ; Sylvie Gallet [101324,3444], 1996
  ; Newton's method applied to   x^3 + y^2 - 1 = 0
  ;                              y^3 - x^2 + 1 = 0
  ;                              solution (0,-1)
  ; One parameter : real(p1) = bailout value
  z = pixel , x = real(z) , y = imag(z) :
   xy = x*y
   d = 9*xy+4 , x2 = x*x , y2 = y*y
   c = 6*xy+2
   x1 = x*c - (y*y2 - 3*y - 2)/x
   y1 = y*c + (x*x2 + 2 - 3*x)/y
   z = (x1+flip(y1))/d , x = real(z) , y = imag(z)
    (|x| >= p1) || (|y+1| >= p1)
  }

G-3-03-M  { ; Sylvie Gallet [101324,3444], 1996
            ; Modified Gallet-3-03 formula
  z = pixel :
   x = real(z) , y = imag(z)
   x1 = x - p1 * fn1(y*y + round(p2*fn2(y)))
   y1 = y - p1 * fn1(x*x + round(p2*fn2(x)))
   z = x1 + flip(y1)
    |z| <= 4
  }

{--- CHRIS GREEN ---------------------------------------------------------}

comment {
  These fractals all use Newton's or Halley's formula for approximation of
  a function.  In all of these fractals, p1 real is the "relaxation
  coefficient". A value of 1 gives the conventional newton or halley
  iteration. Values <1 will generally produce less chaos than values >1.
  1-1.5 is probably a good range to try.  P1 imag is the imaginary
  component of the relaxation coefficient, and should be zero but maybe a
  small non-zero value will produce something interesting.  Who knows?
  For more information on Halley maps, see "Computers, Pattern, Chaos, and
  Beauty" by Pickover.
  }

Halley (XYAXIS) {; Chris Green. Halley's formula applied to x^7-x=0.
  ; P1 real usually 1 to 1.5, P1 imag usually zero. Use floating point.
  ; Setting P1 to 1 creates the picture on page 277 of Pickover's book
  z=pixel:
   z5=z*z*z*z*z
   z6=z*z5
   z7=z*z6
   z=z-p1*((z7-z)/ ((7.0*z6-1)-(42.0*z5)*(z7-z)/(14.0*z6-2)))
    0.0001 <= |z7-z|
  }

CGhalley (XYAXIS) {; Chris Green -- Halley's formula
  ; P1 real usually 1 to 1.5, P1 imag usually zero. Use floating point.
  z=(1,1):
   z5=z*z*z*z*z
   z6=z*z5
   z7=z*z6
   z=z-p1*((z7-z-pixel)/ ((7.0*z6-1)-(42.0*z5)*(z7-z-pixel)/(14.0*z6-2)))
    0.0001 <= |z7-z-pixel|
  }

halleySin (XYAXIS) {; Chris Green. Halley's formula applied to sin(x)=0.
  ; Use floating point.
  ; P1 real = 0.1 will create the picture from page 281 of Pickover's book.
  z=pixel:
   s=sin(z), c=cos(z)
   z=z-p1*(s/(c-(s*s)/(c+c)))
    0.0001 <= |s|
  }

NewtonSinExp (XAXIS) {; Chris Green
  ; Newton's formula applied to sin(x)+exp(x)-1=0.
  ; Use floating point.
  z=pixel:
   z1=exp(z)
   z2=sin(z)+z1-1
   z=z-p1*z2/(cos(z)+z1)
    .0001 < |z2|
  }

CGNewtonSinExp (XAXIS) {
  z=pixel:
   z1=exp(z)
   z2=sin(z)+z1-z
   z=z-p1*z2/(cos(z)+z1)
    .0001 < |z2|
  }

CGNewton3 {; Chris Green -- A variation on newton iteration.
  ; The initial guess is fixed at (1,1), but the equation solved
  ; is different at each pixel ( x^3-pixel=0 is solved).
  ; Use floating point.
  ; Try P1=1.8.
  z=(1,1):
   z2=z*z
   z3=z*z2
   z=z-p1*(z3-pixel)/(3.0*z2)
    0.0001 < |z3-pixel|
  }

HyperMandel {; Chris Green.
  ; A four dimensional version of the mandelbrot set.
  ; Use P1 to select which two-dimensional plane of the
  ; four dimensional set you wish to examine.
  ; Use floating point.
  a=(0,0),b=(0,0):
   z=z+1
   anew=sqr(a)-sqr(b)+pixel
   b=2.0*a*b+p1
   a=anew
    |a|+|b| <= 4
  }

OldHalleySin (XYAXIS) {
  z=pixel:
   s=sin(z)
   c=cosxx(z)
   z=z-p1*(s/(c-(s*s)/(c+c)))
    0.0001 <= |s|
  }

{--- RICHARD HUGHES ------------------------------------------------------}

phoenix_m { ; Mandelbrot style map of the Phoenix curves
  z=x=y=nx=ny=x1=y1=x2=y2=0:
   x2 = sqr(x), y2 = sqr(y)
   x1 = x2 - y2 + real(pixel) + imag(pixel) * nx
   y1 = 2 * x * y + imag(pixel) * ny
   nx=x, ny=y, x=x1, y=y1, z=x + flip(y)
    |z| <= 4
  }

{--- GORDON LAMB ---------------------------------------------------------}

SJMAND01 {;Mandelbrot
  z=real(pixel)+flip(imag(pixel)*p1)
  c=p2+p1*real(pixel)+flip(imag(pixel)):
   z=z*z+c
    |z|<=64
  }

3RDIM01 {;Mandelbrot
  z=p1*real(pixel)+flip(imag(pixel))
  c=p2+real(pixel)+flip(imag(pixel)*p1):
   z=z*z+c
    |z|<=64
  }

SJMAND03 {;Mandelbrot function
  z=real(pixel)+p1*(flip(imag(pixel)))
  c=p2+p1*real(pixel)+flip(imag(pixel)):
   z=fn1(z)+c
    |z|<=64
  }

SJMAND05 {;Mandelbrot lambda function
  z=real(pixel)+flip(imag(pixel)*p1)
  c=p2+p1*real(pixel)+flip(imag(pixel)):
   z=fn1(z)*c
    |z|<=64
  }

3RDIM05 {;Mandelbrot lambda function
  z=p1*real(pixel)+flip(imag(pixel))
  c=p2+real(pixel)+flip(imag(pixel)*p1):
   z=fn1(z)*c
    |z|<=64
  }

SJMAND10 {;Mandelbrot power function
  z=real(pixel),c=p2+flip(imag(pixel)):
   z=(fn1(z)+c)^p1
    |z|<=4
  }

SJMAND11 {;Mandelbrot lambda function - lower bailout
  z=real(pixel)+flip(imag(pixel)*p1)
  c=p2+p1*real(pixel)+flip(imag(pixel)):
   z=fn1(z)*c
    |z|<=4
  }

{--- KEVIN LEE -----------------------------------------------------------}

LeeMandel1(XYAXIS) {; Kevin Lee
  z=#pixel + #zwpixel:
;; c=sqr(pixel)/z, c=z+c, z=sqr(z),  this line was an error in v16
   c=sqr(pixel)/z, c=z+c, z=sqr(c)
    |z|<@bailout
default:
float param bailout
	default=4.0
endparam
  }

LeeMandel2(XYAXIS) {; Kevin Lee
  z=#pixel + #zwpixel:
   c=sqr(pixel)/z, c=z+c, z=sqr(c*pixel)
    |z|<@bailout
default:
float param bailout
	default=4.0
endparam
   }

LeeMandel3(XAXIS) {; Kevin Lee
init:
  z=#pixel + #zwpixel, c=#pixel + #zwpixel-sqr(z):
loop:
   c=Pixel+c/z, z=c-z*pixel
bailout:
    |z|<@bailout
default:
float param bailout
	default=4.0
endparam
  }

{--- RON LEWEN -----------------------------------------------------------}

RCL_Cross1 { ; Ron Lewen
  ; Try p1=(0,1), fn1=sin and fn2=sqr.  Set corners at
  ; -10/10/-7.5/7.5 to see a cross shape.  The larger
  ; lakes at the center of the cross have good detail
  ; to zoom in on.
  ; Use floating point.
  z=pixel:
   z=p1*fn1(fn2(z+p1))
    |z| <= 4
  }

RCL_Pick13 { ; Ron Lewen
  ;  Formula from Frontpiece for Appendix C
  ;  and Credits in Pickover's book.
  ;  Set p1=(3,0) to generate the Frontpiece
  ;  for Appendix C and to (2,0) for Credits
  ;  Use Floating Point
  z=.001:
   z=z^p1+(1/pixel)^p1
    |z| <= 100
  }

RCL_1 (XAXIS) { ; Ron Lewen
  ;  An interesting Biomorph inspired by Pickover's
  ;  Computers, Pattern, Choas and Beauty.
  ;  Use Floating Point
  z=pixel:
   z=pixel/z-z^2
    |real(z)| <= 100 || |imag(z)| <= 100
  }

RCL_Cosh (XAXIS) { ; Ron Lewen, 76376,2567
  ; Try corners=2.008874/-3.811126/-3.980167/3.779833/
  ; -3.811126/3.779833 to see Figure 9.7 (P. 123) in
  ; Pickover's Computers, Pattern, Chaos and Beauty.
  ; Figures 9.9 - 9.13 can be found by zooming.
  ; Use floating point
  z=0:
   z=cosh(z) + pixel
    abs(z) < 40
  }

Mothra (XAXIS) { ; Ron Lewen, 76376,2567
  ; Remember Mothra, the giant Japanese-eating moth?
  ; Well... here he (she?) is as a fractal!
  z=pixel:
   a=z^5 + z^3 + z + pixel
   b=z^4 + z^2 + pixel
   z=b^2/a,
    |real(z)| <= 100 || |imag(z)| <= 100
  }

RCL_10 { ; Ron Lewen, 76376,2567
  z=pixel:
   z=flip((z^2+pixel)/(pixel^2+z))
    |z| <= 4
  }

{--- LEE SKINNER ---------------------------------------------------------}

MTet (XAXIS) {; Mandelbrot form 1 of the Tetration formula --Lee Skinner
  z = pixel:
   z = (pixel ^ z) + pixel
    |z| <= (P1 + 3)
  }

AltMTet(XAXIS) {; Mandelbrot form 2 of the Tetration formula --Lee Skinner
  z = 0:
   z = (pixel ^ z) + pixel
    |z| <= (P1 + 3)
  }

JTet (XAXIS) {; Julia form 1 of the Tetration formula --Lee Skinner
  z = pixel:
   z = (pixel ^ z) + P1
    |z| <= (P2 + 3)
  }

AltJTet (XAXIS) {; Julia form 2 of the Tetration formula --Lee Skinner
  z = P1:
   z = (pixel ^ z) + P1
    |z| <= (P2 + 3)
  }

Cubic (XYAXIS) {; Lee Skinner
  p = pixel, test = p1 + 3
  t3 = 3*p, t2 = p*p
  a = (t2 + 1)/t3, b = 2*a*a*a + (t2 - 2)/t3
  aa3 = a*a*3, z = 0 - a :
   z = z*z*z - aa3*z + b
    |z| < test
 }

Fzppfnre {; Lee Skinner
  z = pixel, f = 1./(pixel):
   z = fn1(z) + f
    |z| <= 50
  }

Fzppfnpo {; Lee Skinner
  z = pixel, f = (pixel)^(pixel):
   z = fn1(z) + f
    |z| <= 50
  }

Fzppfnsr {; Lee Skinner
  z = pixel, f = (pixel)^.5:
   z = fn1(z) + f
    |z| <= 50
  }

Fzppfnta {; Lee Skinner
  z = pixel, f = tan(pixel):
   z = fn1(z) + f
    |z|<= 50
  }

Fzppfnct {; Lee Skinner
  z = pixel, f = cos(pixel)/sin(pixel):
   z = fn1(z) + f
    |z|<= 50
  }

Fzppfnse {; Lee Skinner
  z = pixel, f = 1./sin(pixel):
   z = fn1(z) + f
    |z| <= 50
  }

Fzppfncs {; Lee Skinner
  z = pixel, f = 1./cos(pixel):
   z = fn1(z) + f
    |z| <= 50
  }

Fzppfnth {; Lee Skinner
  z = pixel, f = tanh(pixel):
   z = fn1(z)+f
    |z|<= 50
  }

Fzppfnht {; Lee Skinner
  z = pixel, f = cosh(pixel)/sinh(pixel):
   z = fn1(z)+f
    |z|<= 50
  }

Fzpfnseh {; Lee Skinner
  z = pixel, f = 1./sinh(pixel):
   z = fn1(z) + f
    |z| <= 50
  }

Fzpfncoh {; Lee Skinner
  z = pixel, f = 1./cosh(pixel):
   z = fn1(z) + f
    |z| <= 50
  }

Zexpe (XAXIS) {
  s = exp(1.,0.), z = Pixel:
   z = z ^ s + pixel
    |z| <= 100
  }

comment {
  s = log(-1.,0.) / (0.,1.)   is   (3.14159265358979, 0.0)
  }

Exipi (XAXIS) {
  s = log(-1.,0.) / (0.,1.), z = Pixel:
   z = z ^ s + pixel
    |z| <= 100
  }

Fzppchco {
  z = pixel, f = cosxx (pixel):
   z = cosh (z) + f
    |z| <= 50
  }

Fzppcosq {
  z = pixel, f = sqr (pixel):
   z = cosxx (z)  + f
    |z| <= 50
  }

Fzppcosr {
  z = pixel, f = (pixel) ^ 0.5:
   z = cosxx (z)  + f
    |z| <= 50
  }

Leeze (XAXIS) {
  s = exp(1.,0.), z = Pixel, f = Pixel ^ s:
   z = cosxx (z) + f
    |z| <= 50
  }

OldManowar (XAXIS) {
  z0 = 0
  z1 = 0
  test = p1 + 3
  c = pixel :
   z = z1*z1 + z0 + c
   z0 = z1
   z1 = z
    |z| < test
  }

ScSkLMS(XAXIS) {
  z = pixel, TEST = (p1+3):
   z = log(z) - sin(z)
    |z|<TEST
  }

ScSkZCZZ(XYAXIS) {
  z = pixel, TEST = (p1+3):
   z = (z*cosxx(z)) - z
    |z|<TEST
  }

TSinh (XAXIS) {; Tetrated Hyperbolic Sine - Improper Bailout
  z = c = sinh(pixel):
   z = c ^ z
    z <= (p1 + 3)
  }

{--- SCOTT TAYLOR --------------------------------------------------------}

comment {
  The following is from Scott Taylor.
  Scott says they're "Dog" because the first one he looked at reminded him
  of a hot dog. This was originally several fractals, we have generalized it.
  }

FnDog(XYAXIS) {; Scott Taylor
  z = Pixel, b = p1+2:
   z = fn1( z ) * pixel
    |z| <= b
  }

Ent {; Scott Taylor
  ; Try params=.5/.75 and the first function as exp.
  ; Zoom in on the swirls around the middle.  There's a
  ; symmetrical area surrounded by an asymmetric area.
  z = Pixel, y = fn1(z), base = log(p1):
   z = y * log(z)/base
    |z| <= 4
  }

Ent2 {; Scott Taylor
  ; try params=2/1, functions=cos/cosh, potential=255/355
  z = Pixel, y = fn1(z), base = log(p1):
   z = fn2( y * log(z) / base )
    |z| <= 4
  }

{--- MICHAEL THEROUX & RON BARNETT ---------------------------------------}

test3 {; Michael Theroux [71673,2767]
  ;fix and generalization by Ron Barnett [70153,1233]
  ;=phi
  ;try p1 = 2.236067977 for the golden mean
  z = ((p1 + 1)/2)/pixel:
   z =  z*z + pixel*((p1 + 1)/2)/((p1 - 1)/2)
    |z| <= 4
  }

{--- TIMOTHY WEGNER ------------------------------------------------------}

Newton_poly2 { ; Tim Wegner - use float=yes
  ; fractal generated by Newton formula z^3 + (c-1)z - c
  ; p1 is c in above formula
  z = pixel, z2 = z*z, z3 = z*z2:
   z = (2*z3 + p1) / (3*z2 + (p1 - 1))
   z2 = z*z
   z3 = z*z2
   .004 <= |z3 + (p1-1)*z - p1|
  }

Newt_ellipt_oops { ; Tim Wegner - use float=yes and periodicity=0
  ; fractal generated by Newton formula  (z^3 + c*z^2 +1)^.5
  ; try p1 = 1 and p2 = .1
  ; if p2 is small (say .001), converges very slowly so need large maxit
  ; another "tim's error" - mistook sqr for sqrt (see next)
  z = pixel, z2 = z*z, z3 = z*z2:
   num = (z3 + p1*z2 + 1)^.5      ; f(z)
   denom = (1.5*z2 + p1*z)/num    ; f'(z)
   z = z - (num/denom)            ; z - f(z)/f'(z)
   z2 = z*z
   z3 = z*z2
    p2 <= |z3 + p1*z2 + 1|  ; no need for sqrt because sqrt(z)==0 iff z==0
  }

Newton_elliptic { ; Tim Wegner - use float=yes and periodicity=0
  ; fractal generated by Newton formula f(z) = (z^3 + c*z^2 +1)^2
  ; try p1 = 1 and p2 = .0001
  z = pixel, z2 = z*z, z3 = z*z2:
   z = z - (z3 + p1*z2 + 1)/(6*z2 + 4*p1*z)      ; z - f(z)/f'(z)
   z2 = z*z
   z3 = z*z2
    p2 <= |z3 + p1*z2 + 1|  ; no need for sqr because sqr(z)==0 iff z==0
  }

{--- TIM WEGNER & MARK PETERSON ------------------------------------------}

comment {
  These are a few of the examples from the book, Fractal Creations, by Tim
  Wegner and Mark Peterson.
  }

MyFractal {; Fractal Creations example
  c = z = 1/pixel:
   z = sqr(z) + c
    |z| <= 4
  }

MandelTangent {; Fractal Creations example (revised for v.16)
  z = pixel:
   z = pixel * tan(z)
    |real(z)| < 32
  }

Mandel3 {; Fractal Creations example
  z = pixel, c = sin(z):
   z = (z*z) + c
   z = z * 1/c
    |z| <= 4
  }

{--- AUTHORS UNKNOWN -----------------------------------------------------}

moc {
  z=0, c=pixel:
   z=sqr(z)+c
   c=c+p1/c
    |z| <= 4
  }

Bali {;The difference of two squares
  z=x=1/pixel, c= fn1 (z):
   z = (x+c) * (x-c)
   x=fn2(z)
    |z| <=3
  }

Fatso {;
  z=x=1/pixel, c= fn1 (z):
   z = (x^3)-(c^3)
   x=fn2(z)
    |z| <=3
  }

Bjax {;
  z=c=2/pixel:
   z =(1/((z^(real(p1)))*(c^(real(p2))))*c) + c
   |z| < 4.0
  }

ULI_4 {
  z = Pixel:
   z = fn1(1/(z+p1))*fn2(z+p1)
    |z| <= p2
  }

ULI_5 {
  z = Pixel, c = fn1(pixel):
   z = fn2(1/(z+c))*fn3(z+c)
    |z| <= p1
  }

ULI_6 {
  z = Pixel:
   z = fn1(p1+z)*fn2(p2-z)
    |z| <= p2+16
  }
;Version 1.1
;Copyright (c)1998,1999 Morgan L. Owens
;EG-01{;V.1.1 - earlier versions may be discarded
; = Recurrence
;t=p1,bailout=4,z=pixel:
;x=real(z),y=imag(z)
;Fx=function in x
;Fy=function in y
;x=x-t*Fy,y=y+t*Fx
;z=x+flip(y)
;|z|<=bailout}

;
;
;comment{Chebyshev Types:
;       Inspired by Clifford A. Pickover:
;       Dynamic (Euler method)
;}



T02-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; Chebyshev Types:
        ; Inspired by Clifford A. Pickover:
        ; Dynamic (Euler method)
        ;
        ; T(n+1) = 2xT(n)-T(n-1)
        ; T(0)  = 1
        ; T(1)  = x
        ;
        ; = 2zT01-T00
  t=p1, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Tx=(x+x)*x-1
  Ty=(y+y)*y-1
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


T03-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = 2zT02-T01
  t=p1, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Tx=x*(4*x*x-3)
  Ty=y*(4*y*y-3)
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


T04-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = 2zT03-T02
  t=p1, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  xx=x*x, yy=y*y
  Tx=8*xx*(xx-1)+1
  Ty=8*yy*(yy-1)+1
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


T05-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = 2zT04-T03
  t=p1, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  ax=4*x*x, ay=4*y*y
  Tx=x*(ax*(ax-5)+5)
  Ty=x*(ay*(ay-5)+5)
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


T06-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = 2zT05-T04
  t=p1, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  xx=x*x, yy=y*y
  ax=xx+xx, ay=yy+yy
  Tx=ax*(8*xx*(ax-3)+9)-1
  Ty=ay*(8*yy*(ay-3)+9)-1
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


T07-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = 2zT06-T05
  t=p1, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  xx=x*x, yy=y*y
  Tx=x*(8*xx*((xx+xx)*(4*xx-7)+7)-7)
  Ty=y*(8*yy*((yy+yy)*(4*yy-7)+7)-7)
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


T08-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = 2zT07-T06
  t=p1, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  xx=x*x, yy=y*y
  Tx=32*xx*(xx*(4*xx*(xx-2)+5)-1)+1
  Ty=32*yy*(yy*(4*yy*(yy-2)+5)-1)+1
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


T09-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = 2zT08-T07
  t=p1, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  xx=x*x, yy=y*y
  ax=4*xx, ay=4*yy
  Tx=x*(8*xx*((xx+xx)*(ax*(ax-9)+27)-15)+9)
  Ty=y*(8*yy*((yy+yy)*(ay*(ay-9)+27)-15)+9)
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


T10-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = 2zT09-T08
  t=p1, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  xx=x*x, yy=y*y
  ax=xx+xx, ay=yy+yy
  bx=8*xx, by=8*yy
  Tx=ax*(bx*(ax*(bx*(ax-5)+35)-11)+25)-1
  Ty=ay*(by*(ay*(by*(ay-5)+35)-11)+25)-1
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}



U02-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; Chebyshev Types:
        ; Inspired by Clifford A. Pickover:
        ;
        ; Dynamic (Euler method)
        ; U(n+1) = 2xU(n)-U(n-1)
        ; U(0)  = 1
        ; U(1)  = 2x
        ;
        ; = 2zU01-U00
  t=p1, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Tx=4*x*x-1
  Ty=4*y*y-1
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


U03-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = 2zU02-U01
  t=p1, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Tx=4*x*((x+x)*x-1)
  Ty=4*y*((y+y)*y-1)
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


U04-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = 2zU03-U02
  t=p1, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  ax=4*x*x, ay=4*y*y
  Tx=ax*(ax-3)+1
  Ty=ay*(ay-3)+1
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


U05-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = 2zU04-U03
  t=p1, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  xx=x*x, yy=y*y
  Tx=(x+x)*(16*xx*(xx-1)+3)
  Ty=(y+y)*(16*yy*(yy-1)+3)
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


U06-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = 2zU05-U04
  t=p1, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  xx=x*x, yy=y*y
  Tx=8*xx*((xx+xx)*(4*xx-5)+3)-1
  Ty=8*yy*((yy+yy)*(4*yy-5)+3)-1
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


U07-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = 2zU06-U05
  t=p1, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  xx=x*x, yy=y*y
  ax=xx+xx, ay=yy+yy
  Tx=8*x*(ax*(4*xx*(ax-3)+5)-1)
  Ty=8*y*(ay*(4*yy*(ay-3)+5)-1)
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


U08-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = 2zU07-U06
  t=p1, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  xx=x*x, yy=y*y
  ax=4*xx, ay=4*yy
  Tx=8*xx*((xx+xx)*(ax*(ax-7)+15)-5)+1
  Ty=8*yy*((yy+yy)*(ay*(ay-7)+15)-5)+1
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


U09-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = 2zU08-U07
  t=p1, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  xx=x*x, yy=y*y
  ax=16*xx, ay=16*yy
  Tx=(x+x)*(ax*(xx*(ax*(xx-2)+17)-5)-3)
  Ty=(y+y)*(ay*(yy*(ay*(yy-2)+17)-5)-3)
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


U10-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = 2zU09-U08
  t=p1, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  xx=x*x, yy=y*y
  ax=4*xx, ay=4*yy
  Tx=ax*(ax*(16*xx*(xx*(ax-9)+6)-35)+7)-1
  Ty=ay*(ay*(16*yy*(yy*(ay-9)+6)-35)+7)-1
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}



S02-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; Chebyshev Types:
        ; Inspired by Clifford A. Pickover:
        ; Dynamic (Euler method)
        ;
        ; S(n+1) = xS(n)-S(n-1)
        ; S(0)  = 1
        ; S(1)  = x
        ;
        ; = zS01-S00
  t=p1, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Tx=x*x-1
  Ty=y*y-1
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


S03-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = zS02-S01
  t=p1, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Tx=x*(x*x-2)
  Ty=y*(y*y-2)
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


S04-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = zS03-S02
  t=p1, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  xx=x*x, yy=y*y
  Tx=xx*(xx-3)+1
  Ty=yy*(yy-3)+1
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


S05-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = zS04-S03
  t=p1, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  xx=x*x, yy=y*y
  Tx=x*(xx*(xx-4)+3)
  Ty=y*(yy*(yy-4)+3)
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


S06-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = zS05-S04
  t=p1, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  xx=x*x, yy=y*y
  Tx=xx*(xx*(xx-5)+6)-1
  Ty=yy*(yy*(yy-5)+6)-1
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


S07-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = zS06-S05
  t=p1, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  xx=x*x, yy=y*y
  Tx=x*(xx*(xx*(xx-6)+10)-4)
  Ty=y*(yy*(yy*(yy-6)+10)-4)
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


S08-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = zS07-S06
  t=p1, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  xx=x*x, yy=y*y
  Tx=xx*(xx*(xx*(xx-7)+15)-10)+1
  Ty=yy*(yy*(yy*(yy-7)+15)-10)+1
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


S09-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = zS08-S07
  t=p1, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  xx=x*x, yy=y*y
  Tx=x*(xx*(xx*(xx*(xx-8)+21)-20)+5)
  Ty=y*(yy*(yy*(yy*(yy-8)+21)-20)+5)
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


S10-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = zS09-S08
  t=p1, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  xx=x*x, yy=y*y
  Tx=xx*(xx*(xx*(xx*(xx-9)+28)-35)+15)-1
  Ty=yy*(yy*(yy*(yy*(yy-9)+28)-35)+15)-1
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}



C02-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; Chebyshev Types:
        ; Inspired by Clifford A. Pickover:
        ; Dynamic (Euler method)
        ;
        ; C(n+1) = xC(n)-C(n-1)
        ; C(0)  = 2
        ; C(1)  = x
        ;
        ; = zC01-C00
  t=p1, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Tx=x*x-2
  Ty=y*y-2
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


C03-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = zC02-C01
  t=p1, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Tx=x*(x*x-3)
  Ty=y*(y*y-3)
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


C04-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = zC03-C02
  t=p1, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  xx=x*x, yy=y*y
  Tx=xx*(xx-4)+2
  Ty=yy*(yy-4)+2
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


C05-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = zC04-C03
  t=p1, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  xx=x*x, yy=y*y
  Tx=x*(xx*(xx-5)+3)
  Ty=y*(yy*(yy-5)+3)
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


C06-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = zC05-C04
  t=p1, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  xx=x*x, yy=y*y
  Tx=xx*(xx*(xx-6)+7)-2
  Ty=yy*(yy*(yy-6)+7)-2
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


C07-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = zC06-C05
  t=p1, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  xx=x*x, yy=y*y
  Tx=x*(xx*(xx*(xx-7)+12)-5)
  Ty=y*(yy*(yy*(yy-7)+12)-5)
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


C08-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = zC07-C06
  t=p1, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  xx=x*x, yy=y*y
  Tx=xx*(xx*(xx*(xx-8)+18)-12)+2
  Ty=yy*(yy*(yy*(yy-8)+18)-12)+2
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


C09-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = zC08-C07
  t=p1, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  xx=x*x, yy=y*y
  Tx=x*(xx*(xx*(xx*(xx-9)+25)-24)+7)
  Ty=y*(yy*(yy*(yy*(yy-9)+25)-24)+7)
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


C10-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = zC09-C08
  t=p1, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  xx=x*x, yy=y*y
  Tx=xx*(xx*(xx*(xx*(xx-10)+33)-42)+19)-2
  Ty=yy*(yy*(yy*(yy*(yy-10)+33)-42)+19)-2
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}



P02-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens        
        ; Chebyshev Types:
        ; Inspired by Clifford A. Pickover:
        ; Dynamic (Euler method)
        ;
        ; P(n+1) = ((2n+1)xP(n)-nP(n-1))/(n+1)
        ; P(0)  = 1
        ; P(1)  = x
        ;
        ; = (3zP01-P00)/2
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Tx=(3*x*x-1)/2
  Ty=(3*y*y-1)/2
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


P03-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens        
        ; = (5zP02-2P01)/3
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Tx=x*(5*x*x-3)/2
  Ty=y*(5*y*y-3)/2
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


P04-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens        
        ; = (7zP03-3P02)/4
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  xx=x*x, yy=y*y
  Tx=(5*xx*(7*xx-6)+3)/8
  Ty=(5*yy*(7*yy-6)+3)/8
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


P05-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens        
        ; = (9zP04-4P03)/5
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  xx=x*x, yy=y*y
  Tx=x*(7*xx*(9*xx-10)+15)/8
  Ty=y*(7*yy*(9*yy-10)+15)/8
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


P06-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens        
        ; = (11zP05-5P04)/6
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  xx=x*x, yy=y*y
  Tx=(21*xx*(xx*(11*xx-15)+5)-5)/16
  Ty=(21*yy*(yy*(11*yy-15)+5)-5)/16
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


P07-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens        
        ; = (13zP06-6P05)/7
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  xx=x*x, yy=y*y
  Tx=x*(3*xx*(11*xx*(13*xx-21)+105)-35)/16
  Ty=y*(3*yy*(11*yy*(13*yy-21)+105)-35)/16
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


P08-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens        
        ; = (15zP07-7P06)/8
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  xx=x*x, yy=y*y
  Tx=(3*xx*(11*xx*(13*xx*(15*xx-28)+210)-420)+35)/128
  Ty=(3*yy*(11*yy*(13*yy*(15*yy-28)+210)-420)+35)/128
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


P09-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens        
        ; = (17zP08-8P07)/9
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  xx=x*x, yy=y*y
  Tx=x*(11*xx*(13*xx*(5*xx*(17*xx-36)+126)-420)+315)/128
  Ty=y*(11*yy*(13*yy*(5*yy*(17*yy-36)+126)-420)+315)/128
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


P10-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens        
        ; = (19zP09-9P08)/10
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  xx=x*x, yy=y*y
  Tx=(11*xx*(13*xx*(xx*(17*xx*(19*xx-45)+630)-210)+315)-63)/128
  Ty=(11*yy*(13*yy*(yy*(17*yy*(19*yy-45)+630)-210)+315)-63)/128
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}



H02-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; Chebyshev Types:
        ; Inspired by Clifford A. Pickover:
        ; Dynamic (Euler method)
        ;
        ; H(n+1) = 2(xH(n)-nH(n-1))
        ; H(0)  = 1
        ; H(1)  = 2x
        ;
        ; = 2(xH(1)-H(0))
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Tx=(x+x)*x-1
  Tx=Tx+Tx
  Ty=(y+y)*y-1
  Ty=Ty+Ty
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


H03-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = 2(xH(2)-2H(1))
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Tx=4*x*((x+x)*x-3)
  Ty=4*y*((y+y)*y-3)
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


H04-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = 2(xH(3)-3H(2))
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  xx=x*x, yy=y*y
  Tx=4*(4*xx*(xx-3)+3)
  Ty=4*(4*yy*(yy-3)+3)
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


H05-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = 2(xH(4)-4H(3))
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  xx=x*x, yy=y*y
  Tx=8*x*(4*xx*(xx-5)-9)
  Ty=8*y*(4*yy*(yy-5)-9)
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


H06-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = 2(xH(5)-5H(4))
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  ax=(x+x)*x, ay=(y+y)*y
  Tx=8*(ax*(ax*(ax-15)+21)-15)
  Ty=8*(ay*(ay*(ay-15)+21)-15)
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


H07-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = 2(xH(6)-6H(5))
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  ax=(x+x)*x, ay=(y+y)*y
  Tx=16*x*(ax*(ax*(ax-21)+81)+39)
  Ty=16*y*(ay*(ay*(ay-21)+81)+39)
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


H08-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = 2(xH(7)-7H(6))
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  xx=x*x, yy=y*y
  ax=xx+xx, ay=yy+yy
  Tx=16*(4*xx*(ax*(ax*(xx-14)+93)-93)+105)
  Ty=16*(4*yy*(ay*(ay*(yy-14)+93)-93)+105)
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


H09-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = 2(xH(8)-8H(7))
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  xx=x*x, yy=y*y
  ax=xx+xx, ay=yy+yy
  Tx=32*x*(4*xx*(ax*(ax*(xx-18)+177)-417)-207)
  Ty=32*y*(4*yy*(ay*(ay*(yy-18)+177)-417)-207)
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


H10-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = 2(xH(9)-9H(8))
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  xx=x*x, yy=y*y
  ax=xx+xx, ay=yy+yy
  Tx=32*(ax*(4*xx*(ax*(xx*(ax-45)+303)-1254)+1467)-945)
  Ty=32*(ay*(4*yy*(ay*(yy*(ay-45)+303)-1254)+1467)-945)
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}



He02-01 {; V.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; Chebyshev Types:
         ; Inspired by Clifford A. Pickover:
         ; Dynamic (Euler method)
         ;
         ; He(n+1) = xHe(n)-nHe(n-1)
         ; He(0)  = 1
         ; He(1)  = sqrt(2)x
         ;
         ; = xHe(1)-He(0)
  s=sqrt(2), t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Tx=s*x*x-1
  Ty=s*y*y-1
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


He03-01 {; V.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = xHe(2)-2He(1)
  s=sqrt(2), t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Tx=x*(s*(x*x-2)-1)
  Ty=y*(s*(y*y-2)-1)
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


He04-01 {; V.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = xHe(3)-3He(2)
  s=sqrt(2), t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  xx=x*x, yy=y*y
  Tx=xx*(s*(xx-5)-1)+3
  Ty=yy*(s*(yy-5)-1)+3
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


He05-01 {; V.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = xHe(4)-4He(3)
  s=sqrt(2), a=8*s+7
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  xx=x*x, yy=y*y
  Tx=x*(xx*(s*(xx-9)-1)+a)
  Ty=y*(yy*(s*(yy-9)-1)+a)
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


He06-01 {; V.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = xHe(5)-5He(4)
  s=sqrt(2), a=33*s+12
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  xx=x*x, yy=y*y
  Tx=xx*(xx*(s*(xx-14)-1)+a)-15
  Ty=yy*(yy*(s*(yy-14)-1)+a)-15
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


He07-01 {; V.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = xHe(6)-6He(5)
  s=sqrt(2), a=87*s+18, b=8*s-57
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  xx=x*x, yy=y*y
  Tx=x*(xx*(xx*(s*(xx-20)-1)+a)+b)
  Ty=y*(yy*(yy*(s*(yy-20)-1)+a)+b)
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


He08-01 {; V.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = xHe(7)-7He(6)
  s=sqrt(2), a=185*s+25, b=41*s-141
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  xx=x*x, yy=y*y
  Tx=xx*(xx*(xx*(s*(xx-27)-1)+a)+b)+105
  Ty=yy*(yy*(yy*(s*(yy-27)-1)+a)+b)+105
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


He09-01 {; V.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = xHe(8)-8He(7)
  s=sqrt(2), a=345*s+33, b=136*s-285
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  xx=x*x, yy=y*y
  Tx=x*(xx*(xx*(xx*(s*(xx-35)-1)+a)+b)+561)
  Ty=y*(yy*(yy*(yy*(s*(yy-35)-1)+a)+b)+561)
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


He10-01 {; V.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = xHe(9)-9He(8)
  s=sqrt(2), a=588*s+42, b=321*s-510, c=41*s-1830
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  xx=x*x, yy=y*y
  Tx=xx*(xx*(xx*(xx*(s*(xx-44)-1)+a)+b)+c)-945
  Ty=yy*(yy*(yy*(yy*(s*(yy-44)-1)+a)+b)+c)-945
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}



Ca02-01 {; V.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = (a+1)xCa(1)-aCa(0)
         ; Chebyshev Types:
         ; Inspired by Clifford A. Pickover:
         ; Dynamic (Euler method)
         ; Ca(n+1) = (2(a+n)xCa(n)-(2a+n-1)Ca(n-1))/(n+1)
         ; Ca(0) = 1
         ;
         ; Ca(1) = 2ax
  a=p2, b=a+a+2
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Tx=a*(b*x*x-1)
  Ty=a*(b*y*y-1)
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


Ca03-01 {; V.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = (2(a+2)xCa(2)-(2a+1)Ca(1))/3
  a=p2, b=(a+a)*(a+1), c=(a+a+4)/3
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Tx=b*x*(c*x*x-1)
  Ty=b*y*(c*y*y-1)
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


Ca04-01 {; V.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = ((a+3)xCa(3)-(a+1)Ca(2))/2
  a=p2, b=a*(a+1)/2, c=4*(a+2), d=(a+3)/3
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  xx=x*x, yy=y*y
  Tx=b*(c*xx*(d*xx-1)+1)
  Ty=b*(c*yy*(d*yy-1)+1)
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


Ca05-01 {; V.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = (2(a+4)xCa(4)-(2a+3)Ca(3))/5
  a=p2, b=a*(a*(a+3)+2)/3, c=4*(a+3), d=(a+4)/5
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  xx=x*x, yy=y*y
  Tx=b*x*(c*xx*(d*xx-1)+3)
  Ty=b*y*(c*yy*(d*yy-1)+3)
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


Ca06-01 {; V.1.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = ((a+5)xCa(5)-(a+2)Ca(4))/3
  a=p2, b=a*(a*(a+3)+2)/6, c=a+3, d=4*(a+4), k=(a+a+10)/15
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  xx=x*x, yy=y*y
  Tx=b*(c*xx*(d*xx*(k*xx-1)+3)-1)
  Ty=b*(c*yy*(d*yy*(k*yy-1)+3)-1)
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


Ca07-01 {; V.1.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = (2(a+6)xCa(6)-(2a+5)Ca(5))/7
  a=p2, b=a*(a*(a*(a+6)+11)+6)/21, c=a+a+8
  d=((a+a)*(a+11)+60)/15, k=7*(a+5)/5
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  xx=x*x, yy=y*y
  Tx=b*x*(c*xx*((xx+xx)*(d*xx-k)+7)-7)
  Ty=b*y*(c*yy*((yy+yy)*(d*yy-k)+7)-7)
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


Ca08-01 {; V.1.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = ((a+7)xCa(7)-(a+3)Ca(6))/4
  a=p2, b=a*(a*(a*(a+6)+11)+6)/360, c=8*(a+4)
  d=a+5, k=4*(a+6), f=(a+7)/14
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  xx=x*x, yy=y*y
  Tx=b*(c*xx*(d*xx*(k*xx*(f*xx-1)+15)-15)+15)
  Ty=b*(c*yy*(d*yy*(k*yy*(f*yy-1)+15)-15)+15)
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


Ca09-01 {; V.1.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = (2(a+8)xCa(8)-(2a+7)Ca(7))/9
  a=p2, b=a*(a*(a*(a*(a+10)+35)+50)+24)/1260
  c=a*(a*(a+a+36)+214)+420, d=(a+8)/18
  k=7*(a*(9*a+94)+270)/6, f=35*(a+5)/2
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  xx=x*x, yy=y*y
  Tx=b*x*(16*xx*(xx*(c*xx*(d*xx-1)+k)-f)+105)
  Ty=b*y*(16*yy*(yy*(c*yy*(d*yy-1)+k)-f)+105)
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


Ca10-01 {; V.1.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = ((a+9)xCa(9)-(a+4)Ca(8))/5
  a=p2, b=a*(a*(a*(a*(a+10)+35)+50)+24)/382860
  c=15*(a+5), d=a+a+12, k=a*(a+15)+56, f=(a+a+18)/45
  g=14*(a+a+13)/5
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  xx=x*x, yy=y*y
  Tx=b*(c*xx*(d*xx*(81*xx*(k*xx*(f*xx-1)+g)-1418)+2127)-31903)
  Ty=b*(c*yy*(d*yy*(81*yy*(k*yy*(f*yy-1)+g)-1418)+2127)-31903)
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}



Tc02-01 {; V.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; Chebyshev Types:
         ; Inspired by Clifford A. Pickover:
         ; Dynamic (Euler method)
         ;
         ; Tc(n+1) = 2(2x-1)Tc(n)-Tc(n-1)
         ; Tc(0) = 1
         ; Tc(1) = 2(x+1)
         ;
         ; = 2(2z-1)Tc(1)-Tc(0)
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Tx=4*x*(x+x+1)-5
  Ty=4*y*(y+y+1)-5
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


Tc03-01 {; V.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = 2(2z-1)Tc(2)-Tc(1)
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Tx=(x+x)*(16*x*x-15)+8
  Ty=(y+y)*(16*y*y-15)+8
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


Tc04-01 {; V.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = 2(2z-1)Tc(3)-Tc(2)
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  ax=8*x, ay=8*y
  Tx=ax*(ax*(x*(x+x-1)-2)+11)-11
  Ty=ay*(ay*(y*(y+y-1)-2)+11)-11
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


Tc05-01 {; V.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = 2(2z-1)Tc(4)-Tc(3)
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  ax=16*x, ay=16*y
  Tx=(x+x)*(ax*(x*(ax*(x-1)-13)+19)-95)+14
  Ty=(y+y)*(ay*(y*(ay*(y-1)-13)+19)-95)+14
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


Tc06-01 {; V.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = 2(2z-1)Tc(5)-Tc(4)
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  ax=x+x, ay=y+y
  bx=ax+ax, by=ay+ay
  Tx=bx*(ax*(32*x*(x*(bx*(ax-3)-3)+13)-231)+87)-17
  Ty=by*(ay*(32*y*(y*(by*(ay-3)-3)+13)-231)+87)-17
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


Tc07-01 {; V.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = 2(2z-1)Tc(6)-Tc(5)
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Tx=(x+x)*(32*x*(x*(8*x*(x*(16*x*(x-2)+5)+30)-213)+71)-287)+20
  Ty=(y+y)*(32*y*(y*(8*y*(y*(16*y*(y-2)+5)+30)-213)+71)-287)+20
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


Tc08-01 {; V.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = 2(2z-1)Tc(7)-Tc(6)
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  ax=x+x, ay=y+y
  bx=ax+ax, by=ay+ay
  cx=16*x, cy=16*y
  Tx=cx*(bx*(ax*(cx*(x*(bx*(ax*(ax-5)+5)+29)+420+329)-149)+55)-23)
  Ty=cy*(by*(ay*(cy*(y*(by*(ay*(ay-5)+5)+29)+420+329)-149)+55)-23)
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


Tc09-01 {; V.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = 2(2z-1)Tc(8)-Tc(7)
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  ax=8*x, ay=8*y
  Tx=(x+x)*(32*x*(x*(ax*(x*(16*x*(x*(ax*(x+x-7)+59)+11)+435)-37)+1041)+282)-639)+26
  Ty=(y+y)*(32*y*(y*(ay*(y*(16*y*(y*(ay*(y+y-7)+59)+11)+435)-37)+1041)+282)-639)+26
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


Tc10-01 {; V.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = 2(2z-1)Tc(9)-Tc(8)
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  ax=4*x, ay=4*y
  bx=32*x, by=32*y
  cx=x+x, cy=y+y
  Tx=ax*(cx*(bx*(x*(ax*(cx*(bx*(x*(8*x*(x-4)+43)-8)+327)-567)+853)-403)-3959)+445)-29
  Ty=ay*(cy*(by*(y*(ay*(cy*(by*(y*(8*y*(y-4)+43)-8)+327)-567)+853)-403)-3959)+445)-29
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}



L02-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; Chebyshev Types:
        ; Inspired by Clifford A. Pickover:
        ; Dynamic (Euler method)
        ;
        ; L(n+1) = ((2n+1-z)L(n)-nL(n-1))/(n+1)
        ; L(0)=1
        ; L(1)=(1-z)
        ;
        ; = ((3-z)L(1)-L(0))/2
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Tx=x*(x/2-2)+1
  Ty=y*(y/2-2)+1
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


L03-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = ((5-z)L(2)-2L(1))/3
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Tx=x*(x*(3-x/3)/2-3)+1
  Ty=y*(y*(3-y/3)/2-3)+1
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


L04-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = ((7-z)L(3)-3L(2))/4
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Tx=x*(x*(x*(x/8-2)/3+3)-4)+1
  Ty=y*(y*(y*(y/8-2)/3+3)-4)+1
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


L05-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = ((9-z)L(4)-4L(3))/5
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Tx=x*(x*(x*(x*(5-x/5)/8-5)/3+5)-5)+1
  Ty=y*(y*(y*(y*(5-y/5)/8-5)/3+5)-5)+1
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


L06-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = ((11-z)L(5)-5L(4))/6
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Tx=x*(x*(x*(x*(x*(x/18-2)/5+5)/8-10/3)+15/2)-6)+1
  Ty=y*(y*(y*(y*(y*(y/18-2)/5+5)/8-10/3)+15/2)-6)+1
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


L07-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = ((13-z)L(6)-6L(5))/7
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Tx=x*(x*(x*(x*(x*(x*(49-x)/2-441)/5+735)/84-35)/3+21)/2-7)+1
  Ty=y*(y*(y*(y*(y*(y*(49-y)/2-441)/5+735)/84-35)/3+21)/2-7)+1
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


L08-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = ((15-z)L(7)-7L(6))/8
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Tx=x*(x*(x*(x*(x*(x*(x*(x/32-2)/7+7)/3-28)/5+35)/4-28)/3+14)-8)+1
  Ty=y*(y*(y*(y*(y*(y*(y*(y/32-2)/7+7)/3-28)/5+35)/4-28)/3+14)-8)+1
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


L09-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = ((17-z)L(8)-8L(7))/9
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Tx=x*(x*(x*(x*(x*(x*(x*(x*(81-x)/16-162)+2646)-23814)/5+23814)-84)+108)/17-9)+1
  Ty=y*(y*(y*(y*(y*(y*(y*(y*(81-y)/16-162)+2646)-23814)/5+23814)-84)+108)/17-9)+1
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


L10-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = ((19-z)L(9)-9L(8))/10
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Tx=x*(x*(x*(x*(x*(x*(x*(x*(x*(x/100-1)+405)/8-108)+1323)/2-47628)+19845)/2-22680)+27025)/1134-10)+1
  Ty=y*(y*(y*(y*(y*(y*(y*(y*(y*(y/100-1)+405)/8-108)+1323)/2-47628)+19845)/2-22680)+27025)/1134-10)+1
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}



La02-01 {; V.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; Chebyshev Types:
         ; Inspired by Clifford A. Pickover:
         ; Dynamic (Euler method)
         ;
         ; La(n+1) = ((a+2n+1-z)La(n)-(a+n)La(n-1))/(n+1)
         ; La(0)=1
         ; La(1)=(a+1-z)
         ;
         ; = ((a+3-z)La(1)-(a+1)La(0))/2
  a=p2, c=a+2, b=c*(a+1)/2
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Tx=x*(x/2-c)+b
  Ty=y*(y/2-c)+b
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


La03-01 {; V.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = ((a+5-z)La(2)-(a+2)La(1))/3
  a=p2, d=(a+3)/2, c=d*(a+2), b=c*(a+1)/3
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Tx=x*(x*(d-x/6)-c)+b
  Ty=y*(y*(d-y/6)-c)+b
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


La04-01 {; V.1.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = ((a+7-z)La(3)-(a+3)La(2))/4
  a=p2, k=(a+4)/6, d=k*(a+3)*(3/2), c=d*(a+2)*(2/3), b=c*(a+1)/4
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Tx=x*(x*(x*(x/24-k)+d)-c)+b
  Ty=y*(y*(y*(y/24-k)+d)-c)+b
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


La05-01 {; V.1.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = ((a+9-z)La(4)-(a+4)La(3))/5
  a=p2, f=(a+5)/24, k=(f+f)*(a+4), d=k*(a+3), c=d*(a+2)/2, b=c*(a+1)/5
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Tx=x*(x*(x*(x*(f-x/120)-k)+d)-c)+b
  Ty=y*(y*(y*(y*(f-y/120)-k)+d)-c)+b
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


La06-01 {; V.1.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = ((a+11-z)La(5)-(a+5)La(4))/6
  a=p2, g=(a+6)/120, f=g*(a+5)*(5/2), k=f*(a+4)*(4/3)
  d=k*(a+3)*(3/4), c=d*(a+2)*(2/5), b=c*(a+1)/6
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Tx=x*(x*(x*(x*(x*(x/720-g)+f)-k)+d)-c)+b
  Ty=y*(y*(y*(y*(y*(y/720-g)+f)-k)+d)-c)+b
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


La07-01 {; V.1.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = ((a+13-z)La(6)-(a+6)La(5))/7
  a=p2, h=(a+7)/720, g=h*(a+6)*3, f=g*(a+5)*(5/3), k=f*(a+4)
  d=k*(a+3)*(3/5), c=d*(a+2)/3, b=c*(a+1)/7
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Tx=x*(x*(x*(x*(x*(x*(h-x/5040)-g)+f)-k)+d)-c)+b
  Ty=y*(y*(y*(y*(y*(y*(h-y/5040)-g)+f)-k)+d)-c)+b
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


La08-01 {; V.1.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = ((a+15-z)La(7)-(a+7)La(6))/8
  a=p2, i=(a+8)/5040, h=i*(a+7)*(7/2), g=h*(a+6)*2
  f=g*(a+5)*(5/4), k=f*(a+4)*(4/5), d=k*(a+3)/2
  c=d*(a+2)*(2/7),b=c*(a+1)/8
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Tx=x*(x*(x*(x*(x*(x*(x*(x/40320-i)+h)-g)+f)-k)+d)-c)+b
  Ty=y*(y*(y*(y*(y*(y*(y*(y/40320-i)+h)-g)+f)-k)+d)-c)+b
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


La09-01 {; V.1.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = ((a+17-z)La(8)-(a+8)La(7))/9
  a=p2, j=(a+9)/40320, i=j*(a+8)*4, h=i*(a+7)*(7/3)
  g=h*(a+6)*(3/2), f=g*(a+5), k=f*(a+4)*(2/3), d=k*(a+3)*(3/7)
  c=d*(a+2)/4, b=c*(a+1)/9
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Tx=x*(x*(x*(x*(x*(x*(x*(x/40320-i)+h)-g)+f)-k)+d)-c)+b
  Ty=y*(y*(y*(y*(y*(y*(y*(y/40320-i)+h)-g)+f)-k)+d)-c)+b
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


La10-01 {; V.1.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = ((a+19-z)La(9)-(a+9)La(8))/10
  a=p2, k=(a+10)/362880, j=k*(a+9)*45, i=j*(a+8)*(4/15)
  h=i*(a+7)*(7/4), g=h*(a+6)*12, f=g*(a+5)/12
  l=f*(a+4)*(4/7), d=l*(a+3)*(15/4), c=d*(a+2)/45, b=c*(a+1)/10
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Tx=x*(x*(x*(x*(x*(x*(x*(x*(x*(x/3628800-k)+j)-i)+h)-g)+f)-l)+d)-c)+b
  Ty=y*(y*(y*(y*(y*(y*(y*(y*(y*(y/3628800-k)+j)-i)+h)-g)+f)-l)+d)-c)+b
  x=x-t*Ty,y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}



Uc02-01 {; V.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; Chebyshev Types:
         ; Inspired by Clifford A. Pickover:
         ; Dynamic (Euler method)
         ;
         ; Uc(n+1) = 2(2z-1)Uc(n)-Uc(n-1)
         ; a=4z-2
         ; Uc(0)  = 1
         ; Uc(1)  = a
         ;
         ; = 2z(2z-1)U01-U00
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  ax=4*x-2, ay=4*y-2
  Tx=ax*ax-1
  Ty=ay*ay-1
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


Uc03-01 {; V.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = 2z(2z-1)U02-U01
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  ax=4*x-2, ay=4*y-2
  Tx=ax*(ax*ax-2)
  Ty=ay*(ay*ay-2)
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


Uc04-01 {; V.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = 2z(2z-1)U03-U02
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  ax=4*x-2, ay=4*y-2
  aax=ax*ax, aay=ay*ay
  Tx=aax*(aax-3)+1
  Ty=aay*(aay-3)+1
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


Uc05-01 {; V.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = 2z(2z-1)U04-U03
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  ax=4*x-2, ay=4*y-2
  aax=ax*ax, aay=ay*ay
  Tx=ax*(aax*(aax-4)+3)
  Ty=ay*(aay*(aay-4)+3)
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


Uc06-01 {; V.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = 2z(2z-1)U05-U04
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  ax=4*x-2, ay=4*y-2
  aax=ax*ax, aay=ay*ay
  Tx=aax*(aax*(aax-5)+6)-1
  Ty=aay*(aay*(aay-5)+6)-1
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


Uc07-01 {; V.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = 2z(2z-1)U06-U05
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  ax=4*x-2, ay=4*y-2
  aax=ax*ax, aay=ay*ay
  Tx=ax*(aax*(aax*(aax-6)+10)-4)
  Ty=ay*(aay*(aay*(aay-6)+10)-4)
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


Uc08-01 {; V.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = 2z(2z-1)U07-U06
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  ax=4*x-2, ay=4*y-2
  aax=ax*ax, aay=ay*ay
  Tx=aax*(aax*(aax*(aax-7)+15)-10)+1
  Ty=aay*(aay*(aay*(aay-7)+15)-10)+1
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


Uc09-01 {; V.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = 2z(2z-1)U08-U07
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  ax=4*x-2, ay=4*y-2
  aax=ax*ax, aay=ay*ay
  Tx=ax*(aax*(aax*(aax*(aax-8)+21)-20)+5)
  Ty=ay*(aay*(aay*(aay*(aay-8)+21)-20)+5)
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}


Uc10-01 {; V.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = 2z(2z-1)U09-U08
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  ax=4*x-2, ay=4*y-2
  aax=ax*ax, aay=ay*ay
  Tx=aax*(aax*(aax*(aax*(aax-9)+36)-35)+15)-1
  Ty=aay*(aay*(aay*(aay*(aay-9)+36)-35)+15)-1
  x=x-t*Ty, y=y+t*Tx
  z=x+flip(y)
  |z|<=bailout
}



Pc02-01 {; V.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; Chebyshev Types
         ; Inspired by Clifford A. Pickover
         ;
         ; Dynamic (Euler method)
         ; Pc[0] = 1
         ; Pc[1] = 2z-1
         ; Pc[n+1] = ((2((n+1)z-n)-1)Pc[n]-nPc[n-1])/(n+1)
         ;
         ; = Pc[2] = ((2(2z-1)-1)Pc[1]-Pc[0])/2
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Fx=(4*x-5)*x+1
  Fy=(4*y-5)*y+1
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}


Pc03-01 {; V.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = Pc[3] = ((2(3z-2)-1)Pc[2]-2Pc[1])/3
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Fx=((8*x-50/3)*x+9)*x-1
  Fy=((8*y-50/3)*y+9)*y-1
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}


Pc04-01 {; V.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = Pc[4] = ((2(4z-3)-1)Pc[3]-3Pc[2])/4
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Fx=(((16*x-142/3)*x+265/6)*x-14)*x+1
  Fy=(((16*y-142/3)*y+265/6)*y-14)*y+1
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}


Pc05-01 {; V.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = Pc[5] = ((2(5z-4)-1)Pc[4]-4Pc[3])/5
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Fx=((((32*x-1852/15)*x+2507/15)*x-565/6)*x+20)*x-1
  Fy=((((32*y-1852/15)*y+2507/15)*y-565/6)*y+20)*y-1
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}


Pc06-01 {; V.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = Pc[6] = ((2(6z-5)-1)Pc[5]-5Pc[4])/6
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Fx=(((((64*x-1528/5)*x+24628/45)*x-4553/10)*x+1055/6)*x-27)*x+1
  Fy=(((((64*y-1528/5)*y+24628/45)*y-4553/10)*y+1055/6)*y-27)*y+1
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}


Pc07-01 {; V.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = Pc[7] = ((2(7z-6)-1)Pc[6]-6Pc[5])/7
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Fx=((((((128*x-25552/35)*x+514928/315)*x-573667/315)*x+31619/30)*x-1799/6)*x+35)*x-1
  Fy=((((((128*y-25552/35)*y+514928/315)*y-573667/315)*y+31619/30)*y-1799/6)*y+35)*y-1
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}


Pc08-01 {; V.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = Pc[8] = ((2(8z-7)-1)Pc[7]-7Pc[6])/8
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Fx=(((((((256*x-59504/35)*x+1443406/315)*x-289799/45)*x+2542045/504)*x-32662/15)*x+1435/3)*x-44)*x+1
  Fy=(((((((256*y-59504/35)*y+1443406/315)*y-289799/45)*y+2542045/504)*y-32662/15)*y+1435/3)*y-44)*y+1
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}


Pc09-01 {; V.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = Pc[9] = ((2(9z-8)-1)Pc[8]-8Pc[7])/9
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Fx=((((((((512*x-1223392/315)*x+772508/63)*x-8458976/405)*x+26206517/1260)*x-2060215/168)*x+20664/5)*x-725)*x+54)*x-1
  Fy=((((((((512*y-1223392/315)*y+772508/63)*y-8458976/405)*y+26206517/1260)*y-2060215/168)*y+20664/5)*y-725)*y+54)*y-1
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}


Pc10-01 {; V.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = Pc[10] = ((2(10z-9)-1)Pc[9]-9Pc[8])/10
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Fx=(((((((((1024*x-2753216/315)*x+2375464/75)*x-900686282/14175)*x+312488741/4050)*x-4193867/72)*x+22702079/840)*x-36713/5)*x+1055)*x-65)*x+1
  Fy=(((((((((1024*y-2753216/315)*y+2375464/75)*y-900686282/14175)*y+312488741/4050)*y-4193867/72)*y+22702079/840)*y-36713/5)*y+1055)*y-65)*y+1
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}



O02-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; Chebyshev Types
        ; Inspired by Clifford A. Pickover
        ;
        ; Dynamic (Euler method)
        ; Neumann Polynomials
        ; O[0] = 1/z
        ; O[1] = 1/zz
        ; O[2] = (4/zz+1)/z
        ; O[n+1] = 2(n+1)O[n]/z-((n+1)/(n-1))O[n-1]+(2n/z)sin(n*pi/2)^2
        ;
        ; = O[2] = (4/zz+1)/z
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  x2=x*x, y2=y*y
  Fx=(x2+4)/(x2*x)
  Fy=(y2+4)/(y2*y)
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}


O03-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = O[3] = 6O[2]/z-3O[1]+(4/z)sin(2*pi/2)^2
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  x2=x*x, y2=y*y
  Fx=(((6-3*x)*x-12)*x+24)/(x2*x2)
  Fy=(((6-3*y)*y-12)*y+24)/(y2*y2)
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}


O04-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = O[4] = 8O[3]/z-2O[2]+(6/z)sin(3*pi/2)^2
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  x2=x*x, y2=y*y
  Fx=((((12*x-36)*x+72)*x-144)*x+192)/(x2*x2*x)
  Fy=((((12*y-36)*y+72)*y-144)*y+192)/(y2*y2*y)
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}


O05-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = O[5] = 10O[4]/z-(5/3)O[3]+(8/z)sin(4*pi/2)^2
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  x2=x*x, y2=y*y
  Fx=(((((180-20*x)*x-480)*x+960)*x-1760)*x+1920)/(x2*x2*x2)
  Fy=(((((180-20*y)*y-480)*y+960)*y-1760)*y+1920)/(y2*y2*y2)
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}


O06-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = O[6] = 12O[5]/z-(3/2)O[4]+(10/z)sin(5*pi/2)^2
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  x2=x*x, y2=y*y
  Fx=((((((40*x-510)*x+2880)*x-7200)*x+14160)*x-24000)*x+23040)/(x2*x2*x2*x)
  Fy=((((((40*y-510)*y+2880)*y-7200)*y+14160)*y-24000)*y+23040)/(y2*y2*y2*y)
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}


O07-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = O[7] = 14O[6]/z-(7/5)O[5]+(12/z)sin(6*pi/2)^2
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  x2=x*x, y2=y*y, x4=x2*x2, y4=y2*y2
  Fx=(((((((1274-56*x)*x-11172)*x+50400)*x-120624)*x+231840)*x-368256)*x+322560)/(x4*x4)
  Fy=(((((((1274-56*y)*y-11172)*y+50400)*y-120624)*y+231840)*y-368256)*y+322560)/(y4*y4)
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}


O08-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = O[8] = 16O[7]/z-(4/3)O[6]+(14/z)sin(7*pi/2)^2
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  x2=x*x, y2=y*y, x4=x2*x2, y4=y2*y2
  Fx=((((((((266/3*x-7784/3)*x+35280)*x-245952)*x+967232)*x-2239104)*x+4200448)*x-6322176)*x+5160960)/(x4*x4*x)
  Fy=((((((((266/3*y-7784/3)*y+35280)*y-245952)*y+967232)*y-2239104)*y+4200448)*y-6322176)*y+5160960)/(y4*y4*y)
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}


O09-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = O[9] = 18O[8]/z-(9/7)O[7]+(16/z)sin(8*pi/2)^2
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  x2=x*x, y2=y*y, x4=x2*x2, y4=y2*y2
  Fx=(((((((((4932-114*x)*x-92064)*x+951264)*x-5670720)*x+20289024)*x-45704448)*x+83736576)*x-120434688)*x+92897280)/(x4*x4*x2)
  Fy=(((((((((4932-114*y)*y-92064)*y+951264)*y-5670720)*y+20289024)*y-45704448)*y+83736576)*y-120434688)*y+92897280)/(y4*y4*y2)
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}


O10-01 {; V.1.1 - earlier versions may be discarded
        ; Copyright (c)1998,1999 Morgan L. Owens
        ; = O[10] = 20O[9]/z-(5/4)O[8]+(18/z)sin(9*pi/2)^2
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  x2=x*x, y2=y*y, x4=x2*x2, y4=y2*y2
  Fx=((((((((((321/2*x-8445)*x+213720)*x-3030360)*x+26113680)*x-138775680)*x+462911040)*x-1018759680)*x+1825274880)*x-2524815360)*x+1857945600)/(x4*x4*x2*x)
  Fy=((((((((((321/2*y-8445)*y+213720)*y-3030360)*y+26113680)*y-138775680)*y+462911040)*y-1018759680)*y+1825274880)*y-2524815360)*y+1857945600)/(y4*y4*y2*y)
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}



Sc02-01 {; V.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; Chebyshev Types
         ; Inspired by Clifford A. Pickover
         ;
         ; Schlafi Polynomials
         ; Sc[0] = 0
         ; Sc[1] = 0
         ; Sc[n+1] = 2(zO[n]-cos(n*pi/2)^2)/n
         ;
         ; = Sc[2]=2(zO[1]-cos(pi/2)^2)
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Fx=2/x
  Fy=2/y
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}


Sc03-01 {; V.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = Sc[3]=2(zO[2]-cos(2*pi/2)^2)/2
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Fx=4/(x*x)
  Fy=4/(y*y)
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}


Sc04-01 {; V.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = Sc[4]=2(zO[3]-cos(3*pi/2)^2)/3
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Fx=(((4-2*x)*x-8)*x+16)/(x*x*x)
  Fy=(((4-2*y)*y-8)*y+16)/(y*y*y)
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}


Sc05-01 {; V.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = Sc[5]=2(zO[4]-cos(4*pi/2)^2)/4
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  x2=x*x, y2=y*y
  Fx=((((11/2*x-18)*x+36)*x-72)*x+96)/(x2*x2)
  Fy=((((11/2*y-18)*y+36)*y-72)*y+96)/(y2*y2)
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}


Sc06-01 {; V.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = Sc[6]=2(zO[5]-cos(5*pi/2)^2)/5
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  x2=x*x, y2=y*y
  Fx=(((((72-8*x)*x-192)*x+384)*x-704)*x+768)/(x2*x2*x)
  Fy=(((((72-8*y)*y-192)*y+384)*y-704)*y+768)/(y2*y2*y)
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}


Sc07-01 {; V.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = Sc[7]=2(zO[6]-cos(6*pi/2)^2)/6
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  x2=x*x, y2=y*y
  Fx=((((((13*x-170)*x+960)*x-2400)*x+4720)*x-8000)*x+7680)/(x2*x2*x2)
  Fy=((((((13*y-170)*y+960)*y-2400)*y+4720)*y-8000)*y+7680)/(y2*y2*y2)
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}


Sc08-01 {; V.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = Sc[8]=2(zO[7]-cos(7*pi/2)^2)/7
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  x2=x*x, y2=y*y
  Fx=(((((((364-16*x)*x-3192)*x+14400)*x-34464)*x+66240)*x-105216)*x+92160)/(x2*x2*x2*x)
  Fy=(((((((364-16*y)*y-3192)*y+14400)*y-34464)*y+66240)*y-105216)*y+92160)/(y2*y2*y2*y)
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}


Sc09-01 {; V.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = Sc[9]=2(zO[8]-cos(8*pi/2)^2)/8
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  x2=x*x, y2=y*y, x4=x2*x2, y4=y2*y2
  Fx=((((((((263/12*x-1946/3)*x+8820)*x-61488)*x+241808)*x-559776)*x+1050112)*x-1580544)*x+1290240)/(x4*x4)
  Fy=((((((((263/12*y-1946/3)*y+8820)*y-61488)*y+241808)*y-559776)*y+1050112)*y-1580544)*y+1290240)/(y4*y4)
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}


Sc10-01 {; V.1.1 - earlier versions may be discarded
         ; Copyright (c)1998,1999 Morgan L. Owens
         ; = Sc[10]=2(zO[9]-cos(9*pi/2)^2)/9
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  x2=x*x, y2=y*y, x4=x2*x2, y4=y2*y2
  Fx=(((((((((1096-76/3*x)*x-61376/3)*x+211392)*x-1260160)*x+4508672)*x-10156544)*x+18608128)*x-26763264)*x+20643840)/(x4*x4*x)
  Fy=(((((((((1096-76/3*y)*y-61376/3)*y+211392)*y-1260160)*y+4508672)*y-10156544)*y+18608128)*y-26763264)*y+20643840)/(y4*y4*y)
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}



Exp02-01 {; V.1.1 - earlier versions may be discarded
          ; Copyright (c)1998,1999 Morgan L. Owens
          ; Chebyshev Types
          ; Inspired by Clifford A. Pickover 
          ;
          ; Dynamic (Euler method)
          ; Exponential Integral
          ; Exp[0] = exp(-z)/z
          ; Exp[1] = 0
          ; Exp[n+1] = (exp(-z)-zExp[n])/n
          ;
          ; = Exp[2] = (exp(-z)-zExp[1])
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Fx=exp(-x)
  Fy=exp(-y)
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}


Exp03-01 {; V.1.1 - earlier versions may be discarded
          ; Copyright (c)1998,1999 Morgan L. Owens
          ; = Exp[3] = (exp(-z)-zExp[2])/2
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Fx=(1-x)/(exp(x)*2)
  Fy=(1-y)/(exp(y)*2)
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}


Exp04-01 {; V.1.1 - earlier versions may be discarded
          ; Copyright (c)1998,1999 Morgan L. Owens
          ; = Exp[4] = (exp(-z)-zExp[3])/3
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Fx=((x-1)*x/6+1/3)/exp(x)
  Fy=((y-1)*y/6+1/3)/exp(y)
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}


Exp05-01 {; V.1.1 - earlier versions may be discarded
          ; Copyright (c)1998,1999 Morgan L. Owens
          ; = Exp[5] = (exp(-z)-zExp[4])/4
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Fx=(((1-x)*x/24-1/12)*x+1/4)/exp(x)
  Fy=(((1-y)*y/24-1/12)*y+1/4)/exp(y)
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}


Exp06-01 {; V.1.1 - earlier versions may be discarded
          ; Copyright (c)1998,1999 Morgan L. Owens
          ; = Exp[6] = (exp(-z)-zExp[5])/5
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Fx=((((x-1)*x/120+1/60)*x-1/20)*x+1/5)/exp(x)
  Fy=((((y-1)*y/120+1/60)*y-1/20)*y+1/5)/exp(y)
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}


Exp07-01 {; V.1.1 - earlier versions may be discarded
          ; Copyright (c)1998,1999 Morgan L. Owens
          ; = Exp[7] = (exp(-z)-zExp[6])/6
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Fx=(((((1-x)*x/720-1/360)*x+1/120)*x-1/30)*x+1/6)/exp(x)
  Fy=(((((1-y)*y/720-1/360)*y+1/120)*y-1/30)*y+1/6)/exp(y)
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}


Exp08-01 {; V.1.1 - earlier versions may be discarded
          ; Copyright (c)1998,1999 Morgan L. Owens
          ; = Exp[8] = (exp(-z)-zExp[7])/7
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Fx=((((((x-1)*x/5040+1/2520)*x-1/840)*x+1/210)*x-1/42)*x+1/7)/exp(x)
  Fy=((((((y-1)*y/5040+1/2520)*y-1/840)*y+1/210)*y-1/42)*y+1/7)/exp(y)
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}


Exp09-01 {; V.1.1 - earlier versions may be discarded
          ; Copyright (c)1998,1999 Morgan L. Owens
          ; = Exp[9] = (exp(-z)-zExp[8])/8
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Fx=(((((((1-x)*x/40320-1/20160)*x+1/6720)*x-1/1680)*x+1/336)*x-1/56)*x+1/8)/exp(x)
  Fy=(((((((1-y)*y/40320-1/20160)*y+1/6720)*y-1/1680)*y+1/336)*y-1/56)*y+1/8)/exp(y)
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}


Exp10-01 {; V.1.1 - earlier versions may be discarded
          ; Copyright (c)1998,1999 Morgan L. Owens
          ; = Exp[10] = (exp(-z)-zExp[9])/9
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Fx=((((((((x-1)*x/362880+1/181440)*x-1/60480)*x+1/15120)*x-1/3024)*x+1/504)*x-1/72)*x+1/9)/exp(x)
  Fy=((((((((y-1)*y/362880+1/181440)*y-1/60480)*y+1/15120)*y-1/3024)*y+1/504)*y-1/72)*y+1/9)/exp(y)
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}



Alpha02-01 {; V.1.1 - earlier versions may be discarded
            ; Copyright (c)1998,1999 Morgan L. Owens
            ; Chebyshev Types:
            ; Inspired by Clifford A. Pickover:
            ;
            ; Dynamic (Euler method)
            ; Alpha Integral
            ; Alpha[0] = exp(-z)/z
            ; Alpha[1] = exp(-z)(1-1/z)/z
            ; Alpha[n+1] = (exp(-z)-(n+1)Alpha[n])/z
            ;
            ; = Alpha[2] = (exp(-z)-2Alpha[1])/z
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  Fx=((x-2)*x+2)/(exp(x)*x*x*x)
  Fy=((y-2)*y+2)/(exp(y)*y*y*y)
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}


Alpha03-01 {; V.1.1 - earlier versions may be discarded
            ; Copyright (c)1998,1999 Morgan L. Owens
            ; = Alpha[3] = (exp(-z)-3Alpha[2])/z
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  x2=x*x, y2=y*y
  Fx=(((x-3)*x+6)*x-6)/(exp(x)*x2*x2)
  Fy=(((y-3)*y+6)*y-6)/(exp(y)*y2*y2)
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}


Alpha04-01 {; V.1.1 - earlier versions may be discarded
            ; Copyright (c)1998,1999 Morgan L. Owens
            ; = Alpha[4] = (exp(-z)-4Alpha[3])/z
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  x2=x*x, y2=y*y
  Fx=((((x-4)*x+12)*x-24)*x+24)/(exp(x)*x2*x2*x)
  Fy=((((y-4)*y+12)*y-24)*y+24)/(exp(y)*y2*y2*y)
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}


Alpha05-01 {; V.1.1 - earlier versions may be discarded
            ; Copyright (c)1998,1999 Morgan L. Owens
            ; = Alpha[5] = (exp(-z)-5Alpha[4])/z
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  x2=x*x, y2=y*y
  Fx=(((((x-5)*x+20)*x-60)*x+120)*x-120)/(exp(x)*x2*x2*x2)
  Fy=(((((y-5)*y+20)*y-60)*y+120)*y-120)/(exp(y)*y2*y2*y2)
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}


Alpha06-01 {; V.1.1 - earlier versions may be discarded
            ; Copyright (c)1998,1999 Morgan L. Owens
            ; = Alpha[6] = (exp(-z)-6Alpha[5])/z
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  x2=x*x, y2=y*y
  Fx=((((((x-6)*x+30)*x-120)*x+360)*x-720)*x+720)/(exp(x)*x2*x2*x2*x)
  Fy=((((((y-6)*y+30)*y-120)*y+360)*y-720)*y+720)/(exp(y)*y2*y2*y2*y)
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}


Alpha07-01 {; V.1.1 - earlier versions may be discarded
            ; Copyright (c)1998,1999 Morgan L. Owens
            ; = Alpha[7] = (exp(-z)-7Alpha[6])/z
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  x2=x*x, y2=y*y, x4=x2*x2, y4=y2*y2
  Fx=(((((((x-7)*x+42)*x-210)*x+840)*x-2520)*x+5040)*x-5040)/(exp(x)*x4*x4)
  Fy=(((((((y-7)*y+42)*y-210)*y+840)*y-2520)*y+5040)*y-5040)/(exp(y)*y4*y4)
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}


Alpha08-01 {; V.1.1 - earlier versions may be discarded
            ; Copyright (c)1998,1999 Morgan L. Owens
            ; = Alpha[8] = (exp(-z)-8Alpha[7])/z
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  x2=x*x, y2=y*y, x4=x2*x2, y4=y2*y2
  Fx=((((((((x-8)*x+56)*x-336)*x+1680)*x-6720)*x+20160)*x-40320)*x+40320)/(exp(x)*x4*x4*x)
  Fy=((((((((y-8)*y+56)*y-336)*y+1680)*y-6720)*y+20160)*y-40320)*y+40320)/(exp(y)*y4*y4*y)
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}


Alpha09-01 {; V.1.1 - earlier versions may be discarded
            ; Copyright (c)1998,1999 Morgan L. Owens
            ; = Alpha[9] = (exp(-z)-9Alpha[8])/z
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  x2=x*x, y2=y*y, x4=x2*x2, y4=y2*y2
  Fx=(((((((((x-9)*x+72)*x-504)*x+3024)*x-15120)*x+60480)*x-181440)*x+362880)*x-362880)/(exp(x)*x4*x4*x2)
  Fy=(((((((((y-9)*y+72)*y-504)*y+3024)*y-15120)*y+60480)*y-181440)*y+362880)*y-362880)/(exp(y)*y4*y4*y2)
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}


Alpha10-01 {; V.1.1 - earlier versions may be discarded
            ; Copyright (c)1998,1999 Morgan L. Owens
            ; = Alpha[10] = (exp(-z)-10Alpha[9])/z
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  x2=x*x, y2=y*y, x4=x2*x2, y4=y2*y2
  Fx=((((((((((x-10)*x+90)*x-720)*x+5040)*x-30240)*x+151200)*x-604800)*x+1814400)*x-3628800)*x+3628800)/(exp(x)*x4*x4*x2*x)
  Fy=((((((((((y-10)*y+90)*y-720)*y+5040)*y-30240)*y+151200)*y-604800)*y+1814400)*y-3628800)*y+3628800)/(exp(y)*y4*y4*y2*y)
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}



Beta02-01 {; V.1.1 - earlier versions may be discarded
           ; Copyright (c)1998,1999 Morgan L. Owens
           ; Chebyshev Types:
           ; Inspired by Clifford A. Pickover
           ;
           ; Dynamic (Euler method)
           ; Beta Integral
           ; Beta[0] = 2sinh(z)/z = (exp(z)-exp(-z))/z
           ; Beta[n+1] = (exp(-z)(-1)^(n+1)-(n+1)Beta[n])/z
           ;
           ; = Beta[2] = (exp(-z)-2Beta[1])/z
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  ex=exp(x), ey=exp(y)
  Fx=((x+2)*x+(2*ex*ex-2))/(x*x*x*ex)
  Fy=((y+2)*y+(2*ey*ey-2))/(y*y*y*ey)
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}


Beta03-01 {; V.1.1 - earlier versions may be discarded
           ; Copyright (c)1998,1999 Morgan L. Owens
           ; = Beta[3] = (-exp(-z)-3Beta[2])/z
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  ex=exp(x), ey=exp(y)
  x2=x*x, y2=y*y
  Fx=-(((x+3)*x+6)*x+(6*ex*ex-6))/(x2*y2*ex)
  Fy=-(((y+3)*y+6)*y+(6*ey*ey-6))/(y2*y2*ey)
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}


Beta04-01 {; V.1.1 - earlier versions may be discarded
           ; Copyright (c)1998,1999 Morgan L. Owens
           ; = Beta[4] = (exp(-z)-4Beta[3])/z
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  ex=exp(x), ey=exp(y)
  x2=x*x, y2=y*y
  Fx=((((x+4)*x+12)*x+24)*x+(24*ex*ex-24))/(x2*x2*x*ex)
  Fy=((((y+4)*y+12)*y+24)*y+(24*ey*ey-24))/(y2*y2*y*ey)
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}


Beta05-01 {; V.1.1 - earlier versions may be discarded
           ; Copyright (c)1998,1999 Morgan L. Owens
           ; = Beta[5] = (-exp(-z)-5Beta[4])/z
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  ex=exp(x), ey=exp(y)
  x2=x*x, y2=y*y
  Fx=-(((((x+5)*x+20)*x+60)*x+120)*x+(120*ex*ex-120))/(x2*x2*x2*ex)
  Fy=-(((((y+5)*y+20)*y+60)*y+120)*y+(120*ey*ey-120))/(y2*y2*y2*ey)
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}


Beta06-01 {; V.1.1 - earlier versions may be discarded
           ; Copyright (c)1998,1999 Morgan L. Owens
           ; = Beta[6] = (exp(-z)-6Beta[5])/z
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  ex=exp(x), ey=exp(y)
  x2=x*x, y2=y*y
  Fx=((((((x+6)*x+30)*x+120)*x+360)*x+720)*x+(720*ex*ex-720))/(x2*x2*x2*x*ex)
  Fy=((((((y+6)*y+30)*y+120)*y+360)*y+720)*y+(720*ey*ey-720))/(y2*y2*y2*y*ey)
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}


Beta07-01 {; V.1.1 - earlier versions may be discarded
           ; Copyright (c)1998,1999 Morgan L. Owens
           ; = Beta[7] = (-exp(-z)-7Beta[6])/z
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  ex=exp(x), ey=exp(y)
  x2=x*x, y2=y*y, x4=x2*x2, y4=y2*y2
  Fx=-(((((((x+7)*x+42)*x+210)*x+840)*x+2520)*x+5040)*x+(5040*ex*ex-5040))/(x4*x4*ex)
  Fy=-(((((((y+7)*y+42)*y+210)*y+840)*y+2520)*y+5040)*y+(5040*ey*ey-5040))/(y4*y4*ey)
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}


Beta08-01 {; V.1.1 - earlier versions may be discarded
           ; Copyright (c)1998,1999 Morgan L. Owens
           ; = Beta[8] = (exp(-z)-8Beta[7])/z
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  ex=exp(x), ey=exp(y)
  x2=x*x, y2=y*y, x4=x2*x2, y4=y2*y2
  Fx=((((((((x+8)*x+56)*x+336)*x+1680)*x+6720)*x+20160)*x+40320)*x+(40320*ex*ex-40320))/(x4*x4*x*ex)
  Fy=((((((((y+8)*y+56)*y+336)*y+1680)*y+6720)*y+20160)*y+40320)*y+(40320*ey*ey-40320))/(y4*y4*y*ey)
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}


Beta09-01 {; V.1.1 - earlier versions may be discarded
           ; Copyright (c)1998,1999 Morgan L. Owens
           ; = Beta[9] = (-exp(-z)-9Beta[8])/z
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  ex=exp(x), ey=exp(y)
  x2=x*x, y2=y*y, x4=x2*x2, y4=y2*y2
  Fx=-(((((((((x+9)*x+72)*x+504)*x+3024)*x+15120)*x+60480)*x+181440)*x+362880)*x+(362880*ex*ex-362880))/(x4*x4*x2*ex)
  Fy=-(((((((((y+9)*y+72)*y+504)*y+3024)*y+15120)*y+60480)*y+181440)*y+362880)*y+(362880*ey*ey-362880))/(y4*y4*y2*ey)
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}


Beta10-01 {; V.1.1 - earlier versions may be discarded
           ; Copyright (c)1998,1999 Morgan L. Owens
           ; = Beta[10] = (exp(-z)-10Beta[9])/z
  t=#zwpixel, bailout=4, z=pixel:
  x=real(z), y=imag(z)
  ex=exp(x), ey=exp(y)
  x2=x*x, y2=y*y, x4=x2*x2, y4=y2*y2
  Fx=((((((((((x+10)*x+90)*x+720)*x+5040)*x+30240)*x+151200)*x+604800)*x+1814400)*x+3628800)*x+(3628800*ex*ex-3628800))/(x4*x4*x2*x*ex)
  Fy=((((((((((y+10)*y+90)*y+720)*y+5040)*y+30240)*y+151200)*y+604800)*y+1814400)*y+3628800)*y+(3628800*ey*ey-3628800))/(y4*y4*y2*y*ey)
  x=x-t*Fy, y=y+t*Fx
  z=x+flip(y)
  |z|<=bailout
}

