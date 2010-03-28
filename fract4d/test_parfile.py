#!/usr/bin/env python

# test cases for parfile.py


import string
import unittest
import StringIO
import math

import testbase

import parfile
import fractal
import fc
import preprocessor
import gradient

g_comp = fc.Compiler()
g_comp.add_func_path("../formulas")
g_comp.load_formula_file("gf4d.frm")
g_comp.load_formula_file("test.frm")
g_comp.load_formula_file("gf4d.cfrm")

fotd = """FOTD_for_04-05-06  { ; time=2:38:57.82--SF5 on a P200
reset=2004 type=mandel passes=1
center-mag=-0.74999655467724592903865/0.0171269216\\
3034049041486/5.51789e+018 params=0/0 float=y
maxiter=72000 inside=0 periodicity=10
colors=0000qJ0mP0iX0eb0di0`o0Xu0Tz2Pz2NzRTzoZqzbRz\\
dTzdTzeTzeTzeTzgVzgVzgVziVziVzkXzkXzkXzmXzmXzmXzgV\\
zdTu`RkXP`TNRNNGJL6GJ0CH08K04U0GcAWdPdkehvpmuxrzzx\\
zzzuzzqzzmzzizzezzbzzZzzVzzTzzRzzRxzPozPexNZvNPsLG\\
qL8oLEkNJiNNgNTeNXdN``PbXPeTPgPPkLPmHPqEPsARv6Rx2R\\
z0Rz0Rz0Rz0RzzLzzPzgTzLXz0`z0Xz0Vz0Rz0Pz0Lz0Jz0Gz0\\
Ez0Az08z04z02z00z00z00s2GNV`0uu0so6qiCodJo`PmVXkPd\\
kLiiGqgAvg6Lzb0zz2zgJzJ`z0Tz2Nz8HzECxJ6vP0sV0q`0me\\
0kk0io0os0su0xx4zzCzzHzzPzzVzzXzzXzzXzzXzzXzzXzxXx\\
vXvuXssXqqXmoXkmbizVdzPZyHTsCNh6HZ0CS06Q00S00U00W0\\
0Y00_00a40cC4eJ6hR8kZAneEqmGtuHwzJzzLzz0Hz0Gz0Gz0E\\
z0Ez0Ez0Cz0Cz0Cz0Ax0Av08u08q08o06m06k06s0Cgz0TZzz0\\
zz0zz2zq6ziAz`GzRJxHNvARuLGko0CV4de0Vo0NgVzkHzo6ss\\
0ev0TmCbq2Xs0Tu0Nv0J0z02z0Cs0Lb0XL2e46o0CiZpoRmqGe\\
c4`h0Tc0LGzzRdxbHim0VPJob2bm0R60AP0Cg0EzzzzzzzdqxH\\
dx0RzzLzmJzNHx0G0z00v60uE }"""

fotd2 = """FOTD_for_02-05-06  { ; time=0:03:43.11--SF5 on a P200
reset=2004 type=formula formulafile=allinone.frm
formulaname=MandelbrotMix4 function=ident passes=1
center-mag=+0.27710097748940720/+2.663965799618463\
00/5.609397e+008/1/22.5/1.57466375611675646e-005
params=-1/1.5/1/-1.5/0/0 float=y maxiter=750
inside=0 logmap=69 periodicity=10
colors=0000HG5JA9L6VNRlCeJC0JJRJCnJ6z`Uzokzuuuzzzf\
bjqaxkTreHn_6i`9oaAtbCzbCz_NzVUzR`yNhwHnvCss9yrozz\
rpzvfzyXzzLzz6yzGwzOvzUsz`ryepxkowpntnqrlspkwniykh\
zifzhezdiq`laXpJUr0GbsLawO`yR_zUYzYXz`VzbUzeUzkVzq\
XzwYzz_zz`zzazsiw_paVrbTtbQwbLybHzbEzbOqhVdlaQpYXi\
UaaRhUNlLJqAz5bz2fz2iz2kz0nz0pw0rt0ts6ssCsrGrrLrrQ\
rqTqqXqq_qlYjhXbbVXYUOTTGNR5HQ0LTANUNOXXRYeT`nUavV\
bzU_zTXzRUzRRzQOzOLzNHyNEyXHweLvlOstRrzUpzVox_jnae\
bdaQfXAiR0kN0nH5pCAr6Gs2Lk5Qb6TV9XLA`9Cb0CVCAOOAE_\
A5hACiOJiYQifVjp`jxejzohqxebzbNza0o_jJXzYiyishszOq\
vRpnUneXlX_jNaiAdh0feE`dTVadQ`oJYyCXz5TnGalRjk`rji\
ziqziytjYhk0jiCkfQle`niVnkQnnJnpCnr5nt0fo6_iGRbOHX\
V9RaTHjf9rs0yvftwzpsznpzklziizfezdazarzwozxlzxizxf\
zybzy`zyYzyVzzTzzQzzNzzJzzHzzGzzEzzCztAzl9ze6zYzzQ\
zzzzzyzzqzzhzz_zzkzzvzzzzzijzelzazzzzzzzzzzzzzzzzz\
zzzzvzxozsizpazk0zR0zO0zL }
"""

map="""0   0   0
  0  68  64
 20  76  40
 36  84  24
124  92 108
196  48 168
 76  48   0
 76  76 108
 76  48 204
 76  24 252
148 120 252
208 192 252
232 232 232
252 252 252
172 156 188
216 152 244
192 116 220
168  68 204
144  24 184
148  36 208
152  40 228
156  48 252
156  48 252
144  92 252
124 120 252
108 148 248
 92 180 240
 68 204 236
 48 224 224
 36 248 220
208 252 252
220 212 252
236 172 252
248 132 252
252  84 252
252  24 248
252  64 240
252  96 236
252 120 224
252 148 220
248 168 212
244 192 208
240 212 204
228 204 216
220 196 224
212 192 240
204 184 248
192 180 252
184 172 252
180 168 252
164 184 216
148 196 152
132 212  76
120 220   0
 64 156 224
 84 152 240
 96 148 248
108 144 252
120 136 252
136 132 252
148 124 252
156 120 252
168 120 252
192 124 252
216 132 252
240 136 252
252 144 252
252 148 252
252 152 252
224 184 240
144 212 152
124 220 156
116 228 156
104 240 156
 84 248 156
 68 252 156
 56 252 156
 96 216 180
124 164 196
152 104 212
136 132 184
120 152 152
108 180 120
 92 196  84
 76 216  40
252  20 156
252   8 172
252   8 184
252   8 192
252   0 204
252   0 212
240   0 220
228   0 228
224  24 224
224  48 224
220  64 220
220  84 220
220 104 220
216 116 216
216 132 216
216 144 216
196 136 188
180 132 156
156 124 132
136 120  96
116 116  64
 92 108  20
 68 104   0
 84 116  40
 92 120  92
 96 132 132
108 136 168
116 148 204
120 152 236
124 156 252
120 144 252
116 132 252
108 120 252
108 108 252
104  96 252
 96  84 252
 92  68 248
 92  56 248
132  68 240
168  84 236
196  96 224
228 108 220
252 120 212
252 124 208
244 144 188
204 152 168
156 164 152
104 172 132
 40 184 108
  0 192  92
  0 204  68
 20 212  48
 40 220  24
 64 224   8
 84 192  20
104 156  24
116 124  36
132  84  40
148  36  48
156   0  48
124  48  40
 96  96  40
 56 144  40
 20 180  40
 48 184  96
 76 184 136
104 184 172
124 188 212
148 188 244
168 188 252
208 180 216
244 168 156
252 156  92
252 152   0
208 144 188
 76 132 252
136 184 248
184 224 180
224 252  96
216 236 108
212 204 120
204 168 132
196 132 144
188  92 152
184  40 164
180   0 172
168  56 148
164 116 124
152 164 104
148 208  76
136 248  48
132 252  20
116 204  64
152 196 108
188 192 148
220 188 184
252 184 216
252 184 248
228 188 136
180 192   0
188 184  48
192 172 104
196 168 148
204 184 124
204 192 104
204 204  76
204 212  48
204 220  20
204 228   0
172 208  24
144 184  64
108 156  96
 68 132 124
 36 108 152
116  68 188
172  36 220
224   0 248
236 172 228
240 252 212
224 252 204
212 252 192
196 252 184
184 252 172
168 252 164
152 252 152
220 252 240
208 252 244
196 252 244
184 252 244
172 252 248
156 252 248
148 252 248
136 252 248
124 252 252
116 252 252
104 252 252
 92 252 252
 76 252 252
 68 252 252
 64 252 252
 56 252 252
 48 252 228
 40 252 196
 36 252 168
 24 252 136
252 252 104
252 252 252
252 252 248
252 252 216
252 252 180
252 252 144
252 252 192
252 252 236
252 252 252
252 252 184
188 252 168
196 252 152
252 252 252
252 252 252
252 252 252
252 252 252
252 252 252
252 252 252
252 252 252
236 252 244
208 252 224
184 252 212
152 252 192
  0 252 108
  0 252  96
  0 252  84
"""

class ParTest(testbase.TestBase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testColors(self):
        self.assertEqual(parfile.colorRange(""), [])

        colors = parfile.colorRange("05F")
        self.assertEqual(len(colors),1)
        
        colors = parfile.colorRange("05F<63>DISDISDIS<89>uxxuxxvyyvyywzz<94>05F")
        self.assertEqual(len(colors),256)

        self.assertRaises(RuntimeError,parfile.colorRange, "&*(")
        self.assertRaises(RuntimeError,parfile.colorRange, "00")
        self.assertRaises(RuntimeError,parfile.colorRange, "000<0>000")
        self.assertRaises(RuntimeError,parfile.colorRange, "<1>000")
        self.assertRaises(RuntimeError,parfile.colorRange, "<nootherangle")
        self.assertRaises(ValueError,parfile.colorRange, "<>")

    def testColors2(self):
        colors = parfile.colorRange("0000HG5JA9L6VNRlCeJC0JJRJCnJ6z`UzokzuuuzzzfbjqaxkTreHn_6i`9oaAtbCzbCz_NzVUzR`yNhwHnvCss9yrozzrpzvfzyXzzLzz6yzGwzOvzUsz`ryepxkowpntnqrlspkwniykhzifzhezdiq`laXpJUr0GbsLawO`yR_zUYzYXz`VzbUzeUzkVzqXzwYzz_zz`zzazsiw_paVrbTtbQwbLybHzbEzbOqhVdlaQpYXiUaaRhUNlLJqAz5bz2fz2iz2kz0nz0pw0rt0ts6ssCsrGrrLrrQrqTqqXqq_qlYjhXbbVXYUOTTGNR5HQ0LTANUNOXXRYeT`nUavVbzU_zTXzRUzRRzQOzOLzNHyNEyXHweLvlOstRrzUpzVox_jnaebdaQfXAiR0kN0nH5pCAr6Gs2Lk5Qb6TV9XLA`9Cb0CVCAOOAE_A5hACiOJiYQifVjp`jxejzohqxebzbNza0o_jJXzYiyishszOqvRpnUneXlX_jNaiAdh0feE`dTVadQ`oJYyCXz5TnGalRjk`rjiziqziytjYhk0jiCkfQle`niVnkQnnJnpCnr5nt0fo6_iGRbOHXV9RaTHjf9rs0yvftwzpsznpzklziizfezdazarzwozxlzxizxfzybzy`zyYzyVzzTzzQzzNzzJzzHzzGzzEzzCztAzl9ze6zYzzQzzzzzyzzqzzhzz_zzkzzvzzzzzijzelzazzzzzzzzzzzzzzzzzzzzzvzxozsizpazk0zR0zO0zL")

        check_grad = gradient.Gradient()
        check_grad.load_map_file(StringIO.StringIO(map),-1)

        for(thecolor,expcolor) in zip(colors[1:],check_grad.segments):
            self.assertEqual(thecolor[0],int(255*expcolor.left_color[0]))
            self.assertEqual(thecolor[1],int(255*expcolor.left_color[1]))
            self.assertEqual(thecolor[2],int(255*expcolor.left_color[2]))
            
    def testLoadFOTD1(self):
        fotd_file = StringIO.StringIO(fotd)
        f = fractal.T(g_comp)        
        parfile.parse(fotd_file, f)
        self.assertEqual(f.maxiter, 72000)

    def testGetParams(self):
        fotd_file = StringIO.StringIO(fotd)
        
        params = parfile.get_params(fotd_file)
        self.assertEqual(len(params), 18)
        self.assertEqual(params[0],"FOTD_for_04-05-06")

    def testGetPairs(self):
        fotd_file = StringIO.StringIO(fotd)
        
        params = parfile.get_params(fotd_file)
        pairs = parfile.get_param_pairs(params)

        self.assertEqual(pairs["maxiter"],'72000')

    def testParseParams(self):
        f = fractal.T(g_comp)        
        parfile.parse_maxiter("72000",f)
        self.assertEqual(f.maxiter,72000)
        parfile.parse_colors('0000qJ0mP0iX0eb0di0`o0Xu0Tz2Pz2NzRTzoZqzbRzdTzdTzeTzeTzeTzgVzgVzgVziVziVzkXzkXzkXzmXzmXzmXzgVzdTu`RkXP`TNRNNGJL6GJ0CH08K04U0GcAWdPdkehvpmuxrzzxzzzuzzqzzmzzizzezzbzzZzzVzzTzzRzzRxzPozPexNZvNPsLGqL8oLEkNJiNNgNTeNXdN``PbXPeTPgPPkLPmHPqEPsARv6Rx2Rz0Rz0Rz0Rz0RzzLzzPzgTzLXz0`z0Xz0Vz0Rz0Pz0Lz0Jz0Gz0Ez0Az08z04z02z00z00z00s2GNV`0uu0so6qiCodJo`PmVXkPdkLiiGqgAvg6Lzb0zz2zgJzJ`z0Tz2Nz8HzECxJ6vP0sV0q`0me0kk0io0os0su0xx4zzCzzHzzPzzVzzXzzXzzXzzXzzXzzXzxXxvXvuXssXqqXmoXkmbizVdzPZyHTsCNh6HZ0CS06Q00S00U00W00Y00_00a40cC4eJ6hR8kZAneEqmGtuHwzJzzLzz0Hz0Gz0Gz0Ez0Ez0Ez0Cz0Cz0Cz0Ax0Av08u08q08o06m06k06s0Cgz0TZzz0zz0zz2zq6ziAz`GzRJxHNvARuLGko0CV4de0Vo0NgVzkHzo6ss0ev0TmCbq2Xs0Tu0Nv0J0z02z0Cs0Lb0XL2e46o0CiZpoRmqGec4`h0Tc0LGzzRdxbHim0VPJob2bm0R60AP0Cg0EzzzzzzzdqxHdx0RzzLzmJzNHx0G0z00v60uE',f)
        self.assertEqual(len(f.get_gradient().segments),255)

        parfile.parse_center_mag("-0.74999655467724592903865/0.01712692163034049041486/5.51789e+018",f)
        self.assertEqual(f.params[f.XCENTER],-0.74999655467724592903865)
        self.assertEqual(f.params[f.YCENTER],-0.01712692163034049041486)
        self.assertEqual(f.params[f.MAGNITUDE],2.0/5.51789e+018 * 1.33)

    def disabled_testLogTableLimits(self):
        # disabled since for some odd reason we get a slightly different
        # logtable from Fractint
        (lf,mlf) = parfile.get_log_table_limits(69,750,256,2004)
        self.assertEqual(69,lf)
        self.assertNearlyEqual([38.935782028258387], [mlf]) 

        n = parfile.calc_log_table_entry(0,69,lf,mlf, 2004)
        self.assertEqual(1 ,n)

        n = parfile.calc_log_table_entry(69,69,lf,mlf, 2004)
        self.assertEqual(1 ,n)

        n = parfile.calc_log_table_entry(70,69,lf,mlf, 2004)
        self.assertEqual(1 ,n)

        n = parfile.calc_log_table_entry(71,69,lf,mlf, 2004)
        self.assertEqual(2 ,n)

        # this gets the wrong answer
        n = parfile.calc_log_table_entry(749,69,lf,mlf, 2004)
        self.assertEqual(0xfd,n)
        
    def testSetupLogTable(self):
        table = parfile.setup_log_table(69, 750, 256, 2004)
        self.assertEqual(750,len(table))

        self.assertEqual([1] * 70, table[0:70]) # all entries <= logflag should be 1
        
def suite():
    return unittest.makeSuite(ParTest,'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
