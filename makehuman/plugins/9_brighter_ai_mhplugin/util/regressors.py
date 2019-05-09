from abc import ABCMeta, abstractmethod
from .constant import CONST_TARGETS, UNRESTRICTED_TARGETS, BETA_TARGETS, RESTRICTED_TARGETS, SYMMETRICAL_TARGETS, HEAD_SHAPE
from .model_data import ModelData
from numpy.random import beta, random, normal
import numpy as np


class Regressor:
    __metaclass__ = ABCMeta

    @abstractmethod
    def randomize(self):
        """ set the entity properties to new random values """

    @abstractmethod
    def apply(self):
        """apply changes to the human model"""


class ApplyRegressor(Regressor):

    """
    A class that implements apply() function and require human instance as an arg.
    just to avoid implementing the same __init__ and apply functions multiple times
    """
    def __init__(self, human):
        self.human = human
        self.md = ModelData()
        self.values = {}

    @abstractmethod
    def randomize(self):
        """ set the entity properties to new random values """

    def apply(self, reselect=True):
        if reselect:
            self.randomize()
        for key, val in self.values.items():
            modifier = self.human.getModifier(key)
            modifier.setValue(val)


class AgeRegressor(Regressor):

    def __init__(self, human, min_age, max_age):
        self.human = human
        self.md = ModelData()
        self.age = None
        self.min_age = min_age / 70
        self.max_age = max_age / 70

    def randomize(self):
        self.age = (self.max_age - self.min_age) * random() + self.min_age
        self.md.set('macrodetails/Age', self.age)
        self.md.set('real_age', self.age * 70)

    def apply(self, reselect=True):
        if reselect:
            self.randomize()
        modifier = self.human.getModifier('macrodetails/Age')
        modifier.setValue(self.age)


class BetaRegressor(ApplyRegressor):

    def __init__(self, human):
        super(BetaRegressor, self).__init__(human)

    def randomize(self):
        for key, val in zip(BETA_TARGETS, beta(0.5, 0.5, len(BETA_TARGETS))):
            self.values[key] = val
            self.md.set(key, val)

    def apply(self, reselect=True):
        if reselect:
            self.randomize()
        for key, val in self.values.items():
            modifier = self.human.getModifier(key)
            modifier.setValue(val)


class ConstRegressor(ApplyRegressor):

    def __init__(self, human, const):
        super(ConstRegressor, self).__init__(human)
        self.constant = const

    def randomize(self):
        for modifier in CONST_TARGETS:
            val = self.constant
            if modifier == 'macrodetails-height/Height':
                val = 0.75
            self.values[modifier] = val
            self.md.set(modifier, val)


class HeadShapeRegressor(ApplyRegressor):

    def __init__(self, human):
        super(HeadShapeRegressor, self).__init__(human)

    def randomize(self):
        remaining = 1
        for i, target in enumerate(HEAD_SHAPE):
            if i == len(HEAD_SHAPE) - 1:
                value = remaining
            else:
                value = random() * min(0.5, remaining)
                remaining -= value

            self.values[target] = value


class SymmetricalRegressor(ApplyRegressor):

    def __init__(self, human, symmetry=True, stddev=0):
        super(SymmetricalRegressor, self).__init__(human)
        self.symmetry = symmetry
        self.stddev = stddev

    def randomize(self):
        for key in SYMMETRICAL_TARGETS:
            if self.stddev:
                values = normal(0, self.stddev, size=10)
                values = values[(values >= -1) & (values <= 1)][:2]
            else:
                values = random(2) * 2 - 1

            if self.symmetry:
                values = (values[0], values[0])

            self.values[key.replace('X', 'r')] = values[0]
            self.values[key.replace('X', 'l')] = values[1]


class RestrictedRegressor(ApplyRegressor):

    def __init__(self, human, restricted=True, stddev=0):
        super(RestrictedRegressor, self).__init__(human)
        self.restricted = restricted
        self.stddev = stddev

    def randomize(self):
        if self.restricted:
            for key, stats in RESTRICTED_TARGETS.items():
                val = random() * (stats[2] - stats[1]) + stats[1]
                self.values[key] = val
                self.md.set(key, val)
        else:
            if self.stddev == 0:
                values = random(len(RESTRICTED_TARGETS))
            else:
                values = normal(0, self.stddev, 2 * len(RESTRICTED_TARGETS))
                values = values[(values >= -1) & (values <= 1)][:len(RESTRICTED_TARGETS)]

            for key, val in zip(RESTRICTED_TARGETS, values):
                self.values[key] = val
                self.md.set(key, val)


class UnrestrictedRegressor(ApplyRegressor):

    def __init__(self, human, stddev):
        super(UnrestrictedRegressor, self).__init__(human)
        self.stddev = stddev

    def randomize(self):
        if self.stddev == 0:
            sample = random(len(UNRESTRICTED_TARGETS))
        else:
            sample = normal(0., self.stddev, 2 * len(UNRESTRICTED_TARGETS))
            sample = sample[(sample >= -1) & (sample <= 1)][:len(UNRESTRICTED_TARGETS)]

        for key, val in zip(UNRESTRICTED_TARGETS, sample):
            self.values[key] = val
            self.md.set(key, val)


class FaceRegressor:
    """
    This class should instantiate all face target regressors and randomize their values
    """
    def __init__(self, human, stddev=0, restricted=True, symmetry=True):
        self.sym_reg = SymmetricalRegressor(human, symmetry, stddev)
        self.res_reg = RestrictedRegressor(human, restricted, stddev)
        self.un_res_reg = UnrestrictedRegressor(human, stddev)
        self.head_reg = HeadShapeRegressor(human)

    def apply(self):
        self.sym_reg.apply()
        self.res_reg.apply()
        self.un_res_reg.apply()
        self.head_reg.apply()


class LightRegressor(Regressor):

    def __init__(self, light):
        self.light = light
        self.md = ModelData()
        self.values = {}

    def randomize(self):
        self.values['position'] = tuple(np.random.randint(-350, 350, 3) * 10)
        self.values['color'] = tuple(random(3))
        self.values['specular'] = tuple(random(3))

        for key, val in zip(['l_position_x', 'l_position_y', 'l_position_z', 'l_color_r', 'l_color_g', 'l_color_b', 'l_specular_r', 'l_specular_g', 'l_specular_b'],
                            self.values['position'] + self.values['color'] + self.values['specular']):
            self.md.set(key, val)

    def apply(self, reselect=True):
        if reselect:
            self.randomize()
        self.light.__setattr__('position', self.values['position'])
        self.light.__getattr__('color').setValues(*self.values['color'])
        self.light.__getattr__('specular').setValues(*self.values['specular'])
        return self.light
