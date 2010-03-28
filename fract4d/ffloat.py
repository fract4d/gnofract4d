import exceptions

has_bigmath = False

try:
    import gmpy
    has_bigmath = True
except:
    pass

class PrecisionError(exceptions.Exception):
    def __init__(self):
        exceptions.Exception.__init__(
            self,"Cannot process number: arbitrary precision math is not enabled")

def Float(num,precision=64):
    "Either a builtin float, or a GMP-based bigfloat, if required and supported"
    if precision > 64:
        if has_bigmath:
            return gmpy.mpf(num,precision)
        else:
            raise PrecisionError()        
    return float(num)


    
