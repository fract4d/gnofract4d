#!/usr/bin/env python3

# test symbol table implementation

import collections.abc
import unittest
import copy

from . import fsymbol, function
from .fracttypes import *

class SymbolTest(unittest.TestCase):
    def setUp(self):
        self.t = fsymbol.T()

    def tearDown(self):
        pass

    def testCopy(self):
        self.t["foo"] = Var(Int, 4)
        self.t["@fn1"][0].set_func("sin")
        name = self.t.newTemp(Float)
        c = copy.copy(self.t)

        self.assertEqual(c["foo"].value,4)
        self.assertEqual(c["@fn1"][0].cname,"sin")
        self.assertEqual(c.nextTemp, self.t.nextTemp)
        
        self.t["foo"].value = 5
        self.t["@fn1"][0].set_func("sinh")
        
        self.assertEqual(c["foo"].value,4)
        self.assertEqual(c["@fn1"][0].cname,"sin")
        self.assertTrue(c[name].is_temp == True)
        
    def testParamSlots(self):
        t = fsymbol.T("boo")
        v = Var(Int,1)
        self.assertEqual(-1,v.param_slot)
        t["x"] = v
        self.assertEqual(-1,v.param_slot)

        v2 = Var(Complex,[1.0,2.0])
        self.assertEqual(-1,v2.param_slot)
        t["@p"] = v2
        self.assertEqual(0,v2.param_slot)
        self.assertEqual(2,t.nextParamSlot)

        v3 = Var(Hyper,[1.0,2.0,3.0,4.0])
        self.assertEqual(-1,v3.param_slot)
        t["@pc"] = v3
        self.assertEqual(2,v3.param_slot)
        self.assertEqual(6,t.nextParamSlot)
        
        v4 = Var(Int,77)
        self.assertEqual(-1,v4.param_slot)
        t["@pi"] = v4
        self.assertEqual(6,v4.param_slot)
        self.assertEqual(7,t.nextParamSlot)

        # functions shouldn't affect this
        f = fsymbol.OverloadList([function.Func([Int],Int,"ident")])
        t["@myfunc"] = f
        self.assertNotEqual(True,hasattr(f,"param_slot"))
        self.assertEqual(7,t.nextParamSlot)

        v5 = Var(Image,None)
        self.assertEqual(-1,v5.param_slot)
        t["@image"] = v5
        self.assertEqual(7,v5.param_slot)
        self.assertEqual(8,t.nextParamSlot)
        
    def testOrderOfParams(self):
        "Are parameters returned in the right order?"
        t = fsymbol.T("f")
        t["@a"] = Var(Int,1)

        op = t.order_of_params()
        self.assertEqual(0, op["t__a_a"])

        # add another param
        t["@y"] = Var(Int,1)
        op = t.order_of_params()
        self.assertEqual(1, op["t__a_y"])

        # and another earlier in the alphabet. This should
        # still end up later, unlikely when order_of_params
        # sorted by keys
        t["@p"] = Var(Int,1)
        op = t.order_of_params()
        self.assertEqual(2, op["t__a_p"])
        self.assertEqual(3, op["__SIZE__"])

    def testParameterTypes(self):
        t = fsymbol.T("f")
        t["@a"] = Var(Int,1)
        t["@b"] = Var(Bool,False)
        t["@c"] = Var(Float,1.0)
        t["@d"] = Var(Complex,[10,20])
        t["@e"] = Var(Hyper,[1.0,1.0,1.0,1.0])
        t["@f"] = Var(Gradient,None)
        t["@g"] = Var(Color,[0.0,1.0,2.0,3.0])
        t["@h"] = Var(Image, None)
        
        self.assertEqual(
            [Int,
             Bool,
             Float,
             Float,Float,
             Float,Float,Float,Float,
             Gradient,
             Float,Float,Float,Float,
             Image],
            t.type_of_params())
    
    def testOrderOfParamsMerges(self):
        (t1,t2) = (fsymbol.T("a"), fsymbol.T("b"))
        t1["@a"] = Var(Int, 1)
        t1["d"] = Var(Int,100)
        t2["d"] = Var(Int,200)
        t2["@a"] = Var(Int, 3)
        t2["@b"] = Var(Float, 2)        
        t1["@myfunc"] = fsymbol.OverloadList([function.Func([Int],Int,"ident")])
        t2["@myotherfunc"] = fsymbol.OverloadList([function.Func([Int],Int,"ident")])
        t1.merge(t2)

        op = t1.order_of_params()
        self.assertEqual(0, op["t__a_a"])
        self.assertEqual(1, op["t__a_ba"])
        self.assertEqual(2, op["t__a_bb"])
        self.assertEqual(-1, t1["d"].param_slot)
        self.assertEqual(-1, t2["d"].param_slot)

    def testZ(self):
        t1 = fsymbol.T("a")
        x = t1["z"]
        self.assertEqual(-1,x.param_slot)
        
    def testGetDefaultParamSetsSlot(self):
        t = fsymbol.T("f")
        x = t["@p1"]
        self.assertEqual(0,x.param_slot)
        
    def testPrefix(self):
        t = fsymbol.T("boo")
        v = Var(Int,1)
        t["x"] = v
        self.assertEqual(t["x"].cname,"boox")
        self.assertEqual(t.realName("@x"),"t__a_x")
        self.assertEqual(t.mangled_name("@x"),"t__a_x")
        
    def testSqr(self):
        sqr_c = self.t[("sqr")][2];
        sqr_i = self.t[("sqR")][0];
        self.assertTrue(isinstance(sqr_c, function.Func) and sqr_c.ret == Complex)
        self.assertTrue(isinstance(sqr_i, function.Func) and sqr_i.args == [Int])

    def testNoOverride(self):
        self.assertRaises(KeyError,self.t.__setitem__,("sqr"),1)
        
    def testAddCheckVar(self):
        self.t["fish"] = Var(Int,1)
        self.assertTrue("fish" in self.t)
        self.assertTrue("FisH" in self.t)
        x = self.t["fish"]
        self.assertTrue(isinstance(x,Var))
        self.assertEqual(x.value, 1)
        self.assertEqual(x.type, Int)

    def test_user(self):
        self.t["fish"] = Var(Int,1,1)
        self.assertTrue(self.t.is_user("fish"))
        self.assertTrue(not self.t.is_user("z"))
        self.assertTrue(not self.t.is_user("cmag"))
        
    def test_expand(self):
        l = fsymbol.efl("foo", "[_,_] , _", [Int, Float, Complex])
        self.assertEqual(len(l),3)
        self.assertEqual(l[0].ret, Int)
        self.assertEqual(l[1].args, [Float,Float])

    def test_matches(self):
        times = self.t["*"]
        times_i = times[0]
        self.assertTrue(times_i.matchesArgs([Int,Int]))
        self.assertTrue(times_i.matchesArgs([Int,Bool]))
        self.assertTrue(not times_i.matchesArgs([Int,Color]))

    def test_use_hash(self):
        self.assertRaises(KeyError, self.t.__setitem__, ("#foo"), 1)
        
    def test_clash_with_secret_vars(self):
        self.assertRaises(KeyError, self.t.__setitem__, ("t__temp0"), 1)

    def testStartsWithHash(self):
        self.assertRaises(KeyError,self.t.__setitem__,"#wombat",1)

    def testAt(self):
        self.t["@foo"] = Var(Int, 1, 0)
        self.assertEqual(self.t.realName("@foo"), "t__a_foo")

    def testCName(self):
        self.t["bar"] = Var(Int,1,0)
        self.assertEqual(self.t["bAr"].cname,"bar")
        v = Var(Int,1,0)
        v.cname = "fish"
        self.t["var_with_name"] = v
        self.assertEqual(self.t["var_with_name"].cname,"fish")
        self.assertEqual(self.t["cos"][0].cname,"cos")
        
    def testZ(self):
        self.assertEqual(self.t["z"].type, Complex)

    def testAlias(self):
        self.assertEqual(self.t["#z"].cname, self.t["z"].cname)
        self.t["#z"].value = [47.0, 12.0]
        self.assertEqual(self.t["z"].value,[47.0, 12.0])

    def testParams(self):
        self.assertEqual(self.t["@p6"].type, Complex)
        self.assertEqual(self.t["@p1"], self.t["p1"])
        self.assertEqual(self.t["@fn1"][0].ret, Complex)

        params = self.t.parameters()
        self.assertTrue(isinstance(params["t__a_fn1"],function.Func))

    def testFirst(self):
        self.assertEqual(self.t["z"].first(),self.t["z"])
        self.assertTrue(isinstance(self.t["@fn1"].first(), function.Func))
        
    def testReset(self):
        self.t["fish"] = Var(Int, 1, 1)
        self.t.reset()
        self.assertRaises(KeyError, self.t.__getitem__, ("fish"))

    def testChangeValue(self):
        x = Var(Int,1,1)
        self.t["x"] = x
        self.assertEqual(1, self.t["x"].value)
        x.value = 20
        self.assertEqual(20, self.t["x"].value)
                
    def testAvailable(self):
        fnames = self.t.available_param_functions(Complex,[Complex])
        self.assertEqual(fnames.count("ident"),1)
        self.assertEqual(fnames.count("flip"),1)
        self.assertEqual(fnames.count("cabs"),0)
        self.assertEqual(fnames.count("t__a_fn1"),0)
        self.assertEqual(fnames.count("t__neg"),0)
        fnames = self.t.available_param_functions(Float,[Complex])
        exp_fnames = ['cabs','manhattanish','real','imag','manhattan','atan2']
        for exp in exp_fnames:
            self.assertEqual(fnames.count(exp),1,exp)

        cnames = self.t.available_param_functions(Color, [Color, Color])
        self.assertEqual(cnames.count('+'),0, "shouldn't find operators")
        exp_cnames = ['mergenormal']
        for exp in exp_cnames:
            self.assertEqual(cnames.count(exp),1,exp)
        
    def testAllSymbolsWork(self):
        for (name,val) in list(self.t.default_dict.items()):
            try:
                for item in val:
                    self.assertIsValidFunc(item)
            except TypeError:
                self.assertIsValidVar(val)

    def testTemps(self):
        name = self.t.newTemp(Float)
        self.assertTrue(self.t[name].is_temp == True)

    def assertIsValidVar(self, val):
        if isinstance(val,Var):
            # ok
            pass
        elif isinstance(val,fsymbol.Alias):
            realvar = self.t[val.realName]
            self.assertEqual(isinstance(realvar, Var) or
                             isinstance(realvar, fsymbol.OverloadList), True)
        else:
            self.fail("weird variable")
        
    def assertIsValidFunc(self,val):
        specialFuncs = [ "noteq", "eq" ]
        self.assertTrue(isinstance(val.genFunc, collections.abc.Callable) or
                        val.genFunc == None or
                        specialFuncs.count(val.cname) > 0, val.cname)
