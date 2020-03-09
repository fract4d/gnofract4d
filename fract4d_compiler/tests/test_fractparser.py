#!/usr/bin/env python3

import re
import unittest

from fract4d_compiler import preprocessor, fractparser, fractlexer, absyn


class ParserTest(unittest.TestCase):
    def setUp(self):
        self.parser = fractparser.parser
        fractlexer.lexer.lineno = 1
        #self.parser.lexer.lineno = 1

    def parse(self, s):
        fractlexer.lexer.lineno = 1
        pp = preprocessor.T(s)
        return self.parser.parse(pp.out())

    def tearDown(self):
        self.parser.restart()

    def testEmpty(self):
        tree = self.parse("\n")
        self.assertTrue(absyn.CheckTree(tree))
        # print tree.pretty()

    def testEmptyFormula(self):
        tree = self.parse("t1 {\n}\n")
        self.assertTrue(absyn.CheckTree(tree))
        formula = tree.children[0]
        self.assertTrue(formula.type == "formula" and formula.leaf == "t1")
        # print tree.pretty()

    def testErrorThenFormula(self):
        tree = self.parse("gibberish~\nt1 {\n}\n")
        self.assertTrue(absyn.CheckTree(tree))
        # print tree.pretty()
        formula = tree.children[0]
        self.assertTrue(formula.type == "formula" and formula.leaf == "t1")

    def testErrorInFormula(self):
        tree = self.parse("t1 {\n ~\n}\n")
        self.assertTrue(absyn.CheckTree(tree))
        # print tree.pretty()
        formula = tree.children[0]
        self.assertTrue(formula.type == "formula")
        err = formula.children[0]
        self.assertTrue(err.type == "error")
        self.assertNotEqual(re.search("^2:", err.leaf), None,
                            "bad error message line number")

    def testErrorBeforeAndInFormula(self):
        tree = self.parse("gibberish\nt1 {\n ~\n}\n")
        self.assertTrue(absyn.CheckTree(tree))
        # print tree.pretty()
        formula = tree.children[0]
        self.assertTrue(formula.type == "formula")
        err = formula.children[0]
        self.assertTrue(err.type == "error")
        self.assertNotEqual(re.search("^3:", err.leaf), None,
                            "bad error message line number")

    def testErrorAfterFormula(self):
        tree = self.parse("t1{\n}\ngibberish")
        self.assertTrue(absyn.CheckTree(tree))

    def testNoNewlineAtEnd(self):
        t1 = self.parse("t1 {\n:\n}")
        self.assertIsValidParse(t1)

    def testOneStm(self):
        t1 = self.parse("t1 {\nt=1\n}")
        self.assertIsValidParse(t1)

    def testIfdef(self):
        self.assertParsesEqual('''
        $define foo
        $ifdef foo
        x = 2 * 3
        $else
        x = 3 * 2
        $endif''', 'x = 2 * 3')

    def testBadPreProcessor(self):
        self.assertIsBadFormula(self.makeMinimalFormula('$foo'),
                                "unexpected preprocessor", 3)

    def testPrecedence(self):
        self.assertParsesEqual(
            "x = 2 * 3 + 1 ^ -7 / +2 - |4 - 1|",
            "x = ((2 * 3) + ((1 ^ (-7)) / 2)) - | 4 - 1|")

    def testBooleanPrecedence(self):
        self.assertParsesEqual(
            "2 * 3 > 1 + 1 && x + 1 <= 4.0 || !d >= 2.0",
            "(((2 * 3) > (1 + 1)) && ((x + 1) <= 4.0)) || ((!d) >= 2.0)")

    def testAssociativity(self):
        self.assertParsesEqual(
            "a = b = c",
            "a = (b = c)")
        self.assertParsesEqual(
            "a + b + c - d - e",
            "(((a+b)+c)-d)-e")
        self.assertParsesEqual(
            "a^b^c",
            "a^(b^c)")

    def testGradient(self):
        t1 = self.parse('''cl1rorangemixed {
gradient:
 title="cl1rorangemixed" smooth=no
 index=0 color=5153516
 index=2 color=5087212
 index=399 color=5349352
}
        ''')
        self.assertIsValidParse(t1)

        settings = t1.children[0].children[0].children

        names = ["title", "smooth",
                 "index", "color",
                 "index", "color",
                 "index", "color"]

        vals = ["cl1rorangemixed", False,
                0, 5153516,
                2, 5087212,
                399, 5349352]

        for (name, val, setting) in zip(names, vals, settings):
            self.assertEqual(setting.children[0].leaf, name)
            self.assertEqual(setting.children[1].leaf, val)

    def testAklUpr(self):
        t1 = self.parse('''demo4MedialSmooth {
; \xc2 Andreas Lober 2000
; all rights reserved
; for personal use only
fractal:
  title="demo4MedialSmooth" width=640 height=512
  author="Andreas Lober (AKL)" created="October 31, 2000" numlayers=5
layer:
  outsolid=14548992 outalpha=0 method=multipass caption="New Layer 2"
  opacity=80 visible=yes alpha=no mergemode=softlight
mapping:
  center=-0.287881828498840332/0.592228307628631592 magn=1424.6273242601272
  angle=0
formula:
  filename="Standard.ufm" entry="FastJulia" maxiter=250 percheck=off
  p_Seed=0.55/-0.21875 p_Bailout=4
inside:
  transfer=none repeat=yes
outside:
  filename="akl-t-math.ucl" entry="akl-MedialSmooth" transfer=log
  repeat=yes p_calculate="Angel" p_smooth=0 p_watch="Astro23"
  p_fixit="Minimum" p_disturbFixFactor=0.1 p_disturbMode="Log"
  p_colorby="Fiximum Distance" p_numIterMode="Normal" p_trapMode="None"
  p_lowerTrap=1 p_upperTrap=2 p_skipMode="None" p_skipConst=3
  p_startDistortion="#z" p_minMax=no p_xWaveMode="None" p_yWaveMode="None"
  p_xWaveFreq=1 p_yWaveFreq=1 p_xWaveWeight=1 p_yWaveWeight=1
  p_xWaveConst=0 p_yWaveConst=0 p_xWaveOffset=0 p_yWaveOffset=0
  p_xWaveExp=1 p_yWaveEyp=1 p_wavesLoop=1 p_wavesLoopMode="Static"
  p_wavesGrowFreq=1 p_rotDegree=0 p_rotCentre=0/0 p_zJouk=0/0
  p_vectorJouk=0/0 p_curveJouk=0/0 p_coord="Rectangular" p_coordLoop=1
  p_coordMode="Static" p_lattice="None" p_lattFac1=1/0 p_lattFac2=1/0
  p_lattOffset=0/0 p_colour_limit=0 p_init_z="Always New" p_globalScale=0
  p_globalDither=0 p_shape="None" p_radius=0.5 p_inner_scale=3
  p_inner_amount=0 p_d_randomness=0 p_turnMode=no p_turnScale=1
  p_turnScaleMode="Round" p_corte1=4 p_corte2=2 p_barnMode="None"
  p_barnScale=0 p_barnScaleMode="Round" p_barnSeed=0.6/1.1 p_barnShift=1
  p_disturb_fbm=0 p_disturb_fbm_mode="Sum only" p_disturb_fbm_apply="Pixel"
  p_disturb_fbm_scale=1 p_disturb_fbm_octaves=9 p_disturb_fbm_lattice=no
  p_l_randomness=0 p_txtr_verlauf_Line1=0/0 p_txtr_verlauf_Line2=1/1
  p_txtr_verlauf_exponent=1.5 p_txtr_verlauf_Rot=0
  p_txtr_verlauf_RotCentre=0/0 p_f_randomness=0 p_f_rand_verlaufMode="None"
  p_base4txtr="Z" p_reachThrough=no p_txtr_gnarl=0
  p_f_Gnarl_verlaufMode="None" p_f_Gnarl_verlaufOffset=0
  p_txtr_gnarl_lattice="Normal" p_txtr_gnarl_type="x" p_txtr_gnarl_scale=1
  p_txtr_gnarl_size=1 p_txtr_gnarl_octaves=5 p_txtr_gnarl_limit=0
  p_txtr_PopCorn=0 p_f_PopCorn_verlaufMode="None"
  p_f_PopCorn_verlaufOffset=0 p_txtr_PopCorn_lattice="Normal"
  p_txtr_PopCorn_type="x" p_txtr_PopCorn_scale=1 p_txtr_PopCorn_size=1
  p_txtr_PopCorn_limit=0 p_txtr_PopCorn_octaves=5 p_txtr_SFBM=0
  p_f_SFBM_verlaufMode="None" p_f_SFBM_verlaufOffset=0
  p_txtr_SFBM_lattice="Normal" p_txtr_SFBM_mode="Raw... (Sam's)"
  p_txtr_SFBM_scale=1 p_txtr_SFBM_scaledis="1/scale" p_txtr_SFBM_size=0.1
  p_txtr_SFBM_magn=1.2 p_txtr_SFBM_limit=0 p_txtr_SFBM_rot=28
  p_txtr_SFBM_power=1 p_txtr_SFBM_mod="Use sqrt(i)" p_txtr_SFBM_seed=123094
  p_txtr_SFBM_octaves=5 p_txtr_Primes=0 p_f_Primes_verlaufMode="None"
  p_f_Primes_verlaufOffset=0 p_txtr_Primes_lattice="Normal"
  p_txtr_Primes_scale=1 p_txtr_Primes_size=0.5
  p_txtr_primes_withFinalTrunc=yes p_txtr_primes_where2start=1
  p_txtr_primes_lengthOfSnip=1 p_txtr_primes_Mode="Angel"
  p_txtr_primes_limit=0 p_txtr_Gauss=0 p_f_Gauss_verlaufMode="None"
  p_f_Gauss_verlaufOffset=0 p_txtr_Gauss_lattice="Normal"
  p_txtr_Gauss_type="d" p_txtr_Gauss_scale=1 p_txtr_Gauss_size=1
  p_txtr_Gauss_limit=0 p_txtr_Turn=0 p_f_Turn_verlaufMode="None"
  p_f_Turn_verlaufOffset=0 p_txtr_Turn_lattice="Normal" p_txtr_Turn_scale=1
  p_txtr_Turn_size=1 p_txtr_Turn_limit=0 p_txtr_Turn_corte1=4
  p_txtr_Turn_corte2=2 p_txtr_Check=0 p_f_Check_verlaufMode="None"
  p_f_Check_verlaufOffset=0 p_txtr_Check_scale=1 p_txtr_Checker=2
  p_txtr_Check_test="Prod" p_txtr_Check_shape="Square"
  p_txtr_Check_shConst=1 p_txtr_Check_col="Flag" p_txtr_Check_invert=no
  p_txtr_Check_divide="None" p_txtr_Check_limit=0 p_txtr_Pick153=0
  p_f_Pick153_verlaufMode="None" p_f_Pick153_verlaufOffset=0
  p_txtr_Pick153_lattice="Normal" p_txtr_Pick153_scale=1 p_txtr_scale153=1
  p_txtr_numOfTestsPick153=1 p_txtr_Pick153_col="Sum"
  p_txtr_Pick153_limit=0 p_txtr_SumDiv=0 p_f_SumDiv_verlaufMode="None"
  p_f_SumDiv_verlaufOffset=0 p_txtr_SumDiv_lattice="Normal"
  p_txtr_SumDiv_scale=1 p_txtr_scaleSumDiv=1 p_txtr_SumDiv_col="Sum"
  p_txtr_SumDiv_mode="Sum" p_txtr_SumDiv_limit=0 p_txtr_MLAB=0
  p_f_MLAB_verlaufMode="None" p_f_MLAB_verlaufOffset=0
  p_txtr_MLAB_lattice="Normal" p_txtr_MLAB_scale=1 p_txtr_MLAB_size=1
  p_txtr_MLAB_limit=0 p_txtr_MLAB_scalo=1 p_txtr_MLAB_divi=4
  p_txtr_MLAB_edge=0.8 p_txtr_MLAB_pro0=0.25/0.5 p_txtr_MLAB_pro1=0.75/1
  p_txtr_MLAB_vari=1024 p_txtr_Banana=0 p_txtr_Banana_type="Original"
  p_f_Banana_verlaufMode="None" p_f_Banana_verlaufOffset=0
  p_txtr_Banana_lattice="Normal" p_txtr_Banana_scale=1 p_txtr_Banana_size=1
  p_txtr_Banana_limit=0 p_txtr_Banana_scalo=1 p_txtr_Banana_divi=4
  p_txtr_Banana_ratio=0.5/0.5 p_txtr_Banana_edge=0.8
  p_txtr_Banana_itre="Continuous" p_txtr_Banana_otre="Continuous"
  p_txtr_Banana_pro0=0.25/0.5 p_txtr_Banana_pro1=0.75/1
  p_txtr_Banana_vari=1024 p_txtr_Banana_seed0=3779 p_txtr_Banana_seed1=9377
  p_txtr_Ell=0 p_txtr_Ell_type="Magn Diff" p_f_Ell_verlaufMode="None"
  p_f_Ell_verlaufOffset=0 p_txtr_Ell_lattice="Normal" p_txtr_Ell_scale=5
  p_txtr_Ell_size=1 p_txtr_Ell_a=-1 p_txtr_Ell_b=-1 p_txtr_Ell_c=1
  p_txtr_Ell_d=0 p_txtr_Ell_pseudo=yes p_txtr_Ell_pseudoMix=no
  p_txtr_Ell_mixMode="Normal" p_txtr_Ell_limit=0 p_txtr_MedialCut=0
  p_f_MedialCut_verlaufMode="None" p_f_MedialCut_verlaufOffset=0
  p_txtr_MedialCut_lattice="Normal" p_txtr_MedialCut_type="Real"
  p_txtr_MedialCut_watch="Diff" p_txtr_MedialCut_scale=1
  p_txtr_MedialCut_size=1 p_txtr_MedialCut_calcScale=1
  p_txtr_MedialCut_smooth=0.1 p_txtr_MedialCut_limit=0 p_masking="None"
  p_maskType="Index" p_threshold_l=0.1 p_threshold_u=0.452 f_startFct=ident
  f_fkt=ident f_barnFct1=flip f_barnFct2=flip
gradient:
  smooth=yes position=103 numnodes=3 index=86 color=10927304 index=201
  color=42 index=360 color=42
layer:
  outsolid=14606046 outalpha=0 method=multipass caption="New Layer 3"
  opacity=35 visible=yes alpha=yes mergemode=hsladd
mapping:
  center=-0.287881828498840332/0.592228307628631592 magn=1424.6273242601272
  angle=0
formula:
  filename="Standard.ufm" entry="FastJulia" maxiter=250 percheck=off
  p_Seed=0.55/-0.21875 p_Bailout=4
inside:
  transfer=none repeat=yes
outside:
  filename="akl-t-math.ucl" entry="akl-MedialSmooth" transfer=log
  repeat=yes p_calculate="Angel" p_smooth=0 p_watch="Astro23"
  p_fixit="Minimum" p_disturbFixFactor=0.1 p_disturbMode="Log"
  p_colorby="Iterations" p_numIterMode="Normal" p_trapMode="None"
  p_lowerTrap=1 p_upperTrap=2 p_skipMode="None" p_skipConst=3
  p_startDistortion="#z" p_minMax=no p_xWaveMode="None" p_yWaveMode="None"
  p_xWaveFreq=1 p_yWaveFreq=1 p_xWaveWeight=1 p_yWaveWeight=1
  p_xWaveConst=0 p_yWaveConst=0 p_xWaveOffset=0 p_yWaveOffset=0
  p_xWaveExp=1 p_yWaveEyp=1 p_wavesLoop=1 p_wavesLoopMode="Static"
  p_wavesGrowFreq=1 p_rotDegree=0 p_rotCentre=0/0 p_zJouk=0/0
  p_vectorJouk=0/0 p_curveJouk=0/0 p_coord="Rectangular" p_coordLoop=1
  p_coordMode="Static" p_lattice="None" p_lattFac1=1/0 p_lattFac2=1/0
  p_lattOffset=0/0 p_colour_limit=0 p_init_z="Always New" p_globalScale=0
  p_globalDither=0 p_shape="None" p_radius=0.5 p_inner_scale=3
  p_inner_amount=0 p_d_randomness=0 p_turnMode=no p_turnScale=1
  p_turnScaleMode="Round" p_corte1=4 p_corte2=2 p_barnMode="None"
  p_barnScale=0 p_barnScaleMode="Round" p_barnSeed=0.6/1.1 p_barnShift=1
  p_disturb_fbm=0 p_disturb_fbm_mode="Sum only" p_disturb_fbm_apply="Pixel"
  p_disturb_fbm_scale=1 p_disturb_fbm_octaves=9 p_disturb_fbm_lattice=no
  p_l_randomness=0 p_txtr_verlauf_Line1=0/0 p_txtr_verlauf_Line2=1/1
  p_txtr_verlauf_exponent=1.5 p_txtr_verlauf_Rot=0
  p_txtr_verlauf_RotCentre=0/0 p_f_randomness=0 p_f_rand_verlaufMode="None"
  p_base4txtr="Z" p_reachThrough=no p_txtr_gnarl=0
  p_f_Gnarl_verlaufMode="None" p_f_Gnarl_verlaufOffset=0
  p_txtr_gnarl_lattice="Normal" p_txtr_gnarl_type="x" p_txtr_gnarl_scale=1
  p_txtr_gnarl_size=1 p_txtr_gnarl_octaves=5 p_txtr_gnarl_limit=0
  p_txtr_PopCorn=0 p_f_PopCorn_verlaufMode="None"
  p_f_PopCorn_verlaufOffset=0 p_txtr_PopCorn_lattice="Normal"
  p_txtr_PopCorn_type="x" p_txtr_PopCorn_scale=1 p_txtr_PopCorn_size=1
  p_txtr_PopCorn_limit=0 p_txtr_PopCorn_octaves=5 p_txtr_SFBM=0
  p_f_SFBM_verlaufMode="None" p_f_SFBM_verlaufOffset=0
  p_txtr_SFBM_lattice="Normal" p_txtr_SFBM_mode="Raw... (Sam's)"
  p_txtr_SFBM_scale=1 p_txtr_SFBM_scaledis="1/scale" p_txtr_SFBM_size=0.1
  p_txtr_SFBM_magn=1.2 p_txtr_SFBM_limit=0 p_txtr_SFBM_rot=28
  p_txtr_SFBM_power=1 p_txtr_SFBM_mod="Use sqrt(i)" p_txtr_SFBM_seed=123094
  p_txtr_SFBM_octaves=5 p_txtr_Primes=0 p_f_Primes_verlaufMode="None"
  p_f_Primes_verlaufOffset=0 p_txtr_Primes_lattice="Normal"
  p_txtr_Primes_scale=1 p_txtr_Primes_size=0.5
  p_txtr_primes_withFinalTrunc=yes p_txtr_primes_where2start=1
  p_txtr_primes_lengthOfSnip=1 p_txtr_primes_Mode="Angel"
  p_txtr_primes_limit=0 p_txtr_Gauss=0 p_f_Gauss_verlaufMode="None"
  p_f_Gauss_verlaufOffset=0 p_txtr_Gauss_lattice="Normal"
  p_txtr_Gauss_type="d" p_txtr_Gauss_scale=1 p_txtr_Gauss_size=1
  p_txtr_Gauss_limit=0 p_txtr_Turn=0 p_f_Turn_verlaufMode="None"
  p_f_Turn_verlaufOffset=0 p_txtr_Turn_lattice="Normal" p_txtr_Turn_scale=1
  p_txtr_Turn_size=1 p_txtr_Turn_limit=0 p_txtr_Turn_corte1=4
  p_txtr_Turn_corte2=2 p_txtr_Check=0 p_f_Check_verlaufMode="None"
  p_f_Check_verlaufOffset=0 p_txtr_Check_scale=1 p_txtr_Checker=2
  p_txtr_Check_test="Prod" p_txtr_Check_shape="Square"
  p_txtr_Check_shConst=1 p_txtr_Check_col="Flag" p_txtr_Check_invert=no
  p_txtr_Check_divide="None" p_txtr_Check_limit=0 p_txtr_Pick153=0
  p_f_Pick153_verlaufMode="None" p_f_Pick153_verlaufOffset=0
  p_txtr_Pick153_lattice="Normal" p_txtr_Pick153_scale=1 p_txtr_scale153=1
  p_txtr_numOfTestsPick153=1 p_txtr_Pick153_col="Sum"
  p_txtr_Pick153_limit=0 p_txtr_SumDiv=0 p_f_SumDiv_verlaufMode="None"
  p_f_SumDiv_verlaufOffset=0 p_txtr_SumDiv_lattice="Normal"
  p_txtr_SumDiv_scale=1 p_txtr_scaleSumDiv=1 p_txtr_SumDiv_col="Sum"
  p_txtr_SumDiv_mode="Sum" p_txtr_SumDiv_limit=0 p_txtr_MLAB=0
  p_f_MLAB_verlaufMode="None" p_f_MLAB_verlaufOffset=0
  p_txtr_MLAB_lattice="Normal" p_txtr_MLAB_scale=1 p_txtr_MLAB_size=1
  p_txtr_MLAB_limit=0 p_txtr_MLAB_scalo=1 p_txtr_MLAB_divi=4
  p_txtr_MLAB_edge=0.8 p_txtr_MLAB_pro0=0.25/0.5 p_txtr_MLAB_pro1=0.75/1
  p_txtr_MLAB_vari=1024 p_txtr_Banana=2 p_txtr_Banana_type="Ori/Polyominos"
  p_f_Banana_verlaufMode="None" p_f_Banana_verlaufOffset=0
  p_txtr_Banana_lattice="Normal" p_txtr_Banana_scale=5 p_txtr_Banana_size=1
  p_txtr_Banana_limit=0 p_txtr_Banana_scalo=1 p_txtr_Banana_divi=4
  p_txtr_Banana_ratio=0.5/0.5 p_txtr_Banana_edge=0.8
  p_txtr_Banana_itre="Continuous" p_txtr_Banana_otre="Continuous"
  p_txtr_Banana_pro0=0.25/0.5 p_txtr_Banana_pro1=0.75/1
  p_txtr_Banana_vari=1024 p_txtr_Banana_seed0=3779 p_txtr_Banana_seed1=9377
  p_txtr_Ell=0 p_txtr_Ell_type="Magn Diff" p_f_Ell_verlaufMode="None"
  p_f_Ell_verlaufOffset=0 p_txtr_Ell_lattice="Normal" p_txtr_Ell_scale=1
  p_txtr_Ell_size=1 p_txtr_Ell_a=-1 p_txtr_Ell_b=-1 p_txtr_Ell_c=1
  p_txtr_Ell_d=0 p_txtr_Ell_pseudo=yes p_txtr_Ell_pseudoMix=no
  p_txtr_Ell_mixMode="Normal" p_txtr_Ell_limit=0 p_txtr_MedialCut=0
  p_f_MedialCut_verlaufMode="None" p_f_MedialCut_verlaufOffset=0
  p_txtr_MedialCut_lattice="Normal" p_txtr_MedialCut_type="Real"
  p_txtr_MedialCut_watch="Diff" p_txtr_MedialCut_scale=1
  p_txtr_MedialCut_size=1 p_txtr_MedialCut_calcScale=1
  p_txtr_MedialCut_smooth=0.1 p_txtr_MedialCut_limit=0 p_masking="Lower"
  p_maskType="Index" p_threshold_l=11 p_threshold_u=1 f_startFct=ident
  f_fkt=ident f_barnFct1=flip f_barnFct2=flip
gradient:
  smooth=no position=47 numnodes=20 index=0 color=269976 index=1 color=0
  index=2 color=271003 index=43 color=301274 index=63 color=1097709
  index=82 color=2212852 index=101 color=3516144 index=135 color=6243023
  index=157 color=7868077 index=174 color=8978573 index=193 color=9769065
  index=220 color=10310714 index=249 color=9807890 index=267 color=9093637
  index=284 color=8044800 index=302 color=6660101 index=335 color=4014118
  index=357 color=2362696 index=376 color=1179755 index=393 color=463500
layer:
  method=multipass caption="New Layer 1" opacity=100 visible=yes alpha=no
  mergemode=color
mapping:
  center=-0.287881828498840332/0.592228307628631592 magn=1424.6273242601272
  angle=0
formula:
  filename="Standard.ufm" entry="FastJulia" maxiter=250 percheck=off
  p_Seed=0.55/-0.21875 p_Bailout=4
inside:
  transfer=none repeat=yes
outside:
  filename="akl-t-math.ucl" entry="akl-MedialSmooth" transfer=log
  repeat=yes p_calculate="Angel" p_smooth=0 p_watch="Astro23"
  p_fixit="Minimum" p_disturbFixFactor=0.1 p_disturbMode="Log"
  p_colorby="Iterations" p_numIterMode="Normal" p_trapMode="None"
  p_lowerTrap=1 p_upperTrap=2 p_skipMode="None" p_skipConst=3
  p_startDistortion="#z" p_minMax=no p_xWaveMode="None" p_yWaveMode="None"
  p_xWaveFreq=1 p_yWaveFreq=1 p_xWaveWeight=1 p_yWaveWeight=1
  p_xWaveConst=0 p_yWaveConst=0 p_xWaveOffset=0 p_yWaveOffset=0
  p_xWaveExp=1 p_yWaveEyp=1 p_wavesLoop=1 p_wavesLoopMode="Static"
  p_wavesGrowFreq=1 p_rotDegree=0 p_rotCentre=0/0 p_zJouk=0/0
  p_vectorJouk=0/0 p_curveJouk=0/0 p_coord="Rectangular" p_coordLoop=1
  p_coordMode="Static" p_lattice="None" p_lattFac1=1/0 p_lattFac2=1/0
  p_lattOffset=0/0 p_colour_limit=0 p_init_z="Always New" p_globalScale=0
  p_globalDither=0 p_shape="None" p_radius=0.5 p_inner_scale=3
  p_inner_amount=0 p_d_randomness=0 p_turnMode=no p_turnScale=1
  p_turnScaleMode="Round" p_corte1=4 p_corte2=2 p_barnMode="None"
  p_barnScale=0 p_barnScaleMode="Round" p_barnSeed=0.6/1.1 p_barnShift=1
  p_disturb_fbm=0 p_disturb_fbm_mode="fBm Pix*Angle"
  p_disturb_fbm_apply="Pixel" p_disturb_fbm_scale=100
  p_disturb_fbm_octaves=9 p_disturb_fbm_lattice=no p_l_randomness=0
  p_txtr_verlauf_Line1=-0.289517924499511719/0.591151650905609131
  p_txtr_verlauf_Line2=-0.286483230304718018/0.593294408893585205
  p_txtr_verlauf_exponent=1.5 p_txtr_verlauf_Rot=0
  p_txtr_verlauf_RotCentre=0/0 p_f_randomness=0 p_f_rand_verlaufMode="None"
  p_base4txtr="Z" p_reachThrough=no p_txtr_gnarl=0
  p_f_Gnarl_verlaufMode="None" p_f_Gnarl_verlaufOffset=0
  p_txtr_gnarl_lattice="Normal" p_txtr_gnarl_type="x" p_txtr_gnarl_scale=1
  p_txtr_gnarl_size=1 p_txtr_gnarl_octaves=5 p_txtr_gnarl_limit=0
  p_txtr_PopCorn=0 p_f_PopCorn_verlaufMode="None"
  p_f_PopCorn_verlaufOffset=0 p_txtr_PopCorn_lattice="Normal"
  p_txtr_PopCorn_type="x" p_txtr_PopCorn_scale=1 p_txtr_PopCorn_size=1
  p_txtr_PopCorn_limit=0 p_txtr_PopCorn_octaves=5 p_txtr_SFBM=1
  p_f_SFBM_verlaufMode="Bottom to Top" p_f_SFBM_verlaufOffset=0
  p_txtr_SFBM_lattice="None" p_txtr_SFBM_mode="Raw... (Sam's)"
  p_txtr_SFBM_scale=0.1 p_txtr_SFBM_scaledis="1/scale" p_txtr_SFBM_size=0.1
  p_txtr_SFBM_magn=1.2 p_txtr_SFBM_limit=0 p_txtr_SFBM_rot=28
  p_txtr_SFBM_power=1 p_txtr_SFBM_mod="Use sqrt(i)" p_txtr_SFBM_seed=123094
  p_txtr_SFBM_octaves=5 p_txtr_Primes=0 p_f_Primes_verlaufMode="None"
  p_f_Primes_verlaufOffset=0 p_txtr_Primes_lattice="Normal"
  p_txtr_Primes_scale=1 p_txtr_Primes_size=0.5
  p_txtr_primes_withFinalTrunc=yes p_txtr_primes_where2start=1
  p_txtr_primes_lengthOfSnip=1 p_txtr_primes_Mode="Angel"
  p_txtr_primes_limit=0 p_txtr_Gauss=0 p_f_Gauss_verlaufMode="None"
  p_f_Gauss_verlaufOffset=0 p_txtr_Gauss_lattice="Normal"
  p_txtr_Gauss_type="d" p_txtr_Gauss_scale=1 p_txtr_Gauss_size=1
  p_txtr_Gauss_limit=0 p_txtr_Turn=0 p_f_Turn_verlaufMode="None"
  p_f_Turn_verlaufOffset=0 p_txtr_Turn_lattice="Normal" p_txtr_Turn_scale=1
  p_txtr_Turn_size=1 p_txtr_Turn_limit=0 p_txtr_Turn_corte1=4
  p_txtr_Turn_corte2=2 p_txtr_Check=0 p_f_Check_verlaufMode="None"
  p_f_Check_verlaufOffset=0 p_txtr_Check_scale=1 p_txtr_Checker=2
  p_txtr_Check_test="Prod" p_txtr_Check_shape="Square"
  p_txtr_Check_shConst=1 p_txtr_Check_col="Flag" p_txtr_Check_invert=no
  p_txtr_Check_divide="None" p_txtr_Check_limit=0 p_txtr_Pick153=0
  p_f_Pick153_verlaufMode="None" p_f_Pick153_verlaufOffset=0
  p_txtr_Pick153_lattice="Normal" p_txtr_Pick153_scale=1 p_txtr_scale153=1
  p_txtr_numOfTestsPick153=1 p_txtr_Pick153_col="Sum"
  p_txtr_Pick153_limit=0 p_txtr_SumDiv=0 p_f_SumDiv_verlaufMode="None"
  p_f_SumDiv_verlaufOffset=0 p_txtr_SumDiv_lattice="Normal"
  p_txtr_SumDiv_scale=1 p_txtr_scaleSumDiv=1 p_txtr_SumDiv_col="Sum"
  p_txtr_SumDiv_mode="Sum" p_txtr_SumDiv_limit=0 p_txtr_MLAB=0
  p_f_MLAB_verlaufMode="None" p_f_MLAB_verlaufOffset=0
  p_txtr_MLAB_lattice="Normal" p_txtr_MLAB_scale=1 p_txtr_MLAB_size=1
  p_txtr_MLAB_limit=0 p_txtr_MLAB_scalo=1 p_txtr_MLAB_divi=4
  p_txtr_MLAB_edge=0.8 p_txtr_MLAB_pro0=0.25/0.5 p_txtr_MLAB_pro1=0.75/1
  p_txtr_MLAB_vari=1024 p_txtr_Banana=0 p_txtr_Banana_type="Original"
  p_f_Banana_verlaufMode="None" p_f_Banana_verlaufOffset=0
  p_txtr_Banana_lattice="Normal" p_txtr_Banana_scale=1 p_txtr_Banana_size=1
  p_txtr_Banana_limit=0 p_txtr_Banana_scalo=1 p_txtr_Banana_divi=4
  p_txtr_Banana_ratio=0.5/0.5 p_txtr_Banana_edge=0.8
  p_txtr_Banana_itre="Continuous" p_txtr_Banana_otre="Continuous"
  p_txtr_Banana_pro0=0.25/0.5 p_txtr_Banana_pro1=0.75/1
  p_txtr_Banana_vari=1024 p_txtr_Banana_seed0=3779 p_txtr_Banana_seed1=9377
  p_txtr_Ell=0 p_txtr_Ell_type="Magn Diff" p_f_Ell_verlaufMode="None"
  p_f_Ell_verlaufOffset=0 p_txtr_Ell_lattice="Normal" p_txtr_Ell_scale=1
  p_txtr_Ell_size=1 p_txtr_Ell_a=-1 p_txtr_Ell_b=-1 p_txtr_Ell_c=1
  p_txtr_Ell_d=0 p_txtr_Ell_pseudo=yes p_txtr_Ell_pseudoMix=no
  p_txtr_Ell_mixMode="Normal" p_txtr_Ell_limit=0 p_txtr_MedialCut=0.1
  p_f_MedialCut_verlaufMode="Top to Bottom" p_f_MedialCut_verlaufOffset=0
  p_txtr_MedialCut_lattice="Normal" p_txtr_MedialCut_type="Real"
  p_txtr_MedialCut_watch="Diff" p_txtr_MedialCut_scale=0.1
  p_txtr_MedialCut_size=1 p_txtr_MedialCut_calcScale=1
  p_txtr_MedialCut_smooth=0.1 p_txtr_MedialCut_limit=10 p_masking="None"
  p_maskType="Index" p_threshold_l=0.5 p_threshold_u=1 f_startFct=ident
  f_fkt=ident f_barnFct1=flip f_barnFct2=flip
gradient:
  smooth=no position=-163 numnodes=20 index=0 color=269976 index=1 color=0
  index=2 color=271003 index=43 color=301274 index=63 color=1097709
  index=82 color=2212852 index=101 color=3516144 index=135 color=6243023
  index=157 color=7868077 index=174 color=8978573 index=193 color=9769065
  index=220 color=10310714 index=249 color=9807890 index=267 color=9093637
  index=284 color=8044800 index=302 color=6660101 index=335 color=4014118
  index=357 color=2362696 index=376 color=1179755 index=393 color=463500
layer:
  method=multipass caption="Layer 1" opacity=80 visible=yes alpha=no
  mergemode=hsladd
mapping:
  center=-0.287881828498840332/0.592228307628631592 magn=1424.6273242601272
  angle=0
formula:
  filename="Standard.ufm" entry="FastJulia" maxiter=250 percheck=off
  p_Seed=0.55/-0.21875 p_Bailout=4
inside:
  transfer=none repeat=yes
outside:
  filename="akl-t-math.ucl" entry="akl-MedialSmooth" transfer=cuberoot
  repeat=yes p_calculate="Real" p_smooth=0 p_watch="Diff2"
  p_fixit="Minimum" p_disturbFixFactor=0 p_disturbMode="Log"
  p_colorby="Fiximum Distance" p_numIterMode="Normal" p_trapMode="None"
  p_lowerTrap=1 p_upperTrap=2 p_skipMode="None" p_skipConst=3
  p_startDistortion="#z" p_minMax=no p_xWaveMode="None" p_yWaveMode="None"
  p_xWaveFreq=1 p_yWaveFreq=1 p_xWaveWeight=1 p_yWaveWeight=1
  p_xWaveConst=0 p_yWaveConst=0 p_xWaveOffset=0 p_yWaveOffset=0
  p_xWaveExp=1 p_yWaveEyp=1 p_wavesLoop=1 p_wavesLoopMode="Static"
  p_wavesGrowFreq=1 p_rotDegree=0 p_rotCentre=0/0 p_zJouk=0/0
  p_vectorJouk=0/0 p_curveJouk=0/0 p_coord="Rectangular" p_coordLoop=1
  p_coordMode="Static" p_lattice="None" p_lattFac1=1/0 p_lattFac2=1/0
  p_lattOffset=0/0 p_colour_limit=0 p_init_z="Always New" p_globalScale=0
  p_globalDither=0 p_shape="None" p_radius=0.5 p_inner_scale=3
  p_inner_amount=0 p_d_randomness=0 p_turnMode=no p_turnScale=1
  p_turnScaleMode="Round" p_corte1=4 p_corte2=2 p_barnMode="None"
  p_barnScale=0 p_barnScaleMode="Round" p_barnSeed=0.6/1.1 p_barnShift=1
  p_disturb_fbm=0.1 p_disturb_fbm_mode="fBm Pix*Angle"
  p_disturb_fbm_apply="Pixel" p_disturb_fbm_scale=100
  p_disturb_fbm_octaves=9 p_disturb_fbm_lattice=no p_l_randomness=0
  p_txtr_verlauf_Line1=0/0 p_txtr_verlauf_Line2=1/1
  p_txtr_verlauf_exponent=1.5 p_txtr_verlauf_Rot=0
  p_txtr_verlauf_RotCentre=0/0 p_f_randomness=0 p_f_rand_verlaufMode="None"
  p_base4txtr="Z" p_reachThrough=no p_txtr_gnarl=0
  p_f_Gnarl_verlaufMode="None" p_f_Gnarl_verlaufOffset=0
  p_txtr_gnarl_lattice="Normal" p_txtr_gnarl_type="x" p_txtr_gnarl_scale=1
  p_txtr_gnarl_size=1 p_txtr_gnarl_octaves=5 p_txtr_gnarl_limit=0
  p_txtr_PopCorn=0 p_f_PopCorn_verlaufMode="None"
  p_f_PopCorn_verlaufOffset=0 p_txtr_PopCorn_lattice="Normal"
  p_txtr_PopCorn_type="x" p_txtr_PopCorn_scale=1 p_txtr_PopCorn_size=1
  p_txtr_PopCorn_limit=0 p_txtr_PopCorn_octaves=5 p_txtr_SFBM=0
  p_f_SFBM_verlaufMode="None" p_f_SFBM_verlaufOffset=0
  p_txtr_SFBM_lattice="Normal" p_txtr_SFBM_mode="Raw... (Sam's)"
  p_txtr_SFBM_scale=1 p_txtr_SFBM_scaledis="1/scale" p_txtr_SFBM_size=0.1
  p_txtr_SFBM_magn=1.2 p_txtr_SFBM_limit=0 p_txtr_SFBM_rot=28
  p_txtr_SFBM_power=1 p_txtr_SFBM_mod="Use sqrt(i)" p_txtr_SFBM_seed=123094
  p_txtr_SFBM_octaves=5 p_txtr_Primes=0 p_f_Primes_verlaufMode="None"
  p_f_Primes_verlaufOffset=0 p_txtr_Primes_lattice="Normal"
  p_txtr_Primes_scale=1 p_txtr_Primes_size=0.5
  p_txtr_primes_withFinalTrunc=yes p_txtr_primes_where2start=1
  p_txtr_primes_lengthOfSnip=1 p_txtr_primes_Mode="Angel"
  p_txtr_primes_limit=0 p_txtr_Gauss=0 p_f_Gauss_verlaufMode="None"
  p_f_Gauss_verlaufOffset=0 p_txtr_Gauss_lattice="Normal"
  p_txtr_Gauss_type="d" p_txtr_Gauss_scale=1 p_txtr_Gauss_size=1
  p_txtr_Gauss_limit=0 p_txtr_Turn=0 p_f_Turn_verlaufMode="None"
  p_f_Turn_verlaufOffset=0 p_txtr_Turn_lattice="Normal" p_txtr_Turn_scale=1
  p_txtr_Turn_size=1 p_txtr_Turn_limit=0 p_txtr_Turn_corte1=4
  p_txtr_Turn_corte2=2 p_txtr_Check=0 p_f_Check_verlaufMode="None"
  p_f_Check_verlaufOffset=0 p_txtr_Check_scale=1 p_txtr_Checker=2
  p_txtr_Check_test="Prod" p_txtr_Check_shape="Square"
  p_txtr_Check_shConst=1 p_txtr_Check_col="Flag" p_txtr_Check_invert=no
  p_txtr_Check_divide="None" p_txtr_Check_limit=0 p_txtr_Pick153=0
  p_f_Pick153_verlaufMode="None" p_f_Pick153_verlaufOffset=0
  p_txtr_Pick153_lattice="Normal" p_txtr_Pick153_scale=1 p_txtr_scale153=1
  p_txtr_numOfTestsPick153=1 p_txtr_Pick153_col="Sum"
  p_txtr_Pick153_limit=0 p_txtr_SumDiv=0 p_f_SumDiv_verlaufMode="None"
  p_f_SumDiv_verlaufOffset=0 p_txtr_SumDiv_lattice="Normal"
  p_txtr_SumDiv_scale=1 p_txtr_scaleSumDiv=1 p_txtr_SumDiv_col="Sum"
  p_txtr_SumDiv_mode="Sum" p_txtr_SumDiv_limit=0 p_txtr_MLAB=0
  p_f_MLAB_verlaufMode="None" p_f_MLAB_verlaufOffset=0
  p_txtr_MLAB_lattice="Normal" p_txtr_MLAB_scale=1 p_txtr_MLAB_size=1
  p_txtr_MLAB_limit=0 p_txtr_MLAB_scalo=1 p_txtr_MLAB_divi=4
  p_txtr_MLAB_edge=0.8 p_txtr_MLAB_pro0=0.25/0.5 p_txtr_MLAB_pro1=0.75/1
  p_txtr_MLAB_vari=1024 p_txtr_Banana=0 p_txtr_Banana_type="Original"
  p_f_Banana_verlaufMode="None" p_f_Banana_verlaufOffset=0
  p_txtr_Banana_lattice="Normal" p_txtr_Banana_scale=1 p_txtr_Banana_size=1
  p_txtr_Banana_limit=0 p_txtr_Banana_scalo=1 p_txtr_Banana_divi=4
  p_txtr_Banana_ratio=0.5/0.5 p_txtr_Banana_edge=0.8
  p_txtr_Banana_itre="Continuous" p_txtr_Banana_otre="Continuous"
  p_txtr_Banana_pro0=0.25/0.5 p_txtr_Banana_pro1=0.75/1
  p_txtr_Banana_vari=1024 p_txtr_Banana_seed0=3779 p_txtr_Banana_seed1=9377
  p_txtr_Ell=0 p_txtr_Ell_type="Magn Diff" p_f_Ell_verlaufMode="None"
  p_f_Ell_verlaufOffset=0 p_txtr_Ell_lattice="Normal" p_txtr_Ell_scale=1
  p_txtr_Ell_size=1 p_txtr_Ell_a=-1 p_txtr_Ell_b=-1 p_txtr_Ell_c=1
  p_txtr_Ell_d=0 p_txtr_Ell_pseudo=yes p_txtr_Ell_pseudoMix=no
  p_txtr_Ell_mixMode="Normal" p_txtr_Ell_limit=0 p_txtr_MedialCut=0
  p_f_MedialCut_verlaufMode="None" p_f_MedialCut_verlaufOffset=0
  p_txtr_MedialCut_lattice="Normal" p_txtr_MedialCut_type="Real"
  p_txtr_MedialCut_watch="Diff" p_txtr_MedialCut_scale=1
  p_txtr_MedialCut_size=1 p_txtr_MedialCut_calcScale=1
  p_txtr_MedialCut_smooth=0.1 p_txtr_MedialCut_limit=0 p_masking="None"
  p_maskType="Index" p_threshold_l=0.5 p_threshold_u=1 f_startFct=ident
  f_fkt=ident f_barnFct1=flip f_barnFct2=flip
gradient:
  smooth=no position=-128 numnodes=20 index=7 color=301274 index=27
  color=1097709 index=46 color=2212852 index=65 color=3516144 index=99
  color=6243023 index=121 color=7868077 index=138 color=8978573 index=157
  color=9769065 index=184 color=10310714 index=213 color=9807890 index=231
  color=9093637 index=248 color=8044800 index=266 color=6660101 index=299
  color=4014118 index=321 color=2362696 index=340 color=1179755 index=357
  color=463500 index=364 color=269976 index=365 color=0 index=366
  color=271003
layer:
  method=multipass caption="New Layer 4" opacity=100 visible=yes alpha=no
  mergemode=difference
mapping:
  center=-0.287881828498840332/0.592228307628631592 magn=1424.6273242601272
  angle=0
formula:
  filename="Standard.ufm" entry="FastJulia" maxiter=250 percheck=off
  p_Seed=0.55/-0.21875 p_Bailout=4
inside:
  transfer=none repeat=yes
outside:
  filename="akl-t-math.ucl" entry="akl-MedialSmooth" transfer=log
  repeat=yes p_calculate="Angel" p_smooth=0 p_watch="Astro23"
  p_fixit="Minimum" p_disturbFixFactor=0.1 p_disturbMode="Log"
  p_colorby="Fiximum Distance" p_numIterMode="Normal" p_trapMode="None"
  p_lowerTrap=1 p_upperTrap=2 p_skipMode="None" p_skipConst=3
  p_startDistortion="#z" p_minMax=no p_xWaveMode="None" p_yWaveMode="None"
  p_xWaveFreq=1 p_yWaveFreq=1 p_xWaveWeight=1 p_yWaveWeight=1
  p_xWaveConst=0 p_yWaveConst=0 p_xWaveOffset=0 p_yWaveOffset=0
  p_xWaveExp=1 p_yWaveEyp=1 p_wavesLoop=1 p_wavesLoopMode="Static"
  p_wavesGrowFreq=1 p_rotDegree=0 p_rotCentre=0/0 p_zJouk=0/0
  p_vectorJouk=0/0 p_curveJouk=0/0 p_coord="Rectangular" p_coordLoop=1
  p_coordMode="Static" p_lattice="None" p_lattFac1=1/0 p_lattFac2=1/0
  p_lattOffset=0/0 p_colour_limit=0 p_init_z="Always New" p_globalScale=0
  p_globalDither=0 p_shape="None" p_radius=0.5 p_inner_scale=3
  p_inner_amount=0 p_d_randomness=0 p_turnMode=yes p_turnScale=50
  p_turnScaleMode="Round" p_corte1=4 p_corte2=2 p_barnMode="None"
  p_barnScale=0 p_barnScaleMode="Round" p_barnSeed=0.6/1.1 p_barnShift=1
  p_disturb_fbm=0 p_disturb_fbm_mode="Sum only" p_disturb_fbm_apply="Pixel"
  p_disturb_fbm_scale=1 p_disturb_fbm_octaves=9 p_disturb_fbm_lattice=no
  p_l_randomness=0 p_txtr_verlauf_Line1=0/0 p_txtr_verlauf_Line2=1/1
  p_txtr_verlauf_exponent=1.5 p_txtr_verlauf_Rot=0
  p_txtr_verlauf_RotCentre=0/0 p_f_randomness=0.05
  p_f_rand_verlaufMode="None" p_base4txtr="Z" p_reachThrough=no
  p_txtr_gnarl=0 p_f_Gnarl_verlaufMode="None" p_f_Gnarl_verlaufOffset=0
  p_txtr_gnarl_lattice="Normal" p_txtr_gnarl_type="x" p_txtr_gnarl_scale=1
  p_txtr_gnarl_size=1 p_txtr_gnarl_octaves=5 p_txtr_gnarl_limit=0
  p_txtr_PopCorn=0 p_f_PopCorn_verlaufMode="None"
  p_f_PopCorn_verlaufOffset=0 p_txtr_PopCorn_lattice="Normal"
  p_txtr_PopCorn_type="x" p_txtr_PopCorn_scale=1 p_txtr_PopCorn_size=1
  p_txtr_PopCorn_limit=0 p_txtr_PopCorn_octaves=5 p_txtr_SFBM=0
  p_f_SFBM_verlaufMode="None" p_f_SFBM_verlaufOffset=0
  p_txtr_SFBM_lattice="Normal" p_txtr_SFBM_mode="Raw... (Sam's)"
  p_txtr_SFBM_scale=1 p_txtr_SFBM_scaledis="1/scale" p_txtr_SFBM_size=0.1
  p_txtr_SFBM_magn=1.2 p_txtr_SFBM_limit=0 p_txtr_SFBM_rot=28
  p_txtr_SFBM_power=1 p_txtr_SFBM_mod="Use sqrt(i)" p_txtr_SFBM_seed=123094
  p_txtr_SFBM_octaves=5 p_txtr_Primes=0 p_f_Primes_verlaufMode="None"
  p_f_Primes_verlaufOffset=0 p_txtr_Primes_lattice="Normal"
  p_txtr_Primes_scale=1 p_txtr_Primes_size=0.5
  p_txtr_primes_withFinalTrunc=yes p_txtr_primes_where2start=1
  p_txtr_primes_lengthOfSnip=1 p_txtr_primes_Mode="Angel"
  p_txtr_primes_limit=0 p_txtr_Gauss=0 p_f_Gauss_verlaufMode="None"
  p_f_Gauss_verlaufOffset=0 p_txtr_Gauss_lattice="Normal"
  p_txtr_Gauss_type="d" p_txtr_Gauss_scale=1 p_txtr_Gauss_size=1
  p_txtr_Gauss_limit=0 p_txtr_Turn=0 p_f_Turn_verlaufMode="None"
  p_f_Turn_verlaufOffset=0 p_txtr_Turn_lattice="Normal" p_txtr_Turn_scale=1
  p_txtr_Turn_size=1 p_txtr_Turn_limit=0 p_txtr_Turn_corte1=4
  p_txtr_Turn_corte2=2 p_txtr_Check=0 p_f_Check_verlaufMode="None"
  p_f_Check_verlaufOffset=0 p_txtr_Check_scale=1 p_txtr_Checker=2
  p_txtr_Check_test="Prod" p_txtr_Check_shape="Square"
  p_txtr_Check_shConst=1 p_txtr_Check_col="Flag" p_txtr_Check_invert=no
  p_txtr_Check_divide="None" p_txtr_Check_limit=0 p_txtr_Pick153=0
  p_f_Pick153_verlaufMode="None" p_f_Pick153_verlaufOffset=0
  p_txtr_Pick153_lattice="Normal" p_txtr_Pick153_scale=1 p_txtr_scale153=1
  p_txtr_numOfTestsPick153=1 p_txtr_Pick153_col="Sum"
  p_txtr_Pick153_limit=0 p_txtr_SumDiv=0 p_f_SumDiv_verlaufMode="None"
  p_f_SumDiv_verlaufOffset=0 p_txtr_SumDiv_lattice="Normal"
  p_txtr_SumDiv_scale=1 p_txtr_scaleSumDiv=1 p_txtr_SumDiv_col="Sum"
  p_txtr_SumDiv_mode="Sum" p_txtr_SumDiv_limit=0 p_txtr_MLAB=0
  p_f_MLAB_verlaufMode="None" p_f_MLAB_verlaufOffset=0
  p_txtr_MLAB_lattice="Normal" p_txtr_MLAB_scale=1 p_txtr_MLAB_size=1
  p_txtr_MLAB_limit=0 p_txtr_MLAB_scalo=1 p_txtr_MLAB_divi=4
  p_txtr_MLAB_edge=0.8 p_txtr_MLAB_pro0=0.25/0.5 p_txtr_MLAB_pro1=0.75/1
  p_txtr_MLAB_vari=1024 p_txtr_Banana=0 p_txtr_Banana_type="Original"
  p_f_Banana_verlaufMode="None" p_f_Banana_verlaufOffset=0
  p_txtr_Banana_lattice="Normal" p_txtr_Banana_scale=1 p_txtr_Banana_size=1
  p_txtr_Banana_limit=0 p_txtr_Banana_scalo=1 p_txtr_Banana_divi=4
  p_txtr_Banana_ratio=0.5/0.5 p_txtr_Banana_edge=0.8
  p_txtr_Banana_itre="Continuous" p_txtr_Banana_otre="Continuous"
  p_txtr_Banana_pro0=0.25/0.5 p_txtr_Banana_pro1=0.75/1
  p_txtr_Banana_vari=1024 p_txtr_Banana_seed0=3779 p_txtr_Banana_seed1=9377
  p_txtr_Ell=0 p_txtr_Ell_type="Magn Diff" p_f_Ell_verlaufMode="None"
  p_f_Ell_verlaufOffset=0 p_txtr_Ell_lattice="Normal" p_txtr_Ell_scale=5
  p_txtr_Ell_size=1 p_txtr_Ell_a=-1 p_txtr_Ell_b=-1 p_txtr_Ell_c=1
  p_txtr_Ell_d=0 p_txtr_Ell_pseudo=yes p_txtr_Ell_pseudoMix=no
  p_txtr_Ell_mixMode="Normal" p_txtr_Ell_limit=0 p_txtr_MedialCut=0
  p_f_MedialCut_verlaufMode="None" p_f_MedialCut_verlaufOffset=0
  p_txtr_MedialCut_lattice="Normal" p_txtr_MedialCut_type="Real"
  p_txtr_MedialCut_watch="Diff" p_txtr_MedialCut_scale=1
  p_txtr_MedialCut_size=1 p_txtr_MedialCut_calcScale=1
  p_txtr_MedialCut_smooth=0.1 p_txtr_MedialCut_limit=0 p_masking="None"
  p_maskType="Index" p_threshold_l=0.1 p_threshold_u=0.452 f_startFct=ident
  f_fkt=ident f_barnFct1=flip f_barnFct2=flip
gradient:
  smooth=yes position=100 numnodes=3 index=83 color=12372190 index=198
  color=42 index=357 color=42
}
''')

        self.assertIsValidParse(t1)

    def testIfStatement(self):
        t1 = self.parse(self.makeMinimalFormula("if x==1\nx=2\nendif"))
        self.assertIsValidParse(t1)

        t1 = self.parse(self.makeMinimalFormula('''
        if x==1
        x=2
        else
        x=3
        endif'''))
        self.assertIsValidParse(t1)

        t1 = self.parse(self.makeMinimalFormula('''
        if x==1
        x=2
        elseif (x==2) && (y==7)
        x=3
        y=5
        endif'''))
        self.assertIsValidParse(t1)

        t1 = self.parse(self.makeMinimalFormula('''
        if x == 2
        endif'''))
        self.assertIsValidParse(t1)

        t1 = self.parse(self.makeMinimalFormula('''
        if x == 2
        if y == 4
           z = 17
        elseif p != q
           w = 4
        else
           v=#pixel
        endif
        elseif 4 + 6
        else
        endif'''))
        # print t1.pretty()
        self.assertIsValidParse(t1)

        t1 = self.parse(self.makeMinimalFormula('''
        IF x==1
        x=2
        eLSe
        x=3
        Endif'''))
        self.assertIsValidParse(t1)

    def testBadIfStatements(self):
        self.assertIsBadFormula(self.makeMinimalFormula("if = 7"),
                                "unexpected assign '='", 3)
        self.assertIsBadFormula(self.makeMinimalFormula("if x == 2\n1+1"),
                                "unexpected form_end '}'", 5)
        self.assertIsBadFormula(self.makeMinimalFormula("endif"),
                                "unexpected endif 'endif'", 3)

    def testCtor(self):
        t1 = self.parse(self.makeMinimalFormula(
            '''bool a = bool(true)
        int i = int(2)
        float f = float(2.5)
        complex c = complex(1.0, 2.0)
        hyper h = hyper(1.0,2.0,3.0,4.0)
        hyper h2 = hyper((1.0,2.0),(3.0,4.0))
        color c = color(0.0,1.0,1.0,0.0)
        '''))
        self.assertIsValidParse(t1)

    def testDecls(self):
        t1 = self.parse(self.makeMinimalFormula(
            '''bool a
        bool b = true
        bool c=false
        int d
        int e= 2
        float f
        float g = 2.0
        complex h
        complex i = 3 + 1i + i
        complex j = (2,3)
        complex k = complex k2 = (2,7)
        hyper hh
        hyper hh2 = (1,2.3+7.9,3,4)
        color l'''))
        self.assertIsValidParse(t1)
        i = t1.children[0].children[0]
        for node in i.children:
            self.assertEqual(node.type, "decl")
        complex_decl = [n for n in i.children[8]]
        self.assertListTypesMatch(
            complex_decl,
            ["decl", "binop", "binop", "const", "binop", "const", "const", "id"])

    def testArrays(self):
        # arrays aren't supported yet - make sure errors are nice
        t1 = self.parse(self.makeMinimalFormula("float array[10]"))
        self.assertIsValidParse(t1)

        t1 = self.parse(self.makeMinimalFormula(
            "float array[1,3+7,@fish * #blong]"))

        indexes = t1.children[0].children[0].children[0].children
        self.assertEqual(1, indexes[0].leaf)
        self.assertEqual(3, len(indexes))
        self.assertIsValidParse(t1)

    def testStrings(self):
        t1 = self.parse('''
        t1 {
        loop:
        x = "wombat"
        default:
        x = ""
        y = "hi"
        z = "hello" "world" "long list"
        }
        ''')
        self.assertIsValidParse(t1)
        self.assertEqual(len(self.allNodesOfType(t1, "string")), 6)
        self.assertIsBadFormula(self.makeMinimalFormula('"'),
                                "unexpected '\"'", 3)

    def testParamBlocks(self):
        t1 = self.parse('''
        t1 {
        default:
        complex param x
        title = "fish"
        default=(0.0,0)
        endparam
        param y
        enum = "foo" "bar"
        endparam
        }
        ''')
        self.assertIsValidParse(t1)

    def testUseEnum(self):
        t1 = self.parse('''
        t1 {
        init:
        if @y == "foo"
           x = 1
        elseif @y == "bar"
           x = 2
        endif
        default:
        param y
        enum = "foo" "bar"
        endparam
        }
        ''')
        self.assertIsValidParse(t1)

    def testFuncBlocks(self):
        t1 = self.parse('''
        t1 {
        default:
        func fn1
           caption = "fn1"
           default = cabs()
        endfunc
        }
        ''')
        self.assertIsValidParse(t1)

    def disabled_testGibberish(self):
        # parser doesn't like this, but can't think of a good fix right now
        t = self.parse('''
        t1 {
        ''')
        self.assertTrue(absyn.CheckTree(t))

    def testHeading(self):
        t1 = self.parse('''
        t1{
        default:
        heading
         caption = "fish face heading"
        endheading
        }
        ''')
        self.assertIsValidParse(t1)

    def testRepeat(self):
        t1 = self.parse(self.makeMinimalFormula(
            '''repeat
        z = z ^ 2
        until |z| > 2000.0
        '''))
        self.assertIsValidParse(t1)

    def testWhile(self):
        t1 = self.parse(self.makeMinimalFormula(
            '''while 1 > 0
             z = z + 2
             while x > y
               foo = bar
             endwhile
           endwhile
           '''))
        self.assertIsValidParse(t1)
        ns = [n for n in t1.children[0].children[0].children[0]]

        self.assertListTypesMatch(
            [n for n in t1.children[0].children[0].children[0]],
            ["while", "binop", "const", "const",
             "stmlist",
             "assign", "id", "binop", "id", "const",
             "while", "binop", "id", "id",
             "stmlist",
             "assign", "id", "id"
             ])

    # this comes from anon.ufm, which appears broken -UF doesn't
    # parse it either
    def testTrailingExpressions(self):
        f = '''
TZ0509-03 {
;
;from TieraZon2 fl-05-09.fll
init:
  z = -(3 * #pixel) / 5
loop:
  z = z - (z * z^4 + z^4 * #pixel - sin(z) - z) / (5 * z^4 + 4 * z^3 *
#pixel -
cos(z) - z)
bailout:
  |z| < 4
}
'''
        self.assertIsBadFormula(f, "unexpected newline", 8)

    def testSections(self):
        t1 = self.parse('''t1{
        Init:
        loop:
        :
        bailout:
        Transform:
        final:
        global:
        switch:
        DEFAULT:
        builtin:
        }
        ''')
        self.assertIsValidParse(t1)
        self.assertListTypesMatch(
            t1.children[0].children,
            ["stmlist"] * 7 + ["setlist"] * 3)

        # test we work with old-style fractint sections
        t1 = self.parse('''InvMandel (XAXIS) {; Mark Peterson
  c = z = 1 / pixel:z = sqr(z) + c
    |z| <= 4
  }
  ''')
        self.assertIsValidParse(t1)
        self.assertTrue(
            t1.children[0].children[0].type == "stmlist" and
            t1.children[0].children[0].leaf == "nameless" and
            t1.children[0].children[1].type == "stmlist" and
            t1.children[0].children[1].leaf == "")

    def testSymmetry(self):
        t1 = self.parse('''
MySymmetricalFractal (XAXIS) {
loop:
    z = zero(z)
}
''')
        self.assertEqual(t1.children[0].leaf, "MySymmetricalFractal")
        self.assertEqual(t1.children[0].symmetry, "XAXIS")

    def testSimpleMandelbrot(self):
        t1 = self.parse('''
MyMandelbrot {
init:
    z = 0
loop:
    z = z * z + #pixel
bailout:
    |z| < 4
default:
    title = "My Mandelbrot"
}
''')
        self.assertIsValidParse(t1)

    def testComma(self):
        self.assertParsesEqual("a=1,b=2", "a=1\nb=2")
        self.assertParsesEqual("if a==b,foo=bar,elseif a==c,foo=baz,endif",
                               "if a==b\nfoo=bar\nelseif a==c\nfoo=baz\nendif")
        self.assertParsesEqual("while a==b,foo,endwhile",
                               "while a==b\nfoo\nendwhile")
        t1 = self.parse('''t1{\ndefault:\n
          param bailout,caption = "Bailout",default = 30,endparam}''')
        self.assertIsValidParse(t1)

    def testParseErrors(self):
        self.assertIsBadFormula(self.makeMinimalFormula("2 + 3 +"),
                                "unexpected newline", 3)
        self.assertIsBadFormula(self.makeMinimalFormula("3 4"),
                                "unexpected number '4'", 3)

        # not a great error message...
        self.assertIsBadFormula(self.makeMinimalFormula("("),
                                "unexpected newline", 3)

    def disabled_testTwoLogistic(self):
        # a formula from orgform that causes trouble
        # looks like if without endif is allowed
        # don't want to try and support that right now
        src = '''TwoLogistic {; Peter Anders (anders@physik.hu-berlin.de)
  z=p1, c=pixel:
  r=rand
  if r<0.5
  z=c*z*(1-z)
  if r>=0.5
  z=c*z*(z-1)
  |fn1(z)|<real(p2)
  ;SOURCE: lambda.frm
}
'''
        t = self.parse(src)
        self.assertIsValidParse(t)

    def testTokenSpanningLines(self):
        # a single token which spans multiple lines
        src = '''foo {
        init:
        z = 1.0\\
        5\\
        3
        }'''
        t = self.parse(src)
        self.assertIsValidParse(t)

    def testParseArray(self):
        src = '''ary {
        init:
        int myarray[10]
        myarray[0] = 23 + myarray[1]
        }'''
        t = self.parse(src)
        self.assertIsValidParse(t)

    def assertListTypesMatch(self, nodes, types):
        self.assertEqual(len(nodes), len(types))
        for (n, t) in zip(nodes, types):
            self.assertEqual(n.type, t)

    def assertIsBadFormula(self, s, message, line):
        t1 = self.parse(s)
        self.assertTrue(absyn.CheckTree(t1), "invalid tree created")
        formula = t1.children[0]
        self.assertTrue(formula.type == "formula")
        err = formula.children[0]
        self.assertTrue(err.type == "error", "error not found")
        # print err.leaf
        self.assertNotEqual(re.search(message, err.leaf), None,
                            ("bad error message text '%s'", err.leaf))
        self.assertNotEqual(re.search(("^%s:" % line), err.leaf), None,
                            ("bad error message line number in '%s'", err.leaf))

    def assertIsValidParse(self, t1):
        self.assertTrue(absyn.CheckTree(t1))
        errors = self.allNodesOfType(t1, "error")
        self.assertEqual(errors, [], [str(e) for e in errors])

    def assertParsesEqual(self, s1, s2):
        t1 = self.parse(self.makeMinimalFormula(s1))
        t2 = self.parse(self.makeMinimalFormula(s2))
        # print(t1.pretty())
        # print(t2.pretty())
        self.assertTreesEqual(t1, t2)

    def assertTreesEqual(self, t1, t2):
        self.assertTrue(
            t1.DeepCmp(t2) == 0,
            ("%s, %s should be equivalent" % (t1.pretty(), t2.pretty())))

    def allNodesOfType(self, t1, type):
        return [n for n in t1 if n.type == type]

    # shorthand for minimal formula defn containing exp
    def makeMinimalFormula(self, exp):
        return '''t2 {
init:
%s
}
''' % exp
