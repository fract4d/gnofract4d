# generally useful funcs for reading in .fct files

import base64
import io
import gzip


class T:
    def __init__(self, parent=None):
        self.endsect = "[endsection]"
        self.tr = str.maketrans("[] ", "___")
        self.parent = parent

    def warn(self, msg):
        if self.parent:
            self.parent.warn(msg)

    def load(self, f):
        line = f.readline()
        while line:
            (name, val) = self.nameval(line)
            if name is not None:
                if name == self.endsect:
                    break

                if name == "compressed":
                    compressed = True
                else:
                    compressed = False
                if val == "[":
                    # start of a multi-line parameter
                    line = f.readline()
                    vals = []
                    while line != "" and line.rstrip() != "]":
                        if compressed:
                            line = line.rstrip()
                        vals.append(line)
                        line = f.readline()
                    val = "".join(vals)

                if name == "compressed":
                    self.decompress(val)
                else:
                    self.parseVal(name, val, f)

            line = f.readline()

    def parseVal(self, name, val, f, sect=""):
        # when reading in a name/value pair, we try to find a method
        # somewhere in the hierarchy of current class called parse_name
        # then call that
        methname = "parse_" + sect + name.translate(self.tr)
        meth = None

        klass = self.__class__
        while True:
            meth = klass.__dict__.get(methname)
            if meth is not None:
                break
            bases = klass.__bases__
            if len(bases) > 0:
                klass = bases[0]
            else:
                break

        if meth:
            return meth(self, val, f)
        elif name != "":
            self.warn("ignoring unknown attribute '%s'" % name)

    def decompress(self, b64string):
        # decompress remaining codes
        bytes = base64.b64decode(b64string.encode("latin_1"))
        embedded_file = io.TextIOWrapper(
            gzip.GzipFile(None, "rb", 9, io.BytesIO(bytes)))
        self.load(embedded_file)

    def nameval(self, line):
        x = line.rstrip().split("=", 1)
        if len(x) == 0:
            return (None, None)
        if len(x) < 2:
            val = None
        else:
            val = x[1]
        return (x[0], val)


class Compressor(io.TextIOWrapper):
    def __init__(self):
        self.sio = io.BytesIO()
        self.gzipfile = gzip.GzipFile(None, "w", 9, self.sio)
        io.TextIOWrapper.__init__(self, self.gzipfile)

    def getvalue(self):
        zippedval = self.sio.getvalue()
        b64 = base64.encodebytes(zippedval)
        val = "compressed=[\n%s\n]" % b64.decode("latin_1")
        return val


class ParamBag(T):
    "A class for reading in and holding a bag of name-value pairs"

    def __init__(self):
        T.__init__(self)
        self.dict = {}

    def parseVal(self, name, val, f, sect=""):
        if name[0] == '[' and name[-1] == "]":
            # start of a section
            sub_bag = ParamBag()
            sub_bag.load(f)
            val = (val, sub_bag)

        self.dict[sect + name] = val
