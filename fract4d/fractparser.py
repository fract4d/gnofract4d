#!/usr/bin/env python3
# Parser for UltraFractal + Fractint input files

import re
import types

import yacc

import fractlexer
import absyn


tokens = fractlexer.tokens

precedence = (
    ('left', 'COMMA'),
    ('right', 'ASSIGN'),
    ('left', 'BOOL_OR', 'BOOL_AND'),
    ('left', 'EQ', 'NEQ', 'LT', 'LTE', 'GT', 'GTE'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE','MOD'),
    ('right', 'BOOL_NEG', 'UMINUS', 'POWER')
)

def formatError(t,i):
     if(isinstance(t[i],str)):
          e = [absyn.Error2(t[i],t.lineno(i))]
     else:
          e = [absyn.Error(t[i].type, t[i].value, t[i].lineno)]
     return e

def p_file(t):
     'file : formlist'
     t[0] = absyn.Formlist(t[1], t.lineno(1))


def p_formlist(t):
     'formlist : formula NEWLINE formlist'
     t[0] = [ t[1] ] + t[3]

def p_formlist_singleform(t):
     'formlist : formula'
     t[0] = [ t[1] ]
     
def p_formlist_empty(t):
     '''formlist : empty
        formlist : error'''
     t[0] = []

def p_formid(t):
     'formid : FORM_ID'
     t[0] = t[1]
     
def p_formula(t):
     'formula : formid formbody'
     t[0] = absyn.Formula(t[1],t[2],t.lineno(1))

def p_formula_err(t):
     'formula : error formid formbody'
     t[0] = absyn.Formula(t[2],t[3],t.lineno(2))

def p_formbody_2(t):
     'formbody : NEWLINE stmlist sectlist FORM_END'
     t[0] = [ absyn.Stmlist("nameless",t[2],t.lineno(2)) ] + t[3] 

def p_formbody_3(t):
     'formbody : NEWLINE stmlist FORM_END'
     t[0] = [ absyn.Stmlist("nameless",t[2],t.lineno(2)) ]

def p_formbody_err(t):
     'formbody : error FORM_END'
     t[0] = formatError(t,1)
     
def p_formbody_sectlist(t):
     'formbody : NEWLINE sectlist FORM_END'
     t[0] = t[2]
     
def p_sectlist_2(t):
     'sectlist : section sectlist'
     t[0] = listify(t[1]) + t[2]

def p_sectlist_section(t):
     'sectlist : section'
     t[0] = listify(t[1])

def p_section_parm(t):
     'section : SECT_PARMS parmlist'
     t[0] = absyn.Setlist(t[1],t[2],t.lineno(1))
     
def p_section_set(t):
     'section : SECT_SET setlist'
     t[0] = absyn.Setlist(t[1],t[2],t.lineno(1))

def p_setlist_set(t):
     'setlist : set'
     t[0] = listify(t[1])

def p_setlist_2(t):
     '''setlist : set NEWLINE setlist
        setlist : set COMMA setlist'''
     t[0] = listify(t[1]) + t[3]

def p_parmlist_parm(t):
     'parmlist : parm'
     t[0] = listify(t[1])

def p_parmlist_2(t):
     'parmlist : parm NEWLINE parmlist'
     t[0] = listify(t[1]) + t[3]

def p_parmlist_3(t):
     'parmlist : parm parmlist'
     t[0] = listify(t[1]) + t[2]

def p_parm_empty(t):
     'parm : empty'
     t[0] = t[1]

# the extras are to allow params which clash with types & reserved words
def p_parm_exp(t):
     '''parm : ID ASSIGN exp
        parm : TYPE ASSIGN exp
        parm : REPEAT ASSIGN exp'''
     t[0] = absyn.Set(absyn.ID(t[1],t.lineno(1)),t[3],t.lineno(2))

def p_parm_type(t):
     'parm : ID ASSIGN TYPE'
     t[0] = absyn.SetType(absyn.ID(t[1],t.lineno(1)), t[3],t.lineno(2))

def p_set_exp(t):
     'set : ID ASSIGN exp'     
     t[0] = absyn.Set(absyn.ID(t[1],t.lineno(1)),t[3],t.lineno(2))

def p_set_type(t):
     'set : ID ASSIGN TYPE'
     t[0] = absyn.SetType(absyn.ID(t[1],t.lineno(1)), t[3],t.lineno(2))
     
def p_set_empty(t):
     'set : empty'
     t[0] = t[1]
     
def p_set_param(t):
     'set : PARAM ID setlist ENDPARAM'
     t[0] = absyn.Param(t[2],t[3],None,t.lineno(1))

def p_set_typed_param(t):
     'set : TYPE PARAM ID setlist ENDPARAM'
     t[0] = absyn.Param(t[3],t[4],t[1],t.lineno(2))

def p_set_func(t):
     'set : FUNC ID setlist ENDFUNC'
     t[0] = absyn.Func(t[2],t[3],"complex",t.lineno(1))

def p_set_typed_func(t):
     'set : TYPE FUNC ID setlist ENDFUNC'
     t[0] = absyn.Func(t[3],t[4],t[1],t.lineno(2))

def p_set_heading(t):
     'set : HEADING setlist ENDHEADING'
     t[0] = absyn.Heading(t[2],t.lineno(1))
     
def p_section_stm_2(t):
     'section : SECT_STM stmlist'
     t[0] = absyn.Stmlist(t[1],t[2],t.lineno(1))

def listify(stm):
    if stm.type == "empty":
         return []
    else:
         return [ stm ]
 
def p_stmlist_stm(t):
    'stmlist : stm'
    t[0] = listify(t[1])
    
def p_stmlist_2(t):
    '''stmlist : stm NEWLINE stmlist
       stmlist : stm COMMA stmlist'''
    t[0] = listify(t[1]) + t[3]

def p_stm_exp(t):
    'stm : exp'
    t[0] = t[1]

def p_stm_empty(t):
    'stm : empty'
    t[0] = t[1]
    
def p_empty(t):
    'empty :'
    t[0] = absyn.Empty(t.lineno(0))

def p_stm_decl_array(t):
    'stm : TYPE ID LARRAY arglist RARRAY'
    t[0] = absyn.DeclArray(t[1], t[2], t[4], t.lineno(3))

def p_stm_decl(t):
    'stm : TYPE ID'
    t[0] = absyn.Decl(t[1], t[2], t.lineno(2))

def p_stm_assign(t):
    'stm : TYPE ID ASSIGN stm'
    t[0] = absyn.Decl(t[1],t[2], t.lineno(2), t[4])
    
def p_stm_repeat(t):
    'stm : REPEAT stmlist UNTIL exp'
    t[0] = absyn.Repeat(t[2],t[4],t.lineno(1))

def p_stm_while(t):
    '''stm : WHILE exp NEWLINE stmlist ENDWHILE
       stm : WHILE exp COMMA stmlist ENDWHILE'''
    t[0] = absyn.While(t[2],t[4], t.lineno(1))
    
def p_stm_if(t):
    'stm : IF ifbody ENDIF' 
    t[0] = t[2]

def p_ifbody(t):
    '''ifbody : exp NEWLINE stmlist
       ifbody : exp COMMA stmlist'''
    t[0] = absyn.If(t[1],t[3],[absyn.Empty(t.lineno(1))], t.lineno(1))
    
def p_ifbody_else(t):
    '''ifbody : exp NEWLINE stmlist ELSE stmlist
       ifbody : exp COMMA stmlist ELSE stmlist'''
    t[0] = absyn.If(t[1], t[3], t[5], t.lineno(1))
    
def p_ifbody_elseif(t):
    '''ifbody : exp NEWLINE stmlist ELSEIF ifbody
       ifbody : exp COMMA stmlist ELSEIF ifbody'''
    t[0] = absyn.If(t[1], t[3], [t[5]], t.lineno(1))

def p_exp_binop(t):
    '''exp : exp PLUS exp
       exp : exp MINUS exp
       exp : exp TIMES exp
       exp : exp DIVIDE exp
       exp : exp MOD exp
       exp : exp POWER exp
       exp : exp BOOL_OR exp
       exp : exp BOOL_AND exp
       exp : exp EQ exp
       exp : exp NEQ exp
       exp : exp LT exp
       exp : exp LTE exp
       exp : exp GT exp
       exp : exp GTE exp
       '''
    t[0] = absyn.Binop(t[2],t[1],t[3], t.lineno(2))

def p_exp_assign(t):
    'exp : lval ASSIGN exp'
    t[0] = absyn.Assign(t[1],t[3], t.lineno(2))

def p_lval_id_array(t):
    'lval : ID LARRAY arglist RARRAY'
    t[0] = absyn.ArrayLookup(t[1],t[3],t.lineno(1))
    
def p_lval_id(t):
    'lval : ID'
    t[0] = absyn.ID(t[1],t.lineno(1))

def p_lval_funcall(t):
    'lval : ID LPAREN arglist RPAREN'
    t[0] = absyn.Funcall(t[1],t[3],t.lineno(1))
    
def p_exp_uminus(t):
    'exp : MINUS exp %prec UMINUS'
    t[0] = absyn.Negate(t[2], t.lineno(1))
    
#unary plus is a no-op
def p_exp_uplus(t):
    'exp : PLUS exp %prec UMINUS'
    t[0] = t[2]
    
def p_exp_mag(t):
    'exp : MAG exp MAG'
    t[0] = absyn.Mag(t[2],t.lineno(1))

def p_exp_neg(t):
    'exp : BOOL_NEG exp'
    t[0] = absyn.Not(t[2],t.lineno(1))

def p_exp_num(t):
    'exp : NUMBER'
    t[0] = absyn.Number(t[1],t.lineno(1))

def p_exp_boolconst(t):
    'exp : CONST'
    t[0] = absyn.Const(t[1],t.lineno(1))

def p_exp_string(t):
     'exp : STRING stringlist'
     t[0] = absyn.String(t[1],t[2],t.lineno(1))

def p_stringlist_string(t):
     'stringlist : STRING stringlist'
     t[0] = [absyn.String(t[1],None,t.lineno(1))] + t[2]

def p_stringlist_empty(t):
     'stringlist : empty'
     t[0] = []

def p_exp_lval(t):
    'exp : lval'
    t[0] = t[1]

def p_exp_complex(t):
     'exp : LPAREN exp COMMA exp RPAREN'
     t[0] = absyn.Binop("complex",t[2],t[4],t.lineno(1))

def p_exp_hyper(t):
     'exp : LPAREN exp COMMA exp COMMA exp COMMA exp RPAREN'
     t[0] = absyn.Funcall("hyper", [ t[2], t[4], t[6], t[8] ], t.lineno(1))

def p_exp_ctor(t):
     'exp : TYPE LPAREN arglist RPAREN'
     t[0] = absyn.Funcall(t[1], t[3], t.lineno(1))
     
def p_exp_complex_i(t):
    'exp : COMPLEX'
    ln = t.lineno(1)
    t[0] = absyn.Binop("complex",absyn.Number("0.0",ln),absyn.Number(t[1],ln),ln)
    
def p_exp_funcall_noargs(t):
    'exp : ID LPAREN RPAREN'
    t[0] = absyn.Funcall(t[1], None,t.lineno(1))
    
def p_exp_parexp(t):
    'exp : LPAREN exp RPAREN'
    t[0] = t[2]

def p_arglist_exp(t):
    'arglist : exp'
    t[0] = [ t[1] ]

def p_arglist_2(t):
    'arglist : arglist COMMA arglist' 
    t[0] = t[1] + t[3]

# Error rule for syntax errors outside a formula
def p_error(t):
     #print "error ",t
     pass

parser = yacc.yacc()
     
# debugging
if __name__ == '__main__': #pragma: no cover
    import sys

    
    for arg in sys.argv[1:]:
        s = open(arg,"r").read() # read in a whole file
        result = yacc.parse(s)
        print(result.pretty())

    if len(sys.argv) == 1:
        while 1:
            try:
                s = input('calc > ')
            except EOFError:
                break
            if not s: continue
            if s[0] == '#':
                s = open(s[1:],"r").read() # read in a whole file
                print(s)
            else:
                s += "\n"
            result = yacc.parse(s)
            print("result",result)
            print(result.pretty())

