# lextab.py. This file automatically created by PLY (version 3.9). Don't edit!
_tabversion   = '3.8'
_lextokens    = {'COMMENT', 'FORM_END', 'BOOL_NEG', 'SECT_PARMS', 'COMMENT_FORMULA', 'ESCAPED_NL', 'NEWLINE', 'MOD', 'LT', 'HEADING', 'ID', 'LPAREN', 'RPAREN', 'SECT_SET', 'BOOL_AND', 'TIMES', 'STRING', 'GT', 'FUNC', 'EQ', 'NUMBER', 'WHILE', 'GTE', 'PLUS', 'COMMA', 'ELSE', 'CONST', 'ENDHEADING', 'BOOL_OR', 'MINUS', 'COMPLEX', 'FORM_ID', 'UNTIL', 'ELSEIF', 'REPEAT', 'ENDWHILE', 'TYPE', 'ENDFUNC', 'IF', 'POWER', 'ENDIF', 'ENDPARAM', 'ASSIGN', 'RARRAY', 'DIVIDE', 'MAG', 'LTE', 'PARAM', 'LARRAY', 'NEQ', 'SECT_STM'}
_lexreflags   = 0
_lexliterals  = ''
_lexstateinfo = {'INITIAL': 'inclusive'}
_lexstatere   = {'INITIAL': [('(?P<t_COMMENT_FORMULA>;?[Cc]omment\\s*{[^}]*})|(?P<t_FORM_ID>[^\\r\\n;"\\{]+{)|(?P<t_NUMBER>(?=\\d|\\.\\d)\\d*(\\.\\d*)?([Ee]([+-]?\\d+))?i?)|(?P<t_SECT_SET>(([Dd][Ee][Ff][Aa][Uu][Ll][Tt])|([Ss][Ww][Ii][Tt][Cc][Hh])|([Bb][Uu][Ii][Ll][Tt][Ii][Nn])):)|(?P<t_SECT_PARMS>(([Gg][Rr][Aa][Dd][Ii][Ee][Nn][Tt])|([Ff][Rr][Aa][Cc][Tt][Aa][Ll])|([Ll][Aa][Yy][Ee][Rr])|([Mm][Aa][Pp][Pp][Ii][Nn][Gg])|([Ff][Oo][Rr][Mm][Uu][Ll][Aa])|([Ii][Nn][Ss][Ii][Dd][Ee])|([Oo][Uu][Tt][Ss][Ii][Dd][Ee])|([Aa][Ll][Pp][Hh][Aa])|([Oo][Pp][Aa][Cc][Ii][Tt][Yy])):)|(?P<t_SECT_STM>(([Gg][Ll][Oo][Bb][Aa][Ll])|([Tt][Rr][Aa][Nn][Ss][Ff][Oo][Rr][Mm])|([Ii][Nn][Ii][Tt])|([Ll][Oo][Oo][Pp])|([Ff][Ii][Nn][Aa][Ll])|([Bb][Aa][Ii][Ll][Oo][Uu][Tt]))?:)|(?P<t_ID>[@#]?[a-zA-Z_][a-zA-Z0-9_]*)|(?P<t_ESCAPED_NL>\\\\\\r?\\s*\\n)|(?P<t_COMMENT>;[^\\n]*)|(?P<t_NEWLINE>\\r*\\n)|(?P<t_STRING>"[^"]*")|(?P<t_BOOL_OR>\\|\\|)|(?P<t_GTE>>=)|(?P<t_NEQ>!=)|(?P<t_BOOL_AND>&&)|(?P<t_LTE><=)|(?P<t_POWER>\\^)|(?P<t_RARRAY>\\])|(?P<t_LPAREN>\\()|(?P<t_LARRAY>\\[)|(?P<t_MAG>\\|)|(?P<t_PLUS>\\+)|(?P<t_FORM_END>\\})|(?P<t_EQ>==)|(?P<t_TIMES>\\*)|(?P<t_RPAREN>\\))|(?P<t_MOD>%)|(?P<t_LT><)|(?P<t_COMMA>,)|(?P<t_ASSIGN>=)|(?P<t_DIVIDE>/)|(?P<t_GT>>)|(?P<t_BOOL_NEG>!)|(?P<t_MINUS>-)', [None, ('t_COMMENT_FORMULA', 'COMMENT_FORMULA'), ('t_FORM_ID', 'FORM_ID'), ('t_NUMBER', 'NUMBER'), None, None, None, ('t_SECT_SET', 'SECT_SET'), None, None, None, None, ('t_SECT_PARMS', 'SECT_PARMS'), None, None, None, None, None, None, None, None, None, None, ('t_SECT_STM', 'SECT_STM'), None, None, None, None, None, None, None, ('t_ID', 'ID'), ('t_ESCAPED_NL', 'ESCAPED_NL'), ('t_COMMENT', 'COMMENT'), ('t_NEWLINE', 'NEWLINE'), ('t_STRING', 'STRING'), (None, 'BOOL_OR'), (None, 'GTE'), (None, 'NEQ'), (None, 'BOOL_AND'), (None, 'LTE'), (None, 'POWER'), (None, 'RARRAY'), (None, 'LPAREN'), (None, 'LARRAY'), (None, 'MAG'), (None, 'PLUS'), (None, 'FORM_END'), (None, 'EQ'), (None, 'TIMES'), (None, 'RPAREN'), (None, 'MOD'), (None, 'LT'), (None, 'COMMA'), (None, 'ASSIGN'), (None, 'DIVIDE'), (None, 'GT'), (None, 'BOOL_NEG'), (None, 'MINUS')])]}
_lexstateignore = {'INITIAL': ' \t\r'}
_lexstateerrorf = {'INITIAL': 't_error'}
_lexstateeoff = {}
