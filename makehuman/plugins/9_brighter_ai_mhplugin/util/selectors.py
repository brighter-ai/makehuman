from abc import ABCMeta, abstractproperty, abstractmethod
import os
import shutil
from PIL import Image
from numpy.random import randint
from .constant import TEETH, EXPRESSIONS, EYE_COLORS, EYEBROWS, EYELASHES, EYES, TONGUES, SKINS, COMMUNITY_SKINS, SPECIAL_SKINS, COMMUNITY_SPECIAL_SKINS
from .model_data import ModelData


class Selector:
    __metaclass__ = ABCMeta

    @abstractproperty
    def selected(self):
        """ set the entity properties to new random values """

    @abstractmethod
    def choose(self):
        """ set the entity properties to new random values """

    @abstractmethod
    def apply(self, select):
        """apply changes to the human model"""


class ExpressionSelector(Selector):

    def __init__(self, mh_tool, rand_expressions):
        self.mh_tool = mh_tool
        self.__selected = None
        self.selection = None
        self.rand_expressions = rand_expressions
        self.model_data = ModelData()
        # needed to be called at least once to be able to change the model expression.
        self.mh_tool._load_pose_units()

    @property
    def selected(self):
        return self.__selected

    def choose(self):
        self.__selected = self.selection[randint(0, len(self.selection))]
        self.model_data.set('expression', self.selected)

    def apply(self, reselect=True):
        self.selection = EXPRESSIONS.copy()
        for i in range(self.rand_expressions):
            if reselect:
                self.choose()
            self.mh_tool.chooseExpression('data/expressions/{}.mhpose'.format(self.selected))
            self.selection.pop(self.selection.index(self.selected))
            # just yielding something to iterate through.
            yield i, self.selected


class SkinSelector(Selector):

    def __init__(self, human, community=False, special=False):
        self.human = human
        self.__selected = None
        if community:
            self.selection = SKINS + COMMUNITY_SKINS
            if special:
                self.selection += SPECIAL_SKINS + COMMUNITY_SPECIAL_SKINS
        else:
            self.selection = SKINS
            if special:
                self.selection += SPECIAL_SKINS
        self.model_data = ModelData()

    @property
    def selected(self):
        return self.__selected

    def choose(self):
        self.__selected = self.selection[randint(0, len(self.selection))]
        self.model_data.set('skin', self.selected)

    def apply(self, reselect=True):
        if reselect:
            self.choose()
        file_path = 'data/skins/{}'.format(self.selected)
        self.human.material.fromFile(file_path)


class BackgroundSelector(Selector):

    backgrounds = []

    def __init__(self):
        self.__selected = None
        self.list_backgrounds()

    @property
    def selected(self):
        return os.path.join(os.path.expanduser('~/Documents/makehuman/v1py3/textures/'), self.__selected)

    def choose(self):
        self.__selected = self.backgrounds[randint(0, len(self.backgrounds))]

    def apply(self, reselect=True):
        if reselect:
            self.choose()
        shutil.copyfile(self.selected, os.path.expanduser('~/Documents/makehuman/v1py3/backgrounds/selected.jpg'))

    def list_backgrounds(self):
        """
        This function will list all the .jpg images.
        Because makehuman expects the image name to be: selected.jpg:
            if it finds a .jpeg image, it will rename it to .jpg
            if it finds a .png image it will convert it to a .jpg image and delete the original .png image
        :return: None
        """
        text_dir = os.path.expanduser('~/Documents/makehuman/v1py3/textures/')
        for filename in os.listdir(text_dir):
            if filename.endswith('.jpeg'):
                os.rename(os.path.join(text_dir, filename), os.path.join(text_dir, os.path.splitext(filename)[0] + '.jpg'))
                filename = os.path.splitext(filename)[0] + '.jpg'
            # transparent will turn to black
            # some picture are modified after the transformation
            elif filename.endswith('.png'):
                im = Image.open(os.path.join(text_dir, filename))
                im = im.convert('RGBA')
                os.remove(os.path.join(text_dir, filename))
                filename = os.path.splitext(filename)[0] + '.jpg'
                im.save(os.path.join(text_dir, filename))

            if filename.endswith('.jpg'):
                self.backgrounds.append(filename)


class EyeColorSelector(Selector):

    def __init__(self, mh_tool, human):
        self.mh_tool = mh_tool
        self.human = human
        self.__selected = None
        self.model_data = ModelData()

    @property
    def selected(self):
        return self.__selected

    def choose(self):
        self.__selected = EYE_COLORS[randint(0, len(EYE_COLORS))]
        self.model_data.set('eye_color', self.selected)

    def apply(self, reselect=True):
        if reselect:
            self.choose()
        file_path = 'data/eyes/materials/{}.mhmat'.format(self.selected)
        self.human.getEyesProxy().object.material = self.mh_tool.fromFile(file_path)


class EyebrowsSelector(Selector):

    proxy_type = 'eyebrows'

    def __init__(self, mh_tool):
        self.mh_tool = mh_tool
        self.__selected = None
        self.model_data = ModelData()

    @property
    def selected(self):
        return self.__selected

    def choose(self):
        self.__selected = EYEBROWS[randint(0, len(EYEBROWS))]
        self.model_data.set('eyebrows', self.selected)

    def apply(self, reselect=True):
        if reselect:
            self.choose()
        self.mh_tool.selectProxy('data/{}/{}/{}.mhclo'.format(self.proxy_type, self.selected, self.selected))


class EyelashesSelector(Selector):

    proxy_type = 'eyelashes'

    def __init__(self, mh_tool):
        self.mh_tool = mh_tool
        self.__selected = None
        self.model_data = ModelData()

    @property
    def selected(self):
        return self.__selected

    def choose(self):
        self.__selected = EYELASHES[randint(0, len(EYELASHES))]
        self.model_data.set('eyelashes', self.selected)

    def apply(self, reselect=True):
        if reselect:
            self.choose()
        self.mh_tool.selectProxy('data/{}/{}/{}.mhclo'.format(self.proxy_type, self.selected, self.selected))


class EyesSelector(Selector):

    proxy_type = 'eyes'

    def __init__(self, mh_tool):
        self.mh_tool = mh_tool
        self.__selected = None
        self.model_data = ModelData()

    @property
    def selected(self):
        return self.__selected

    def choose(self):
        self.__selected = EYES[randint(0, len(EYES))]
        self.model_data.set('eyes', self.selected)

    def apply(self, reselect=True):
        if reselect:
            self.choose()
        self.mh_tool.selectProxy('data/{}/{}/{}.mhclo'.format(self.proxy_type, self.selected, self.selected))


class TeethSelector(Selector):

    proxy_type = 'teeth'

    def __init__(self, mh_tool):
        self.mh_tool = mh_tool
        self.__selected = None
        self.model_data = ModelData()

    @property
    def selected(self):
        return self.__selected

    def choose(self):
        self.__selected = TEETH[randint(0, len(TEETH))]
        self.model_data.set('teeth', self.selected)

    def apply(self, reselect=True):
        if reselect:
            self.choose()
        self.mh_tool.selectProxy('data/{}/{}/{}.mhclo'.format(self.proxy_type, self.selected, self.selected))


class TongueSelector(Selector):

    proxy_type = 'tongue'

    def __init__(self, mh_tool):
        self.mh_tool = mh_tool
        self.__selected = None
        self.model_data = ModelData()

    @property
    def selected(self):
        return self.__selected

    def choose(self):
        self.__selected = TONGUES[randint(0, len(TONGUES))]
        self.model_data.set('tongue', self.selected)

    def apply(self, reselect=True):
        if reselect:
            self.choose()
        self.mh_tool.selectProxy('data/{}/{}/{}.mhclo'.format(self.proxy_type, self.selected, self.selected))
