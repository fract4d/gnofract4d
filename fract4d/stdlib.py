# The fractal standard library, including operators
import math

from .codegen import ComplexArg, ConstFloatArg, ConstIntArg, TempArg, HyperArg, ColorArg
from .fracttypes import *

class Constants:
    def __init__(self):
        self.i = ComplexArg(ConstFloatArg(0.0),ConstFloatArg(1.0))
        self.iby2 = ComplexArg(ConstFloatArg(0.0),ConstFloatArg(0.5))
        self.minus_i = ComplexArg(ConstFloatArg(0.0),ConstFloatArg(-1.0))
        self.one = ComplexArg(ConstFloatArg(1.0),ConstFloatArg(0.0))

const = Constants()
    
def reals(l):
    # [[a + ib], [c+id]] => [ a, c]
    return [x.re for x in l]

def imags(l):
    return [x.im for x in l]

def parts(n,l):
    return [x.parts[n] for x in l]

def not_b_b(gen,t,srcs):
    return gen.emit_func('!', srcs, Int)

# unary negation
def neg_i_i(gen,t,srcs):
    return gen.emit_func('-', srcs, Int)

def neg_f_f(gen,t,srcs):
    return gen.emit_func('-', srcs, Float)

def neg_c_c(gen,t,srcs):
    return ComplexArg(
        gen.emit_func('-', [srcs[0].re], Float),
        gen.emit_func('-', [srcs[0].im], Float))

def neg_h_h(gen,t,srcs):
    src = srcs[0]
    return HyperArg(
        gen.emit_func('-', [src.parts[0]], Float),
        gen.emit_func('-', [src.parts[1]], Float),
        gen.emit_func('-', [src.parts[2]], Float),
        gen.emit_func('-', [src.parts[3]], Float))

# basic binary operation
def add_ff_f(gen,t,srcs):
    return gen.emit_binop(t.op,srcs,t.datatype)

# many equivalent funcs
sub_ff_f = mul_ff_f = div_ff_f = add_ff_f
add_ii_i = sub_ii_i = mul_ii_i = div_ii_i = add_ff_f
gt_ii_b = gte_ii_b = lt_ii_b = lte_ii_b = eq_ii_b = noteq_ii_b = add_ff_f
gt_ff_b = gte_ff_b = lt_ff_b = lte_ff_b = eq_ff_b = noteq_ff_b = add_ff_f

def mod_ii_i(gen,t,srcs):
    return gen.emit_binop('%', srcs, t.datatype)

def mod_ff_f(gen,t,srcs):
    return gen.emit_func2('fmod', srcs, Float)

def mul_cc_c(gen,t,srcs):
    # (a+ib) * (c+id) = ac - bd + i(bc + ad)
    ac = gen.emit_binop('*', [srcs[0].re, srcs[1].re], Float)
    bd = gen.emit_binop('*', [srcs[0].im, srcs[1].im], Float)
    bc = gen.emit_binop('*', [srcs[0].im, srcs[1].re], Float)
    ad = gen.emit_binop('*', [srcs[0].re, srcs[1].im], Float)
    dst = ComplexArg(
        gen.emit_binop('-', [ac, bd], Float),
        gen.emit_binop('+', [bc, ad], Float))
    return dst

def mul_hh_h(gen,t,srcs):
    def mulpair(x,y):
        return gen.emit_binop('*', [srcs[0].parts[x], srcs[1].parts[y]], Float)

    re2 =  mulpair(0,0)
    i2 =   mulpair(1,1)
    j2 =   mulpair(2,2)
    k2 =   mulpair(3,3)

    re = gen.emit_binop('-', [ re2, i2], Float)
    re = gen.emit_binop('-', [ re, j2], Float)
    re = gen.emit_binop('+', [ re, k2], Float)
    
    i_re = mulpair(1,0)
    re_i = mulpair(0,1)
    k_j =  mulpair(3,2)
    j_k =  mulpair(2,3)

    i = gen.emit_binop('+', [ i_re, re_i], Float)
    i = gen.emit_binop('-', [ i, k_j], Float)
    i = gen.emit_binop('-', [ i, j_k], Float)
        
    j_re = mulpair(2,0)
    k_i =  mulpair(3,1)
    re_j = mulpair(0,2)
    i_k =  mulpair(1,3)

    j = gen.emit_binop('-', [ j_re, k_i], Float)
    j = gen.emit_binop('+', [ j, re_j], Float)
    j = gen.emit_binop('-', [ j, i_k], Float)
    
    k_re = mulpair(3,0)
    j_i =  mulpair(2,1)
    i_j =  mulpair(1,2)
    re_k = mulpair(0,3)

    k = gen.emit_binop('+', [ k_re, j_i], Float)
    k = gen.emit_binop('+', [ k, i_j], Float)
    k = gen.emit_binop('+', [ k, re_k], Float)

    return HyperArg(re,i,j,k)

def complex_ff_c(gen,t,srcs):
    # construct a complex number from two real parts
    return ComplexArg(srcs[0],srcs[1])

def hyper_ffff_h(gen,t,srcs):
    return HyperArg(srcs[0],srcs[1],srcs[2],srcs[3])

def hyper_cc_h(gen,t,srcs):
    return HyperArg(srcs[0].re, srcs[0].im, srcs[1].re, srcs[1].im)

def add_cc_c(gen,t,srcs):
    # add 2 complex numbers
    dst = ComplexArg(
        gen.emit_binop('+',reals(srcs), Float),
        gen.emit_binop('+',imags(srcs), Float))
    return dst

def add_hh_h(gen,t,srcs):
    # add 2 hyper numbers
    dst = HyperArg(
        gen.emit_binop('+',parts(0,srcs), Float),
        gen.emit_binop('+',parts(1,srcs), Float),
        gen.emit_binop('+',parts(2,srcs), Float),
        gen.emit_binop('+',parts(3,srcs), Float))
    return dst

def clamp_f_f(gen,t,srcs):
    # ensure f is in the range [0,1.0]
    smaller_than_one = gen.symbols.newLabel()
    done = gen.symbols.newLabel()

    one = ConstFloatArg(1.0)
    zero = ConstFloatArg(0.0)
    src = srcs[0]
    dst = TempArg(gen.symbols.newTemp(Float),Float)

    gen.emit_move(src,dst)
    
    lte1 = gen.emit_binop('<=',[src,one], Float)
    gen.emit_cjump(lte1,smaller_than_one)

    # larger than 1: use one instead
    gen.emit_move(one, dst)
    gen.emit_jump(done)
    
    gen.emit_label(smaller_than_one)
    gte0 = gen.emit_binop('>=', [src, zero], Float)
    gen.emit_cjump(gte0, done)
    
    # smaller than 0: use 0 instead
    gen.emit_move(zero, dst)
    
    gen.emit_label(done)

    return dst

def clamp_C_C(gen,t,srcs):
    # ensure color C is in the range [0.0,1.0]
    dst = ColorArg(
        clamp_f_f(gen,t,parts(0,srcs)),
        clamp_f_f(gen,t,parts(1,srcs)),
        clamp_f_f(gen,t,parts(2,srcs)),
        clamp_f_f(gen,t,parts(3,srcs)))
    return dst

def add_CC_C(gen,t,srcs):
    # add 2 colors, piecewise
    dst = ColorArg(
        gen.emit_binop('+',parts(0,srcs), Float),
        gen.emit_binop('+',parts(1,srcs), Float),
        gen.emit_binop('+',parts(2,srcs), Float),
        gen.emit_binop('+',parts(3,srcs), Float))
    return dst
    
def sub_cc_c(gen,t,srcs):
    # subtract 2 complex numbers
    dst = ComplexArg(
        gen.emit_binop('-',reals(srcs), Float),
        gen.emit_binop('-',imags(srcs), Float))
    return dst

def sub_hh_h(gen,t,srcs):
    # subtract 2 hypercomplex numbers
    dst = HyperArg(
        gen.emit_binop('-',parts(0,srcs), Float),
        gen.emit_binop('-',parts(1,srcs), Float),
        gen.emit_binop('-',parts(2,srcs), Float),
        gen.emit_binop('-',parts(3,srcs), Float))
    return dst

def sub_CC_C(gen,t,srcs):
    dst = ColorArg(
        gen.emit_binop('-',parts(0,srcs), Float),
        gen.emit_binop('-',parts(1,srcs), Float),
        gen.emit_binop('-',parts(2,srcs), Float),
        gen.emit_binop('-',parts(3,srcs), Float))
    return dst
    
def div_cc_c(gen,t,srcs):
    # (a+ib)/(c+id) = (a+ib)*(c-id) / (c+id)*(c-id)
    # = (ac + bd + i(bc - ad))/mag(c+id)
    denom = cmag_c_f(gen,'mag', [srcs[1]])
    ac = gen.emit_binop('*', [srcs[0].re, srcs[1].re], Float)
    bd = gen.emit_binop('*', [srcs[0].im, srcs[1].im], Float)
    bc = gen.emit_binop('*', [srcs[0].im, srcs[1].re], Float)
    ad = gen.emit_binop('*', [srcs[0].re, srcs[1].im], Float)
    dre = gen.emit_binop('+', [ac, bd], Float)
    dim = gen.emit_binop('-', [bc, ad], Float)
    return ComplexArg(
        gen.emit_binop('/', [dre, denom], Float),
        gen.emit_binop('/', [dim, denom], Float))

def div_cf_c(gen,t,srcs):
    # divide a complex number by a real one
    return ComplexArg(
        gen.emit_binop('/',[srcs[0].re, srcs[1]], Float),
        gen.emit_binop('/',[srcs[0].im, srcs[1]], Float))

def mul_cf_c(gen,t,srcs):
    # multiply a complex number by a real one
    return ComplexArg(
        gen.emit_binop('*',[srcs[0].re, srcs[1]], Float),
        gen.emit_binop('*',[srcs[0].im, srcs[1]], Float))

def mul_hf_h(gen,t,srcs):
    # multiply a hypercomplex number by a real one
    return HyperArg(
        gen.emit_binop('*',[srcs[0].parts[0], srcs[1]], Float),
        gen.emit_binop('*',[srcs[0].parts[1], srcs[1]], Float),
        gen.emit_binop('*',[srcs[0].parts[2], srcs[1]], Float),
        gen.emit_binop('*',[srcs[0].parts[3], srcs[1]], Float)
        )

def mul_Cf_C(gen,t,srcs):
    return mul_hf_h(gen,t,srcs)

def div_hf_h(gen,t,srcs):
    # multiply a hypercomplex number by a real one
    return HyperArg(
        gen.emit_binop('/',[srcs[0].parts[0], srcs[1]], Float),
        gen.emit_binop('/',[srcs[0].parts[1], srcs[1]], Float),
        gen.emit_binop('/',[srcs[0].parts[2], srcs[1]], Float),
        gen.emit_binop('/',[srcs[0].parts[3], srcs[1]], Float)
        )

def div_Cf_C(gen,t,srcs):
    return div_hf_h(gen,t,srcs)

def cmag_c_f(gen,t,srcs):
    # |x| = x_re * x_re + x_im * x_im
    src = srcs[0]
    re_2 = gen.emit_binop('*',[src.re,src.re],Float)
    im_2 = gen.emit_binop('*',[src.im,src.im],Float)
    return gen.emit_binop('+',[re_2,im_2],Float)

def cmag_h_f(gen,t,srcs):
    # |x| = x_re * x_re + x_i * x_i + x_j * x_j + x_k * x_k
    src = srcs[0]
    re_2 = gen.emit_binop('*',[src.parts[0],src.parts[0]],Float)
    i_2 = gen.emit_binop('*',[src.parts[1],src.parts[1]],Float)
    j_2 = gen.emit_binop('*',[src.parts[2],src.parts[2]],Float)
    k_2 = gen.emit_binop('*',[src.parts[3],src.parts[3]],Float)
    ret = gen.emit_binop('+',[re_2,i_2],Float)
    ret = gen.emit_binop('+',[ret,j_2], Float)
    ret = gen.emit_binop('+',[ret,k_2], Float)
    return ret
    
def log_f_f(gen,t,srcs):
    return gen.emit_func('log', srcs, Float)

def log_c_c(gen,t,srcs):
    # log(a+ib) = (log(mag(a+ib)), atan2(a+ib))
    re = gen.emit_func('log', [cabs_c_f(gen,t,srcs)], Float)
    im = atan2_c_f(gen,t,srcs)
    return ComplexArg(re,im)

def polar_ff_c(gen,t,srcs):
    # polar(r,theta) = (r * cos(theta), r * sin(theta))
    re = gen.emit_binop('*',[srcs[0],cos_f_f(gen,t,[srcs[1]])], Float)
    im = gen.emit_binop('*',[srcs[0],sin_f_f(gen,t,[srcs[1]])], Float)
    return ComplexArg(re,im)

def exp_f_f(gen,t,srcs):
    return gen.emit_func('exp', srcs, Float)

def exp_c_c(gen,t,srcs):
    #exp(a+ib) = polar(exp(a),b)
    expx = gen.emit_func('exp', [srcs[0].re], Float)
    return polar_ff_c(gen,t,[expx, srcs[0].im])

def pow_ff_f(gen,t,srcs):
    return gen.emit_func2('pow', srcs, Float)

def pow_ff_c(gen,t,srcs):
    arg = ComplexArg(srcs[0], ConstFloatArg(0.0))
    return pow_cf_c(gen,t,[arg,srcs[1]])

def pow_cf_c(gen,t,srcs):
    nonzero = gen.symbols.newLabel()
    done = gen.symbols.newLabel()
    dst_re = gen.newTemp(Float)
    dst_im = gen.newTemp(Float)

    # FIXME: this shortcut breaks 3damand01, not sure why
    #gen.emit_cjump(srcs[0].im,nonzero)

    # compute result if just real
    #tdest = pow_ff_f(gen,t,[srcs[0].re,srcs[1]])
    #gen.emit_move(tdest,dst_re)
    #gen.emit_move(ConstFloatArg(0.0),dst_im)
    #gen.emit_jump(done)

    #gen.emit_label(nonzero)\
    
    # result if real + imag
    # temp = log(a+ib)
    # polar(y * real(temp), y * imag(temp))

    temp = log_c_c(gen,t,[srcs[0]])
    t_re = gen.emit_binop('*',[temp.re, srcs[1]], Float)
    t_re = gen.emit_func('exp',[t_re], Float)
    t_im = gen.emit_binop('*',[temp.im, srcs[1]], Float)
    temp2 = polar_ff_c(gen,t,[t_re, t_im])
    gen.emit_move(temp2.re,dst_re)
    gen.emit_move(temp2.im,dst_im)
    gen.emit_label(done)

    return ComplexArg(dst_re,dst_im)

def pow_cc_c(gen,t,srcs):
    nonzero = gen.symbols.newLabel()
    done = gen.symbols.newLabel()
    dst_re = gen.newTemp(Float)
    dst_im = gen.newTemp(Float)

    gen.emit_cjump(srcs[0].re,nonzero)
    gen.emit_cjump(srcs[0].im,nonzero)
    
    # 0^foo = 0
    gen.emit_move(ConstFloatArg(0.0),dst_re)
    gen.emit_move(ConstFloatArg(0.0),dst_im)
    gen.emit_jump(done)

    gen.emit_label(nonzero)
    # exp(y*log(x))

    logx = log_c_c(gen,t,[srcs[0]])
    ylogx = mul_cc_c(gen,t,[srcs[1],logx])
    xtoy = exp_c_c(gen,t,[ylogx])
    
    gen.emit_move(xtoy.re,dst_re)
    gen.emit_move(xtoy.im,dst_im)
    gen.emit_label(done)

    return ComplexArg(dst_re,dst_im)
    
def lt_cc_b(gen,t,srcs):
    # compare real parts only
    return gen.emit_binop(t.op,reals(srcs), Bool)

# these comparisons implemented the same way
lte_cc_b = gt_cc_b = gte_cc_b = lt_cc_b

def eq_cc_b(gen,t,srcs):
    # compare 2 complex numbers for equality
    d1 = gen.emit_binop(t.op,reals(srcs), Bool)
    d2 = gen.emit_binop(t.op,imags(srcs), Bool)
    dst = gen.emit_binop("&&", [d1, d2], Bool)
    return dst

def noteq_cc_b(gen,t,srcs):
    # compare 2 complex numbers for inequality
    d1 = gen.emit_binop(t.op,reals(srcs), Bool)
    d2 = gen.emit_binop(t.op,imags(srcs), Bool)
    dst = gen.emit_binop("||", [d1, d2], Bool)
    return dst

# sqr = square(x) = x*x

def sqr_c_c(gen,t,srcs):
    # sqr(a+ib) = a2 - b2 + i(2ab)
    src = srcs[0]
    a2 = gen.emit_binop('*', [src.re, src.re], Float)
    b2 = gen.emit_binop('*', [src.im, src.im], Float)
    ab = gen.emit_binop('*', [src.re, src.im], Float)
    dst = ComplexArg(
        gen.emit_binop('-', [a2, b2], Float),
        gen.emit_binop('*', [ConstFloatArg(2.0), ab], Float))
    return dst
    
def sqr_f_f(gen,t,srcs):
    return gen.emit_binop('*',[srcs[0], srcs[0]], Float)

sqr_i_i = sqr_f_f

def conj_c_c(gen,t,srcs):
    # conj (a+ib) = a-ib
    b = gen.emit_binop('-', [ConstFloatArg(0.0), srcs[0].im], Float)
    return ComplexArg(srcs[0].re,b)

def flip_c_c(gen,t,srcs):
    # flip(a+ib) = b+ia
    return ComplexArg(srcs[0].im,srcs[0].re)

def imag_c_f(gen,t,srcs):
    return srcs[0].im

def imag2_c_f(gen,t,srcs):
    return gen.emit_binop('*', [srcs[0].im, srcs[0].im], Float)

def real_c_f(gen,t,srcs):
    return srcs[0].re

def real2_c_f(gen,t,srcs):
    return gen.emit_binop('*', [srcs[0].re, srcs[0].re], Float)

def real_h_f(gen,t,srcs):
    return srcs[0].parts[0]

def imag_h_f(gen,t,srcs):
    return srcs[0].parts[1]

def hyper_j_h_f(gen,t,srcs):
    return srcs[0].parts[2]

def hyper_k_h_f(gen,t,srcs):
    return srcs[0].parts[3]

red_C_f = real_h_f
green_C_f = imag_h_f
blue_C_f = hyper_j_h_f
alpha_C_f = hyper_k_h_f

def hyper_ri_h_c(gen,t,srcs):
    return ComplexArg(srcs[0].parts[0], srcs[0].parts[1])

def hyper_jk_h_c(gen,t,srcs):
    return ComplexArg(srcs[0].parts[2], srcs[0].parts[3])

def ident_i_i(gen,t,srcs):
    return srcs[0]

ident_f_f = ident_c_c = ident_h_h = ident_b_b = ident_i_i

bool_b_b = ident_b_b
int_i_i = ident_i_i
float_f_f = ident_f_f

def recip_f_f(gen,t,srcs):
    # reciprocal
    return gen.emit_binop('/', [ConstFloatArg(1.0), srcs[0]], Float)

def recip_c_c(gen,t,srcs):
    return div_cc_c(gen, None,
                    [ComplexArg(ConstFloatArg(1.0), ConstFloatArg(0.0)), srcs[0]])

def recip_h_h(gen,t,srcs):
    src = srcs[0]
    re = src.parts[0]
    i = src.parts[1]
    j = src.parts[2]
    k = src.parts[3]
    
    # det = ((re-k)^2 + (i+j)^2)*((re+k)^2 + (i-j)^2)
    re_m_k = gen.emit_binop('-', [re, k], Float)
    re_p_k = gen.emit_binop('+', [re, k], Float)
    i_m_j =  gen.emit_binop('-', [i, j], Float)
    i_p_j =  gen.emit_binop('+', [i, j], Float)
    
    det = gen.emit_binop('*',[
        gen.emit_binop('+',[
           gen.emit_binop('*', [re_m_k, re_m_k], Float),
           gen.emit_binop('*', [i_p_j, i_p_j], Float),
           ], Float),
        gen.emit_binop('+',[
           gen.emit_binop('*', [re_p_k, re_p_k], Float),
           gen.emit_binop('*', [i_m_j, i_m_j], Float),
           ], Float),
        ], Float)

    # could check if det == 0 but just allow division by zero instead

    # |h|
    mod = cmag_h_f(gen,t,srcs)

    # 2 * re*k - i*j
    re_k_minus_ij = gen.emit_binop('-', [
        gen.emit_binop('*', [re, k], Float),
        gen.emit_binop('*', [i, j], Float)], Float)
    re_k_minus_ij = gen.emit_binop('+', [re_k_minus_ij, re_k_minus_ij], Float)

    return HyperArg(
        gen.emit_binop('/', [
           gen.emit_binop('-', [
              gen.emit_binop('*', [re,mod], Float),
              gen.emit_binop('*', [k, re_k_minus_ij], Float)], Float),
           det], Float),
        gen.emit_binop('/', [
           gen.emit_binop('-', [
              neg_f_f(gen,t, [gen.emit_binop('*', [i,mod], Float)]),
              gen.emit_binop('*', [j, re_k_minus_ij], Float)], Float),
           det], Float),
        gen.emit_binop('/', [
           gen.emit_binop('-', [
              neg_f_f(gen,t, [gen.emit_binop('*', [j,mod], Float)]),
              gen.emit_binop('*', [i, re_k_minus_ij], Float)], Float),
           det], Float),
        gen.emit_binop('/', [
           gen.emit_binop('-', [
              gen.emit_binop('*', [k,mod], Float),
           gen.emit_binop('*', [re, re_k_minus_ij], Float)], Float),
           det], Float))

def abs_i_i(gen,t,srcs):
    return gen.emit_func('abs',srcs,Int)

def abs_f_f(gen,t,srcs):
    return gen.emit_func('fabs',srcs, Float)

def abs_c_c(gen,t,srcs):
    return ComplexArg(abs_f_f(gen,t,[srcs[0].re]), abs_f_f(gen,t,[srcs[0].im]))

def cabs_c_f(gen,t,srcs):
    # FIXME: per std_complex.h,should divide numbers first to avoid overflow
    return sqrt_f_f(gen,t,[cmag_c_f(gen,t,srcs)])

def sqrt_f_f(gen,t,srcs):
    return gen.emit_func('sqrt', srcs, Float)

def min2_c_f(gen,t,srcs):
    r2 = real2_c_f(gen,t,srcs)
    i2 = imag2_c_f(gen,t,srcs)
    real_larger = gen.symbols.newLabel()
    done = gen.symbols.newLabel()
    dst = gen.newTemp(Float)

    rgt = gen.emit_binop('>=',[r2,i2], Float)
    gen.emit_cjump(rgt,real_larger)

    # imag larger
    gen.emit_move(r2,dst)
    gen.emit_jump(done)

    gen.emit_label(real_larger)
    gen.emit_move(i2,dst)
    gen.emit_label(done)

    return dst

def min_ff_f(gen,t,srcs):
    l = srcs[0]
    r = srcs[1]
    right_larger = gen.symbols.newLabel()
    done = gen.symbols.newLabel()
    dst = gen.newTemp(Float)
    right_greater = gen.emit_binop('>', [r,l], Float)
    gen.emit_cjump(right_greater, right_larger)
    # l is larger
    gen.emit_move(r,dst)
    gen.emit_jump(done)
    gen.emit_label(right_larger)
    gen.emit_move(l,dst)
    gen.emit_label(done)
    return dst

def max_ff_f(gen,t,srcs):
    l = srcs[0]
    r = srcs[1]
    right_larger = gen.symbols.newLabel()
    done = gen.symbols.newLabel()
    dst = gen.newTemp(Float)
    right_greater = gen.emit_binop('>', [r,l], Float)
    gen.emit_cjump(right_greater, right_larger)
    # l is larger
    gen.emit_move(l,dst)
    gen.emit_jump(done)
    gen.emit_label(right_larger)
    gen.emit_move(r,dst)
    gen.emit_label(done)
    return dst

def max2_c_f(gen,t,srcs):
    r2 = real2_c_f(gen,t,srcs)
    i2 = imag2_c_f(gen,t,srcs)
    real_larger = gen.symbols.newLabel()
    done = gen.symbols.newLabel()
    dst = gen.newTemp(Float)

    rgt = gen.emit_binop('>=',[r2,i2], Float)
    gen.emit_cjump(rgt,real_larger)

    # imag larger
    gen.emit_move(i2,dst)
    gen.emit_jump(done)

    gen.emit_label(real_larger)
    gen.emit_move(r2,dst)
    gen.emit_label(done)

    return dst

def sqrt_c_c(gen,t,srcs):
    xnonzero = gen.symbols.newLabel()
    done = gen.symbols.newLabel()
    dst_re = gen.newTemp(Float)
    dst_im = gen.newTemp(Float)

    gen.emit_cjump(srcs[0].re,xnonzero)
    
    # only an imaginary part :
    # temp = sqrt(abs(z.im) / 2);
    # return (temp, __y < 0 ? -__temp : __temp);
    
    temp = sqrt_f_f(gen, t, [abs_f_f(gen,t, [
        gen.emit_binop('/',[srcs[0].im, ConstFloatArg(2.0)],Float)])])

    gen.emit_move(temp,dst_re)
    # y >= 0?
    ypos = gen.emit_binop('>=',[srcs[0].im,ConstFloatArg(0.0)], Float)
    ygtzero = gen.symbols.newLabel()
    gen.emit_cjump(ypos,ygtzero)
    
    nt = neg_f_f(gen,t, [temp])
    gen.emit_move(nt,temp)
    
    gen.emit_label(ygtzero)
    gen.emit_move(temp,dst_im)
    gen.emit_jump(done)

    gen.emit_label(xnonzero)
    # both real and imaginary

    # temp = sqrt(2 * (cabs(z) + abs(z.re)));
    # u = temp/2
    temp = sqrt_f_f(
        gen,t,
        [gen.emit_binop(
            '*',
            [ConstFloatArg(2.0),
             gen.emit_binop(
                 '+',
                 [cabs_c_f(gen,t,[srcs[0]]),
                  abs_f_f(gen,t,[srcs[0].re])],
                 Float)
             ],
            Float)
          ])
    u = gen.emit_binop('/',[temp,ConstFloatArg(2.0)], Float)
    
    #x > 0?
    xpos = gen.emit_binop('>',[srcs[0].re,ConstFloatArg(0.0)], Float)
    xgtzero = gen.symbols.newLabel()
    gen.emit_cjump(xpos,xgtzero)

    # x < 0:

    # x = abs(im)/temp
    gen.emit_move(gen.emit_binop(
        '/',
        [abs_f_f(gen,t,[srcs[0].im]), temp], Float), dst_re)

    # y < 0 ? -u : u
    ypos2 = gen.emit_binop('>=',[srcs[0].im,ConstFloatArg(0.0)], Float)
    ygtzero2 = gen.symbols.newLabel()
    gen.emit_cjump(ypos2,ygtzero2)
    gen.emit_move(neg_f_f(gen,t,[u]), dst_im)
    gen.emit_jump(done)
    gen.emit_label(ygtzero2)
    gen.emit_move(u, dst_im)
    gen.emit_jump(done)

    # x > 0:
    gen.emit_label(xgtzero)

    # (u, im/temp)
    gen.emit_move(u,dst_re)
    gen.emit_move(gen.emit_binop('/',[srcs[0].im, temp], Float),dst_im)
    
    gen.emit_label(done)

    return ComplexArg(dst_re,dst_im)

def sin_f_f(gen,t,srcs):
    return gen.emit_func('sin', srcs, Float)

def sin_c_c(gen,t,srcs):
    # sin(a+ib) = (sin(a) * cosh(b), cos(a) * sinh(b))
    a = srcs[0].re ; b = srcs[0].im
    re = gen.emit_binop('*', [sin_f_f(gen,t,[a]), cosh_f_f(gen,t,[b])], Float)
    im = gen.emit_binop('*', [cos_f_f(gen,t,[a]), sinh_f_f(gen,t,[b])], Float)
    return ComplexArg(re,im)

def cos_f_f(gen,t,srcs):
    return gen.emit_func('cos', srcs, Float)

def cos_c_c(gen,t,srcs):
    # cos(a+ib) = (cos(a) * cosh(b), -(sin(a) * sinh(b)))
    a = srcs[0].re ; b = srcs[0].im
    re = gen.emit_binop('*', [cos_f_f(gen,t,[a]), cosh_f_f(gen,t,[b])], Float)
    im = gen.emit_binop('*', [sin_f_f(gen,t,[a]), sinh_f_f(gen,t,[b])], Float)
    
    nim = gen.emit_func('-',[im], Float)
    return ComplexArg(re,nim)

def cosxx_c_c(gen,t,srcs):
    #cosxx(z) = (re(cos(z)), -im(cos(z)))
    return conj_c_c(gen,t,[cos_c_c(gen,t,srcs)])

def tan_f_f(gen,t,srcs):
    return gen.emit_func('tan', srcs, Float)

def tan_c_c(gen,t,srcs):
    # tan = sin/cos
    return div_cc_c(gen,t, [sin_c_c(gen,t, [srcs[0]]), cos_c_c(gen,t,[srcs[0]])])

def cotan_c_c(gen,t,srcs):
    return div_cc_c(gen,t, [cos_c_c(gen,t, [srcs[0]]), sin_c_c(gen,t,[srcs[0]])])

def cotan_f_f(gen,t,srcs):
    return gen.emit_binop('/', [gen.emit_func('cos', srcs, Float),
                                gen.emit_func('sin', srcs, Float)], Float)

def cotanh_f_f(gen,t,srcs):
    return gen.emit_binop('/', [gen.emit_func('cosh', srcs, Float),
                                gen.emit_func('sinh', srcs, Float)], Float)

def cotanh_c_c(gen,t,srcs):
    return div_cc_c(gen,t, [cosh_c_c(gen,t, [srcs[0]]),
                            sinh_c_c(gen,t,[srcs[0]])])

def cosh_f_f(gen,t,srcs):
    return gen.emit_func('cosh', srcs, Float)

def cosh_c_c(gen,t,srcs):
    # cosh(a+ib) = cosh(a)*cos(b) + i (sinh(a) * sin(b))
    a = [srcs[0].re]; b = [srcs[0].im]
    re = gen.emit_binop('*', [cosh_f_f(gen,t,a), cos_f_f(gen,t,b)], Float)
    im = gen.emit_binop('*', [sinh_f_f(gen,t,a), sin_f_f(gen,t,b)], Float)
    return ComplexArg(re,im)

def sinh_f_f(gen,t,srcs):
    return gen.emit_func('sinh', srcs, Float)

def sinh_c_c(gen,t,srcs):
    # sinh(a+ib) = sinh(a)*cos(b) + i (cosh(a) * sin(b))
    a = [srcs[0].re]; b = [srcs[0].im]
    re = gen.emit_binop('*', [sinh_f_f(gen,t,a), cos_f_f(gen,t,b)], Float)
    im = gen.emit_binop('*', [cosh_f_f(gen,t,a), sin_f_f(gen,t,b)], Float)
    return ComplexArg(re,im)

def tanh_f_f(gen,t,srcs):
    return gen.emit_func('tanh', srcs, Float)

def tanh_c_c(gen,t,srcs):
    # tanh = sinh / cosh
    return div_cc_c(gen,t, [sinh_c_c(gen,t, [srcs[0]]), cosh_c_c(gen,t,[srcs[0]])])

def asin_f_f(gen,t,srcs):
    return gen.emit_func('asin', srcs, Float)

def asin_c_c(gen,t,srcs):
    # asin(z) = -i * log(i*z + sqrt(1-z*z))
   
    one_minus_z2 = sub_cc_c(gen,t,[const.one,sqr_c_c(gen,t,srcs)])
    sq = sqrt_c_c(gen,t,[one_minus_z2])
    arg = add_cc_c(gen,t,[mul_cc_c(gen,t,[const.i,srcs[0]]), sq])

    l = log_c_c(gen,t,[arg])
    return mul_cc_c(gen,t,[const.minus_i,l])

def acos_f_f(gen,t,srcs):
    return gen.emit_func('acos', srcs, Float)

def acos_c_c(gen,t,srcs):
    # acos(z) = pi/2 - asin(z)
    pi_by_2 = ComplexArg(ConstFloatArg(math.pi/2.0),ConstFloatArg(0.0))
    return sub_cc_c(gen,t,[pi_by_2, asin_c_c(gen,t,srcs)])

def atan_f_f(gen,t,srcs):
    return gen.emit_func('atan', srcs, Float)

def atan_c_c(gen,t,srcs):
    # atan(z) = i/2 * log(i+x/i-x)
    ratio = div_cc_c(gen,t,[add_cc_c(gen,t,[const.i,srcs[0]]),
                            sub_cc_c(gen,t,[const.i,srcs[0]])])
    return mul_cc_c(gen,t,[const.iby2,log_c_c(gen,t,[ratio])])

def trunc_f_i(gen,t,srcs):
    return gen.emit_func("(int)", srcs, Int)

def trunc_c_c(gen,t,srcs):
    return ComplexArg(trunc_f_i(gen,t,[srcs[0].re]),
                      trunc_f_i(gen,t,[srcs[0].im]))

def round_f_i(gen,t,srcs):
    return trunc_f_i(gen, t, [
        gen.emit_binop('+',[ConstFloatArg(0.5), srcs[0]], Float)])

def round_c_c(gen,t,srcs):
    return ComplexArg(round_f_i(gen,t,[srcs[0].re]),
                      round_f_i(gen,t,[srcs[0].im]))

def floor_f_i(gen,t,srcs):
    return gen.emit_func('floor', srcs, Int)

def floor_c_c(gen,t,srcs):
    return ComplexArg(floor_f_i(gen,t,[srcs[0].re]),
                      floor_f_i(gen,t,[srcs[0].im]))

def ceil_f_i(gen,t,srcs):
    return gen.emit_func('ceil', srcs, Int)

def ceil_c_c(gen,t,srcs):
    return ComplexArg(ceil_f_i(gen,t,[srcs[0].re]),
                      ceil_f_i(gen,t,[srcs[0].im]))

def zero_i_i(gen,t,srcs):
    return ConstIntArg(0)

def zero_f_f(gen,t,srcs):
    return ConstFloatArg(0.0)

def zero_c_c(gen,t,srcs):
    return ComplexArg(ConstFloatArg(0.0),ConstFloatArg(0.0))

def atan2_c_f(gen,t,srcs):
    return gen.emit_func2('atan2', [srcs[0].im, srcs[0].re], Float)

def asinh_f_f(gen,t,srcs):
    return gen.emit_func('asinh', srcs, Float)

def asinh_c_c(gen,t,srcs):
    # log(z + sqrt(z*z+1))
    sq = sqrt_c_c(gen,t,[add_cc_c(gen,t,[const.one,sqr_c_c(gen,t,srcs)])])
    return log_c_c(gen,t,[add_cc_c(gen,t,[srcs[0],sq])])

def acosh_f_f(gen,t,srcs):
    return gen.emit_func('acosh', srcs, Float)

def acosh_c_c(gen,t,srcs):
    # log(z + sqrt(z-1)*sqrt(z+1))
    sqzm1 = sqrt_c_c(gen,t,[sub_cc_c(gen,t,[srcs[0],const.one])])
    sqzp1 = sqrt_c_c(gen,t,[add_cc_c(gen,t,[srcs[0],const.one])])
    sum = add_cc_c(gen,t,[srcs[0],mul_cc_c(gen,t,[sqzm1,sqzp1])])
    return log_c_c(gen,t,[sum])
    
def atanh_f_f(gen,t,srcs):
    return gen.emit_func('atanh', srcs, Float)

def times_i(gen,t,srcs):
    # multiply by i = (-im,re)
    return ComplexArg(neg_f_f(gen,t,[srcs[0].im]),srcs[0].re)

def atanh_c_c(gen,t,srcs):
    # 1/2(log(1+z)-log(1-z))
    one_m_z = log_c_c(gen,t,[sub_cc_c(gen,t,[const.one,srcs[0]])])
    one_p_z = log_c_c(gen,t,[add_cc_c(gen,t,[const.one,srcs[0]])])
    return mul_cf_c(gen,t,[sub_cc_c(gen,t,[one_p_z, one_m_z]),
                           ConstFloatArg(0.5)])

def manhattanish_c_f(gen,t,srcs):
    return gen.emit_binop('+',[srcs[0].re,srcs[0].im],Float)

def manhattan_c_f(gen,t,srcs):
    return gen.emit_binop('+',[abs_f_f(gen,t,[srcs[0].re]),
                               abs_f_f(gen,t,[srcs[0].im])], Float)

def manhattanish2_c_f(gen,t,srcs):
    return sqr_f_f(
        gen,t,[gen.emit_binop('+',[sqr_f_f(gen,t,[srcs[0].re]),
                                   sqr_f_f(gen,t,[srcs[0].im])], Float)])

def make_hyper_func(f):
    # takes a function from C -> C and returns a function which does the same
    # thing for H -> H
    def genfunc(gen,t,srcs):
        src = srcs[0]
        ax = gen.emit_binop('-', [src.parts[0], src.parts[3]], Float)
        ay = gen.emit_binop('+', [src.parts[1], src.parts[2]], Float)
        bx = gen.emit_binop('+', [src.parts[0], src.parts[3]], Float)
        by = gen.emit_binop('-', [src.parts[1], src.parts[2]], Float)
        
        res_a = f(gen,t, [ComplexArg(ax,ay)])
        res_b = f(gen,t, [ComplexArg(bx,by)])

        outa = gen.emit_binop('+', [res_a.re, res_b.re], Float)
        outb = gen.emit_binop('+', [res_a.im, res_b.im], Float)
        outc = gen.emit_binop('-', [res_a.im, res_b.im], Float)
        outd = gen.emit_binop('-', [res_b.re, res_a.re], Float)
        # divide by 2
        return mul_hf_h(gen,t,[HyperArg(outa, outb, outc, outd),
                               ConstFloatArg(0.5)])
    return genfunc

sin_h_h = make_hyper_func(sin_c_c)
cos_h_h = make_hyper_func(cos_c_c)
cosxx_h_h = make_hyper_func(cosxx_c_c)
tan_h_h = make_hyper_func(tan_c_c)
cotan_h_h = make_hyper_func(cotan_c_c)

sinh_h_h = make_hyper_func(sinh_c_c)
cosh_h_h = make_hyper_func(cosh_c_c)
tanh_h_h = make_hyper_func(tanh_c_c)
cotanh_h_h = make_hyper_func(cotanh_c_c)

asin_h_h = make_hyper_func(asin_c_c)
acos_h_h = make_hyper_func(acos_c_c)
atan_h_h = make_hyper_func(atan_c_c)

asinh_h_h = make_hyper_func(asinh_c_c)
acosh_h_h = make_hyper_func(acosh_c_c)
atanh_h_h = make_hyper_func(atanh_c_c)

log_h_h = make_hyper_func(log_c_c)
sqrt_h_h = make_hyper_func(sqrt_c_c)
exp_h_h = make_hyper_func(exp_c_c)

flip_h_h = make_hyper_func(flip_c_c)
conj_h_h = make_hyper_func(conj_c_c)
sqr_h_h = make_hyper_func(sqr_c_c)

def rgb_fff_C(gen,t,srcs):
    return ColorArg(srcs[0], srcs[1], srcs[2], ConstFloatArg(1.0))

def hsl_fff_C(gen,t,srcs):
    [d1,d2,d3] = gen.emit_func3_3("hsl_to_rgb", srcs, Float)
    return ColorArg(d1,d2,d3,ConstFloatArg(1.0))

def hsla_ffff_C(gen,t,srcs):
    [d1,d2,d3] = gen.emit_func3_3("hsl_to_rgb", srcs, Float)
    return ColorArg(d1,d2,d3,srcs[3])

def hsv_fff_C(gen,t,srcs):
    [d1,d2,d3] = gen.emit_func3_3("hsv_to_rgb", srcs, Float)
    return ColorArg(d1,d2,d3,ConstFloatArg(1.0))

def hue_C_f(gen,t,srcs):
    c = srcs[0]
    return gen.emit_func3("hue",[c.parts[0], c.parts[1], c.parts[2]], Float)

def sat_C_f(gen,t,srcs):
    c = srcs[0]
    return gen.emit_func3("sat", [c.parts[0], c.parts[1], c.parts[2]], Float)

def lum_C_f(gen,t,srcs):
    c = srcs[0]
    return gen.emit_func3("lum",[c.parts[0], c.parts[1], c.parts[2]], Float)

def rgba_ffff_C(gen,t,srcs):
    return ColorArg(srcs[0], srcs[1], srcs[2], srcs[3])

color_ffff_C = rgba_ffff_C

def blend_CCf_C(gen,t,srcs):
    (a, b, factor) = srcs
    one_m_factor = gen.emit_binop('-',[ConstFloatArg(1.0), factor], Float)
    return add_CC_C(
        gen,t,
        [ mul_Cf_C(gen,t,[a,one_m_factor]),
          mul_Cf_C(gen,t,[b,factor])])
        
def compose_CCf_C(gen,t,srcs):
    (a, b, factor) = srcs

    # factor *alpha(b)
    factor = gen.emit_binop('*', [b.parts[3], factor], Float)
    blend = blend_CCf_C(gen,t,[a,b,factor])
    gen.emit_move(a.parts[3],blend.parts[3])
    return blend

def mergenormal_CC_C(gen,t,srcs):
    return srcs[1]

def mergemultiply_CC_C(gen,t,srcs):
    (a,b) = (srcs[0],srcs[1])
    return ColorArg(
        gen.emit_binop('*', [ a.parts[0], b.parts[0]], Float),
        gen.emit_binop('*', [ a.parts[1], b.parts[1]], Float),
        gen.emit_binop('*', [ a.parts[2], b.parts[2]], Float),
        b.parts[3])

def gradient_Gf_C(gen,t,srcs):
    [d1,d2,d3] = gen.emit_func2_3("gradient", srcs, Float)
    # fixme get alpha from gradient
    return ColorArg(d1,d2,d3,ConstFloatArg(1.0))

def _image_Ic_C(gen,t,srcs):
    c = srcs[1]
    [d1,d2,d3] = gen.emit_func3_3("image_lookup", [srcs[0], c.re, c.im], Float)
    return ColorArg(d1,d2,d3,ConstFloatArg(1.0))
    
def gradient_f_C(gen,t,srcs):
    grad = gen.get_gradient_var()
    return gradient_Gf_C(gen,t,[grad,srcs[0]])

def rand__c(gen,t,srcs):
    [d1,d2] = gen.emit_func0_2("fract_rand", srcs, Float)
    return ComplexArg(d1,d2)

def _alloc_avii_av(gen,t,srcs):
    d = gen.emit_func3("alloc_array1D", srcs, VoidArray)
    return d

def _alloc_aviii_av(gen,t,srcs):
    d = gen.emit_func_n(4,"alloc_array2D", srcs, VoidArray)
    return d

def _alloc_aviiii_av(gen,t,srcs):
    d = gen.emit_func_n(5, "alloc_array3D", srcs, VoidArray)
    return d

def _alloc_aviiiii_av(gen,t,srcs):
    d = gen.emit_func_n(6, "alloc_array4D", srcs, VoidArray)
    return d

def _read_lookup_aii_i(gen,t,srcs):
    d = gen.emit_func2("read_int_array_1D", srcs, Int)
    return d

def _read_lookup_afi_f(gen,t,srcs):
    d = gen.emit_func2("read_float_array_1D", srcs, Float)
    return d

def _read_lookup_aci_c(gen,t,srcs):
    # lookup pair of floats
    i1 = gen.emit_binop('*', [ConstIntArg(2), srcs[1]], Int)
    i2 = gen.emit_binop('+', [ConstIntArg(1), i1], Int)
    d1 = gen.emit_func2("read_float_array_1D", [srcs[0], i1], Float)
    d2 = gen.emit_func2("read_float_array_1D", [srcs[0], i2], Float)
    
    return ComplexArg(d1,d2)

def _read_lookup_aiii_i(gen,t,srcs):
    d = gen.emit_func3("read_int_array_2D", srcs, Int)
    return d

def _read_lookup_afii_f(gen,t,srcs):
    d = gen.emit_func3("read_float_array_2D", srcs, Float)
    return d

def _read_lookup_acii_c(gen,t,srcs):

    # lookup pair of floats
    i1 = gen.emit_binop('*', [ConstIntArg(2), srcs[2]], Int)
    i2 = gen.emit_binop('+', [ConstIntArg(1), i1], Int)
    d1 = gen.emit_func3("read_float_array_2D", [srcs[0], srcs[1], i1], Float)
    d2 = gen.emit_func3("read_float_array_2D", [srcs[0], srcs[1], i2], Float)

    return ComplexArg(d1,d2)

def _read_lookup_aiiii_i(gen,t,srcs):
    pass

def _read_lookup_aiiiii_i(gen,t,srcs):
    pass

def _read_lookup_afiii_f(gen,t,srcs):
    pass

def _read_lookup_afiiii_f(gen,t,srcs):
    pass

def _read_lookup_aciii_c(gen,t,srcs):
    pass

def _read_lookup_aciiii_c(gen,t,srcs):
    pass

def _write_lookup_aiii_b(gen,t,srcs):
    d = gen.emit_func3("write_int_array_1D", srcs, Int)
    return d

def _write_lookup_afif_b(gen,t,srcs):
    d = gen.emit_func3("write_float_array_1D", srcs, Int)
    return d

def _write_lookup_acic_b(gen,t,srcs):
    # lookup pair of floats
    i1 = gen.emit_binop('*', [ConstIntArg(2), srcs[1]], Int)
    i2 = gen.emit_binop('+', [ConstIntArg(1), i1], Int)
    d1 = gen.emit_func3(
        "write_float_array_1D", [srcs[0], i1, srcs[2].re], Float)
    d2 = gen.emit_func3(
        "write_float_array_1D", [srcs[0], i2, srcs[2].im], Float)

    # CONSIDER: we ignore these anyway, but here we ignore
    # one return value 'extra thoroughly' which may need fixing
    # the proper return type would be a pair of bools
    return d1

def _write_lookup_aiiii_b(gen,t,srcs):
    d = gen.emit_func_n(4, "write_int_array_2D", srcs, Int)
    return d

def _write_lookup_afiif_b(gen,t,srcs):
    d = gen.emit_func_n(4, "write_float_array_2D", srcs, Int)
    return d

def _write_lookup_aciic_b(gen,t,srcs):
    # lookup pair of floats
    i1 = gen.emit_binop('*', [ConstIntArg(2), srcs[2]], Int)
    i2 = gen.emit_binop('+', [ConstIntArg(1), i1], Int)
    d1 = gen.emit_func_n(
        4, "write_float_array_2D", [srcs[0], srcs[1], i1, srcs[3].re], Float)
    d2 = gen.emit_func_n(
        4, "write_float_array_2D", [srcs[0], srcs[1], i2, srcs[3].im], Float)

    return d1

def _write_lookup_aiiiii_b(gen,t,srcs):
    pass
def _write_lookup_aiiiiii_b(gen,t,srcs):
    pass

def _write_lookup_afiiif_b(gen,t,srcs):
    pass
def _write_lookup_afiiiif_b(gen,t,srcs):
    pass

def _write_lookup_aciiic_b(gen,t,srcs):
    pass
def _write_lookup_aciiiic_b(gen,t,srcs):
    pass
