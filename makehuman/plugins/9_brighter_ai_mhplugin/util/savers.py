import os
import time
import numpy as np
from .model_data import ModelData
from .regressors import LightRegressor
from abc import ABCMeta, abstractmethod
from .constant import INVISIBLE_SKINS
from core import G
import gui3d
import mh


class Saver:
    __metaclass__ = ABCMeta

    @abstractmethod
    def save(self):
        """ set the entity properties to new random values """


class UVMapSaver(Saver):

    def __init__(self, human_material):
        self.md = ModelData()
        self.human_material = human_material

    def save(self):
        dic = self.human_material.exportTextures('{}/{}/uv_maps'.format(self.md.get('saving_path'), self.md.get('data_dir')))
        os.rename(dic['diffuseTexture'], '{}/{}/uv_maps/{}.png'.format(self.md.get('saving_path'), self.md.get('data_dir'), self.md.get('model_uid')))


class ScreenSaver(Saver):

    def __init__(self, w_height, w_width):
        self.md = ModelData()
        self.scene = G.app.getScene()
        self.w_height = w_height
        self.w_width = w_width
        self.light_reg = LightRegressor(self.scene.lights[0])

    def save(self, expression, cam_counter):
        self.scene.load('data/scenes/default.mhscene')
        self.scene.lights[0] = self.light_reg.apply()

        G.app.setScene(self.scene)

        if self.md.get('skin') in INVISIBLE_SKINS:
            gui3d.app.switchCategory('Brighter AI')
        else:
            gui3d.app.switchCategory('Rendering')
            gui3d.app.switchTask('Scene')

        file_name = '{}_{}_{}.png'.format(self.md.get('model_uid'), expression, cam_counter)
        self.md.set('image', file_name)
        mh.grabScreen(1, 1, self.w_height, self.w_width, '{}/{}/images/{}'.format(self.md.get('saving_path'), self.md.get('data_dir'), file_name))


class VerticesSaver(Saver):

    def __init__(self, mesh, mh_install_dir):
        self.md = ModelData()
        self.mesh = mesh
        self.indices = np.load('{}/plugins/9_brighter_ai_mhplugin/util/face_indices.npy'.format(mh_install_dir))

    def save(self, expression=True):
        if expression:
            filename = '{}/{}/vertices/{}_{}'.format(self.md.get('saving_path'), self.md.get('data_dir'), self.md.get('model_uid'),
                                                     self.md.get('expression'))
        else:
            filename = '{}/{}/vertices/{}'.format(self.md.get('saving_path'), self.md.get('data_dir'), self.md.get('model_uid'))
        np.save(filename, self.mesh.getVertexCoordinates()[self.indices, :])


class CenterPointSaver(Saver):

    def __init__(self, human):
        self.md = ModelData()
        self.human = human

    def save(self):
        x, y, z = self.human.meshData.coord[132]
        self.md.set('center_x', x)
        self.md.set('center_y', y)
        self.md.set('center_z', z)


class AttributeSaver(Saver):

    def __init__(self):
        self.file = None
        self.md = ModelData()
        self.save_dir = self.md.get('saving_path')
        self.index = 1
        self.new_dir = True

        if self.md.get('data_dir') == '':
            lt = time.localtime()
            uid = "{}_{}_{}_{}_{}_{}".format(lt.tm_year, lt.tm_mon, lt.tm_mday, lt.tm_hour, lt.tm_min, lt.tm_sec)
            self.md.set('data_dir', uid)
        else:
            self.new_dir = False

        self.file_name = '{}/dataset.csv'.format(self.md.get('data_dir'))

    def __enter__(self):
        if self.new_dir:
            os.mkdir('{}/{}'.format(self.save_dir, self.md.get('data_dir')), 0o777)
            os.mkdir('{}/{}/images'.format(self.save_dir, self.md.get('data_dir')), 0o777)
            os.mkdir('{}/{}/vertices'.format(self.save_dir, self.md.get('data_dir')), 0o777)
            os.mkdir('{}/{}/uv_maps'.format(self.save_dir, self.md.get('data_dir')), 0o777)

            points_col_names = ''
            for i in range(68):
                points_col_names += ',x_{},y_{}'.format(i, i)
            self.file.write(
                'index,model_uid,image,age,gender,dominant_gender,skin,expression,l_position_x,l_position_y,l_position_z,l_color_r,l_color_g,'
                'l_color_b,l_specular_r,l_specular_g,l_specular_b,center_x,center_y,center_z,cam_angle_0,cam_angle_1' + points_col_names + '\n')
        else:
            self.index = sum(1 for _ in open(os.path.join(self.save_dir, self.file_name)))

        self.file = open(os.path.join(self.save_dir, self.file_name), 'a+')

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.file.close()

    def get_dominant_gender(self):
        return int(self.md.get('macrodetails/Gender') >= 0.5)

    def save(self):
        points_coords = [0] * 136
        formatted_str = '{}' + ',{}' * 157 + '\n'
        self.file.write(formatted_str.
                        format(self.index, self.md.get('model_uid'), self.md.get('image'), self.md.get('real_age'), self.md.get('macrodetails/Gender'), self.get_dominant_gender(),
                               self.md.get('skin'), self.md.get('expression'), self.md.get('l_position_x'), self.md.get('l_position_y'),
                               self.md.get('l_position_z'), self.md.get('l_color_r'), self.md.get('l_color_g'), self.md.get('l_color_b'),
                               self.md.get('l_specular_r'), self.md.get('l_specular_g'), self.md.get('l_specular_b'),
                               self.md.get('center_x'), self.md.get('center_y'), self.md.get('center_z'), self.md.get('camera_x'), self.md.get('camera_y'), *points_coords))
        self.index += 1
