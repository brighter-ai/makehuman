from unittest import TestCase
import sys
sys.path.append('/home/bothmena/Projects/PyCharm/BrighterAI/makehuman/makehuman/plugins/9_brighter_ai_mhplugin')
from util.regressors import HeadShapeRegressor, SymmetricalRegressor, RestrictedRegressor, BetaRegressor
from util.constant import RESTRICTED_TARGETS


class TestHeadShapeRegressor(TestCase):

    regressor = HeadShapeRegressor(None)

    def test_sum_equal_one(self):
        for _ in range(10):
            self.regressor.randomize()
            s = 0
            for _, v in self.regressor.values.items():
                s += v

            self.assertGreater(s, 1.0 - 1e-10, 'sum = ' + str(s))


class TestSymmetricalRegressor(TestCase):

    def test_symmetrical_equal(self):
        regressor = SymmetricalRegressor(None, symmetry=True, stddev=0)
        for _ in range(10):
            regressor.randomize()
            for k, v in regressor.values.items():
                if '/l-' in k:
                    new_k = k.replace('/l-', '/r-')
                else:
                    new_k = k.replace('/r-', '/l-')
                self.assertEqual(v, regressor.values[new_k])

    def test_asymmetrical_equal(self):
        regressor = SymmetricalRegressor(None, symmetry=False, stddev=0)
        for _ in range(10):
            regressor.randomize()
            for k, v in regressor.values.items():
                if '/l-' in k:
                    new_k = k.replace('/l-', '/r-')
                else:
                    new_k = k.replace('/r-', '/l-')
                self.assertNotEqual(v, regressor.values[new_k])

    def test_asymmetrical_normal_equal(self):
        regressor = SymmetricalRegressor(None, symmetry=False, stddev=0.5)
        for _ in range(10):
            regressor.randomize()
            for k, v in regressor.values.items():
                if '/l-' in k:
                    new_k = k.replace('/l-', '/r-')
                else:
                    new_k = k.replace('/r-', '/l-')
                self.assertNotEqual(v, regressor.values[new_k])


class TestRestrictedRegressor(TestCase):

    def test_restricted_range(self):
        regressor = RestrictedRegressor(None)
        for _ in range(10):
            regressor.randomize()
            for key, stats in RESTRICTED_TARGETS.items():
                self.assertGreaterEqual(regressor.values[key], stats[1])
                self.assertLessEqual(regressor.values[key], stats[2])

    def test_unrestricted_range(self):
        regressor = RestrictedRegressor(None, restricted=False)
        for _ in range(10):
            regressor.randomize()
            for key, stats in RESTRICTED_TARGETS.items():
                self.assertGreaterEqual(regressor.values[key], -1)
                self.assertLessEqual(regressor.values[key], 1)


class TestBetaRegressor(TestCase):

    def test_not_none(self):
        regressor = BetaRegressor(None)
        for _ in range(10):
            regressor.randomize()
            for key, val in regressor.values.items():
                self.assertIsNotNone(val)
                self.assertIsNotNone(regressor.md.get(key), key + ' is None!!!')
