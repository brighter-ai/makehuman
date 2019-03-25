from abc import ABCMeta, abstractmethod
from .constant import CONST_TARGETS, FACE_TARGETS, BETA_TARGETS, ETHNICITY
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


class AgeRegressor(Regressor):

    def __init__(self, human, min_age, max_age):
        self.human = human
        self.md = ModelData()
        self.age = None
        self.min_age = min_age / 70.
        self.max_age = max_age / 70.

    def randomize(self):
        self.age = self.min_age  # (self.max_age - self.min_age) * np.random.random() + self.min_age  # /home/bothmena/Data/BrighterAI/fixed_age
        self.md.set('macrodetails/Age', self.age)
        self.md.set('real_age', self.age * 70)

    def apply(self, reselect=True):
        if reselect:
            self.randomize()
        modifier = self.human.getModifier('macrodetails/Age')
        modifier.setValue(self.age)


class BetaRegressor(Regressor):

    def __init__(self, human):
        self.human = human
        self.md = ModelData()
        self.values = {}

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


class ConstRegressor(Regressor):

    def __init__(self, human, const):
        self.human = human
        self.constant = const
        self.md = ModelData()
        self.values = {}

    def randomize(self):
        for modifier in CONST_TARGETS:
            val = self.constant
            if modifier == 'macrodetails-height/Height':
                val = 0.75
            self.values[modifier] = val
            self.md.set(modifier, val)

    def apply(self):
        self.randomize()
        for key, val in self.values.items():
            modifier = self.human.getModifier(key)
            modifier.setValue(val)


class EthnicityRegressor(Regressor):

    def __init__(self, human):
        self.human = human
        self.md = ModelData()
        self.values = {}

    def randomize(self):
        p_af = random()
        p_as = (1 - p_af) * random()
        probs = [p_af, p_as, 1 - p_af - p_as]

        for key, val in zip(ETHNICITY, probs):
            self.values[key] = val
            self.md.set(key, val)

        if (probs == np.max(probs)).sum() > 1:
            self.md.set('ethnicity', 'none')
        else:
            self.md.set('ethnicity', ['african', 'asian', 'caucasian'][np.argmax(probs)])

    def apply(self, reselect=True):
        if reselect:
            self.randomize()
        for key, val in self.values.items():
            modifier = self.human.getModifier(key)
            modifier.setValue(val)


class FaceRegressor(Regressor):

    def __init__(self, human, stddev):
        self.human = human
        self.md = ModelData()
        self.stddev = stddev
        self.values = {}

    def randomize(self):
        if self.stddev == 0:
            sample = random(len(FACE_TARGETS))
        else:
            sample = normal(0.5, self.stddev, 2 * len(FACE_TARGETS))
            sample = sample[(sample >= 0) & (sample <= 1)][:2 * len(FACE_TARGETS)]

        for key, val in zip(FACE_TARGETS, sample):
            self.values[key] = val
            self.md.set(key, val)

    def apply(self, reselect=True):
        if reselect:
            self.randomize()
        for key, val in self.values.items():
            modifier = self.human.getModifier(key)
            modifier.setValue(val)


class LightRegressor(Regressor):

    def __init__(self, light):
        self.light = light
        self.md = ModelData()
        self.values = {}

    def randomize(self):
        self.values['position'] = tuple(np.random.randint(-350, 350, 3) * 10)
        self.values['color'] = tuple(np.random.random(size=3))
        self.values['specular'] = tuple(np.random.random(size=3))

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
