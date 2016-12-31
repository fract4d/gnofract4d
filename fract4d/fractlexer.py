#!/usr/bin/env python3
# ------------------------------------------------------------
# fractlexer.py
#
# tokenizer for UltraFractal formula files
# ------------------------------------------------------------
import lex
import sys
import re
import string

# set to True to pass through all tokens. This breaks the parser but
# is useful for pretty-printing

keep_all = False

# List of token names.   This is always required
tokens = (
   'NUMBER',
   'COMPLEX',
   'ID',

   'PLUS',
   'MINUS',
   
   'TIMES',
   'DIVIDE',
   'MOD', 
   
   'LPAREN', 
   'RPAREN', 
   'LARRAY',
   'RARRAY',
   'MAG', 
   'POWER',

   'BOOL_NEG',
   'BOOL_OR',
   'BOOL_AND',

   'EQ',
   'NEQ',
   'LT',
   'LTE',
   'GT',
   'GTE',

   'ASSIGN',

   'COMMENT',
   'NEWLINE',
   'ESCAPED_NL',
   'COMMA',
   'STRING',

   'COMMENT_FORMULA',
   'FORM_ID',
   'FORM_END',
   'SECT_SET',
   'SECT_PARMS',
   'SECT_STM',

   # keywords
   'ELSE',
   'ELSEIF',
   'ENDFUNC',
   'ENDHEADING',
   'ENDIF',
   'ENDPARAM',
   'ENDWHILE',
   'FUNC',
   'HEADING',
   'IF',
   'PARAM',
   'REPEAT',
   'UNTIL',
   'WHILE',

   'TYPE',
   'CONST'
)

# lookup table to convert IDs into keywords
keywords = [ "else",
             "elseif",
             "endfunc",
             "endheading",
             "endif",
             "endparam",
             "endwhile",
             "func",
             "heading",
             "if",
             "param",
             "repeat",
             "until",
             "while"]

types = ["bool",
         "color",
         "complex",
         "float",
         "hyper",
         "grad",
         "int",
         "image"]

consts = ["true", "false", "yes", "no"]

lookup = {}
for k in keywords: lookup[k] = k.upper()
for t in types: lookup[t] = "TYPE"
for c in consts: lookup[c] = "CONST"

# Regular expression rules for simple tokens
t_PLUS    = r'\+'
t_MINUS   = r'-'
t_TIMES   = r'\*'
t_DIVIDE  = r'/'
t_MOD     = r'%'
t_LPAREN  = r'\('
t_RPAREN  = r'\)'
t_LARRAY  = r'\['
t_RARRAY  = r'\]'
t_MAG     = r'\|'
t_POWER   = r'\^'
t_BOOL_NEG= r'!'
t_BOOL_OR = r'\|\|'
t_BOOL_AND= r'&&'
t_EQ      = r'=='
t_NEQ     = r'!='
t_LT      = r'<'
t_LTE     = r'<='
t_GT      = r'>'
t_GTE     = r'>='
t_ASSIGN  = r'='
t_COMMA   = r','
t_FORM_END= r'\}' 

# handle stupid "comment" formula blocks specially
# match ; and Comment because some uf repository files do this
def t_COMMENT_FORMULA(t):
    r';?[Cc]omment\s*{[^}]*}'
    newlines = re.findall(r'\n',t.value)
    t.lexer.lineno += len(newlines)
    pass 

# may seem weird, but this includes the starting {
# this is to ensure that the generous pattern match doesn't
# trigger all the time mid-formula (eg, z = "z^2 + c" is a valid formid)

def t_FORM_ID(t):
    r'[^\r\n;"\{]+{'
    # remove trailing whitespace and {
    if not keep_all:
        t.value = re.sub("\s*{$", "", t.value)    
    return t

def t_NUMBER(t):
    r'(?=\d|\.\d)\d*(\.\d*)?([Ee]([+-]?\d+))?i?'
    if t.value[-1]=="i": # a complex constant
        t.value = t.value[0:-1]
        t.type = "COMPLEX" 

    return t

# these have to be functions to give them higher precedence than ID
# the gnarly regexp syntax is so we are case-insensitive (ick)
# and don't match things like "x = pixel:"

# default, switch, builtin
def t_SECT_SET(t):
    r'(([Dd][Ee][Ff][Aa][Uu][Ll][Tt])|([Ss][Ww][Ii][Tt][Cc][Hh])|([Bb][Uu][Ii][Ll][Tt][Ii][Nn])):'
    if not keep_all:
        t.value = re.sub(":$","",t.value)
    return t

# a section containing parameter settings, as found in .ugr and .upr files
# gradient, fractal, layer, mapping, formula, inside, outside, alpha, opacity
def t_SECT_PARMS(t):
    r'(([Gg][Rr][Aa][Dd][Ii][Ee][Nn][Tt])|([Ff][Rr][Aa][Cc][Tt][Aa][Ll])|([Ll][Aa][Yy][Ee][Rr])|([Mm][Aa][Pp][Pp][Ii][Nn][Gg])|([Ff][Oo][Rr][Mm][Uu][Ll][Aa])|([Ii][Nn][Ss][Ii][Dd][Ee])|([Oo][Uu][Tt][Ss][Ii][Dd][Ee])|([Aa][Ll][Pp][Hh][Aa])|([Oo][Pp][Aa][Cc][Ii][Tt][Yy])):'
    if not keep_all:
        t.value = re.sub(":$","",t.value)
    return t

# global, transform, init, loop, final, bailout
def t_SECT_STM(t):
    r'(([Gg][Ll][Oo][Bb][Aa][Ll])|([Tt][Rr][Aa][Nn][Ss][Ff][Oo][Rr][Mm])|([Ii][Nn][Ii][Tt])|([Ll][Oo][Oo][Pp])|([Ff][Ii][Nn][Aa][Ll])|([Bb][Aa][Ii][Ll][Oo][Uu][Tt]))?:'
    if not keep_all:
        t.value = re.sub(":$","",t.value)
    return t

def t_ID(t):
    r'[@#]?[a-zA-Z_][a-zA-Z0-9_]*'
    global lookup
    lookfor = t.value.lower() # case insensitive lookup
    if lookfor in lookup: t.type = lookup[lookfor]
    return t
    
# don't produce tokens for newlines preceded by \
def t_ESCAPED_NL(t):
    r'\\\r?\s*\n'
    t.lexer.lineno += 1

def t_COMMENT(t):
    r';[^\n]*'
    if keep_all:
        return t
    
def t_NEWLINE(t):
    r'\r*\n'
    t.lexer.lineno += 1 # track line numbers
    return t

def t_STRING(t):
    r'"[^"]*"' # embedded quotes not supported in UF?
    if not keep_all:
        t.value = re.sub(r'(^")|("$)',"",t.value) # remove trailing and leading "
        newlines = re.findall(r'\n',t.value)
        t.lexer.lineno += len(newlines)
        t.value = re.sub(r'\\\r?\n[ \t\v]*',"",t.value) # hide \-split lines
    return t
    
# A string containing ignored characters (spaces and tabs)
t_ignore  = ' \t\r'

# Error handling rule
def t_error(t):
    #print("Illegal character '%s' on line %d" % (t.value[0], t.lexer.lineno))
    t.value = t.value[0]
    t.lexer.skip(1)
    return t
    
# Build the lexer
lexer = lex.lex(optimize=1)

def get_lexer():
    global lexer
    lexer = lex.lex(optimize=1)
    return lexer

# debugging
if __name__ == '__main__': #pragma: no cover
    # Test it out
    data = open(sys.argv[1],"r").read()

    # Give the lexer some input
    lex.input(data)

    # Tokenize
    while 1:
        tok = lex.token()
        if not tok: break      # No more input
        print(tok)
