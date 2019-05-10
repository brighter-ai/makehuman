import os
import uuid

import gui
import gui3d
import yaml
from PyQt5.QtWidgets import *
from core import G

from .util.camera import Camera
from .util.constant import EXPRESSIONS
from .util.model_data import ModelData
from .util.regressors import AgeRegressor, BetaRegressor, ConstRegressor, FaceRegressor
from .util.savers import AttributeSaver, UVMapSaver, VerticesSaver, ScreenSaver, CenterPointSaver
from .util.selectors import EyelashesSelector, EyebrowsSelector, EyeColorSelector, EyesSelector, TeethSelector, \
    TongueSelector, ExpressionSelector, SkinSelector, BackgroundSelector


class BrighterAITaskView(gui3d.TaskView):
    config_filename = '.config.yaml'
    config_attr = ['stddev', 'constant', 'grid_h', 'grid_w', 'min_angle', 'max_angle', 'min_age', 'max_age', 'restriction', 'symmetry', 'community', 'special', 'exp_nbr',
                   'canvas_size', 'quantity', 'saving_path']
    defaults = [0.16, 0.5, 3, 3, -90, 90, 20, 70, True, True, False, False, 5, 800, 10, '']

    def __init__(self, category):

        self.constant = 0.5
        self.stddev = 0.16
        self.grid_h = 3
        self.grid_w = 3
        self.min_angle = -90
        self.max_angle = 90
        self.min_age = 0
        self.max_age = 70
        self.community = False
        self.special = False
        self.restriction = True
        self.symmetry = True
        self.exp_nbr = 5
        self.canvas_size = 800
        self.quantity = 10
        self.saving_path = ''
        self.is_warned = False
        self.config_loaded = False

        self.md = ModelData()
        self.app = G.app
        # set smoothed to True => better rendering, more details
        self.app.selectedHuman.setSubdivided(True)

        gui3d.TaskView.__init__(self, category, 'Brighter AI')

        bai_box = self.addLeftWidget(gui.GroupBox('Generate 3D Faces'))

        self.samplingLabel = bai_box.addWidget(gui.TextView('Sampling parameters:'))

        self.restriction_CB = bai_box.addWidget(gui.CheckBox('Restrictions'))
        self.restriction_CB.setChecked(True)
        self.symmetry_CB = bai_box.addWidget(gui.CheckBox('Symmetry'))
        self.symmetry_CB.setChecked(True)

        self.stddev_S = bai_box.addWidget(gui.Slider(value=self.stddev, label='Standard Deviation'))
        self.stddev_Label = bai_box.addWidget(gui.TextView(
            'Uniform Distribution' if self.stddev == 0. else 'Normal Dist N(0.0, {:.2f})'.format(self.stddev)
        ))

        bai_box.addWidget(gui.TextView(''))

        self.camSizeLabel = bai_box.addWidget(gui.TextView('Camera Grid Size:'))
        self.grid_h_TE = bai_box.addWidget(gui.TextEdit(text=''))
        self.grid_h_TE.setPlaceholderText('Height')
        self.grid_w_TE = bai_box.addWidget(gui.TextEdit(text=''))
        self.grid_w_TE.setPlaceholderText('Width')
        self.camSizeError = bai_box.addWidget(gui.TextView('grid size: {} x {}'.format(self.grid_w, self.grid_h)))

        self.camAngleLabel = bai_box.addWidget(gui.TextView('Camera Angle Interval:'))
        self.min_angle_TE = bai_box.addWidget(gui.TextEdit(text=''))
        self.min_angle_TE.setPlaceholderText('Min angle')
        self.max_angle_TE = bai_box.addWidget(gui.TextEdit(text=''))
        self.max_angle_TE.setPlaceholderText('Max angle')
        self.camAngleError = bai_box.addWidget(gui.TextView('[{}, {}]'.format(self.min_angle, self.max_angle)))

        self.ageIntervalLabel = bai_box.addWidget(gui.TextView('Age interval:'))
        self.min_age_TE = bai_box.addWidget(gui.TextEdit(text=''))
        self.min_age_TE.setPlaceholderText('Min age')
        self.max_age_TE = bai_box.addWidget(gui.TextEdit(text=''))
        self.max_age_TE.setPlaceholderText('Max age')
        self.ageErrorLabel = bai_box.addWidget(gui.TextView('{} <= age <= {}'.format(self.min_age, self.max_age)))

        self.community_CB = bai_box.addWidget(gui.CheckBox('Community Skins'))
        self.special_CB = bai_box.addWidget(gui.CheckBox('Special Skins'))

        self.expLabel = bai_box.addWidget(gui.TextView('# expression per model:'))
        self.exp_nbr_TE = bai_box.addWidget(gui.TextEdit(text=''))
        self.expErrorLabel = bai_box.addWidget(gui.TextView('# = {}'.format(self.exp_nbr)))

        self.CSLabel = bai_box.addWidget(gui.TextView('Image Shape (height = width)'))
        self.canvas_size_TE = bai_box.addWidget(gui.TextEdit(text=''))
        self.csErrorLabel = bai_box.addWidget(gui.TextView('Image shape = {}x{}'.format(self.canvas_size, self.canvas_size)))

        self.quantityLabel = bai_box.addWidget(gui.TextView('# models to generate:'))
        self.quantity_TE = bai_box.addWidget(gui.TextEdit(text=''))
        self.qErrorLabel = bai_box.addWidget(gui.TextView('# = {}'.format(self.quantity)))

        self.savingPathLabel = bai_box.addWidget(gui.TextView('Saving directory path:'))
        self.saving_path_TE = bai_box.addWidget(gui.TextEdit(text=''))
        self.saving_path_TE.setPlaceholderText('Absolute path')
        self.spErrorLabel = bai_box.addWidget(gui.TextView(''))

        self.startButton = bai_box.addWidget(gui.Button("Start"))

        @self.stddev_S.mhEvent
        def onChange(value):
            # print(dir(self.stddev_S))
            self.stddev = round(value, 2)
            self.stddev_S.setValue(self.stddev)
            if value == 0.0:
                self.stddev_Label.setTextFormat('Uniform Distribution')
            else:
                self.stddev_Label.setTextFormat('Normal Dist N(0.0, {:.2f})'.format(self.stddev))

        @self.restriction_CB.mhEvent
        def onClicked(event):
            self.restriction = self.restriction_CB.selected

        @self.symmetry_CB.mhEvent
        def onClicked(event):
            self.symmetry = self.symmetry_CB.selected

        @self.grid_h_TE.mhEvent
        def onChange(event):
            try:
                self.grid_h = int(self.grid_h_TE.getText())
                if self.grid_h < 1 or self.grid_h > 9:
                    raise ValueError()
                self.camSizeError.setTextFormat('grid size: %d x %d', self.grid_w, self.grid_h)
            except ValueError:
                self.camSizeError.setText('1 <= Height <= 9')

        @self.grid_w_TE.mhEvent
        def onChange(event):
            try:
                self.grid_w = int(self.grid_w_TE.getText())
                if self.grid_w < 1 or self.grid_w > 9:
                    raise ValueError()
                self.camSizeError.setTextFormat('grid size: %d x %d', self.grid_w, self.grid_h)
            except ValueError:
                self.camSizeError.setText('1 <= Width <= 9')

        @self.min_angle_TE.mhEvent
        def onChange(event):
            try:
                self.min_angle = int(self.min_angle_TE.getText())
                if self.min_angle < -90 or self.min_angle >= self.max_angle:
                    raise ValueError()
                self.camAngleError.setTextFormat('[{}, {}]'.format(self.min_angle, self.max_angle))
            except ValueError:
                self.camAngleError.setText('-90 <= Max Angle <= {}'.format(self.max_angle))

        @self.max_angle_TE.mhEvent
        def onChange(event):
            try:
                self.max_angle = int(self.max_angle_TE.getText())
                if self.max_angle > 90 or self.max_angle <= self.min_angle:
                    raise ValueError()
                self.camAngleError.setTextFormat('[{}, {}]'.format(self.min_angle, self.max_angle))
            except ValueError:
                self.camAngleError.setText('{} <= Max Angle <= 90'.format(self.min_angle))

        @self.min_age_TE.mhEvent
        def onChange(event):
            try:
                self.ageErrorLabel.setText('')
                self.min_age = int(self.min_age_TE.getText())
                if self.min_age < 0 or self.min_age >= self.max_age or self.max_age > 70:
                    raise ValueError()
                self.ageErrorLabel.setTextFormat('%d <= age <= %d', self.min_age, self.max_age)
            except ValueError:
                self.ageErrorLabel.setText('0 <= min < max <= 70')

        @self.max_age_TE.mhEvent
        def onChange(event):
            try:
                self.ageErrorLabel.setText('')
                self.max_age = int(self.max_age_TE.getText())
                if self.min_age < 0 or self.min_age >= self.max_age or self.max_age > 70:
                    raise ValueError()
                self.ageErrorLabel.setTextFormat('%d <= age <= %d', self.min_age, self.max_age)
            except ValueError:
                self.ageErrorLabel.setText('0 <= min < max <= 70')

        @self.community_CB.mhEvent
        def onClicked(event):
            self.community = self.community_CB.selected

        @self.special_CB.mhEvent
        def onClicked(event):
            self.special = self.special_CB.selected

        @self.saving_path_TE.mhEvent
        def onChange(event):
            self.saving_path = self.saving_path_TE.getText()
            if os.path.isfile(os.path.join(self.saving_path, self.config_filename)):
                load_config(self.saving_path)
            else:
                if self.config_loaded:
                    set_form_values(self.config_attr, self.defaults, disabled=False)
                self.md.set('saving_path', self.saving_path)
                if not os.path.isdir(self.saving_path):
                    self.spErrorLabel.setText('Directory does not exist.')
                elif not os.access(self.saving_path, os.W_OK):
                    self.spErrorLabel.setText('Directory is not writable.')
                else:
                    self.spErrorLabel.setText('')

        @self.exp_nbr_TE.mhEvent
        def onChange(event):
            try:
                self.exp_nbr = int(self.exp_nbr_TE.getText())
                self.expErrorLabel.setText('# = {}'.format(self.exp_nbr))
                if self.exp_nbr < 1 or self.exp_nbr > len(EXPRESSIONS):
                    raise ValueError()
            except ValueError:
                self.expErrorLabel.setText('1 <= # expression/model <= {}'.format(len(EXPRESSIONS)))

        @self.quantity_TE.mhEvent
        def onChange(event):
            try:
                self.quantity = int(self.quantity_TE.getText())
                self.qErrorLabel.setText('# = {}'.format(self.quantity))
                if self.quantity < 1 or self.quantity > 1000000:
                    raise ValueError()
            except ValueError:
                self.qErrorLabel.setText('1 <= # models <= 1000000')

        @self.canvas_size_TE.mhEvent
        def onChange(event):
            try:
                self.canvas_size = int(self.canvas_size_TE.getText())
                self.csErrorLabel.setText('Image shape = {}x{}'.format(self.canvas_size, self.canvas_size))
                if self.canvas_size < 300 or self.canvas_size > 1400:
                    raise ValueError()
            except ValueError:
                self.csErrorLabel.setText('300 <= Canvas Size <= 1400')

        @self.startButton.mhEvent
        def onClicked(event):
            error = is_form_invalid()
            if error:
                self.startButton.setText(error)
            elif not self.is_warned:
                show_reminder()
            else:
                self.startButton.setText('Start')
                set_canvas_size(self.canvas_size)

                eyelashes_selector = EyelashesSelector(self.app.modules['3_libraries_eyelashes'].taskview)
                eyebrows_selector = EyebrowsSelector(self.app.modules['3_libraries_eyebrows'].taskview)
                eye_color_selector = EyeColorSelector(self.app.modules['3_libraries_material_chooser'].material, self.app.selectedHuman)
                eyes_selector = EyesSelector(self.app.modules['3_libraries_eye_chooser'].taskview)
                teeth_selector = TeethSelector(self.app.modules['3_libraries_teeth'].taskview)
                tongue_selector = TongueSelector(self.app.modules['3_libraries_tongue'].taskview)
                exp_tv = self.app.modules['2_posing_expression'].taskview
                expression_selector = ExpressionSelector(exp_tv, self.exp_nbr)

                age_reg = AgeRegressor(self.app.selectedHuman, self.min_age, self.max_age)
                beta_reg = BetaRegressor(self.app.selectedHuman)
                const_reg = ConstRegressor(self.app.selectedHuman, self.constant)
                face_reg = FaceRegressor(self.app.selectedHuman, stddev=self.stddev, symmetry=self.symmetry, restricted=self.restriction)
                camera = Camera(self.app, self.grid_w, self.grid_h, self.min_angle, self.max_angle)

                screen_saver = ScreenSaver(G.windowWidth, G.windowHeight)
                uv_map_saver = UVMapSaver(self.app.selectedHuman.material)
                vertices_saver = VerticesSaver(self.app.mhapi.mesh, G.app.mhapi.locations.getInstallationPath())
                cp_saver = CenterPointSaver(self.app.selectedHuman)
                skin_selector = SkinSelector(self.app.selectedHuman, community=self.community, special=self.special)
                bg_selector = BackgroundSelector()

                with AttributeSaver() as w:
                    if not self.config_loaded:
                        dump_config()
                    for q in range(self.quantity):
                        # reset model expression
                        exp_tv.chooseExpression(None)

                        const_reg.apply()
                        eyes_selector.apply()
                        tongue_selector.apply()

                        eyelashes_selector.apply()
                        eye_color_selector.apply()
                        eyebrows_selector.apply()
                        teeth_selector.apply()
                        face_reg.apply()
                        age_reg.apply()
                        beta_reg.apply()
                        skin_selector.apply()
                        self.app.selectedHuman.applyAllTargets()
                        self.md.set('model_uid', str(uuid.uuid4()).replace('-', '_'))

                        uv_map_saver.save()
                        vertices_saver.save(expression=False)

                        for _, expression in expression_selector.apply():
                            vertices_saver.save()
                            for i in camera.get_cam_position():
                                bg_selector.apply()
                                screen_saver.save(expression, i)
                                cp_saver.save()
                                w.save()
                self.is_warned = False

        def load_config(save_path):

            self.config_loaded = True

            def dirname(path):
                if path[-1] == '/':
                    path = path[:-1]
                return os.path.dirname(path), os.path.basename(path)

            self.saving_path, data_dir = dirname(self.saving_path)
            self.md.set('data_dir', data_dir)
            self.md.set('saving_path', self.saving_path)

            with open(os.path.join(save_path, self.config_filename), 'r') as stream:
                data_dic = yaml.load(stream)  # type: dict
                set_form_values(list(data_dic.keys()), list(data_dic.values()), disabled=True)

        def set_form_values(attributes, values, disabled=False):
            # change all the attributes except the saving_path
            for attr, value in zip(attributes, values):
                setattr(self, attr, value)
                if attr in ['symmetry', 'restriction', 'community', 'special']:
                    getattr(self, attr + '_CB').setChecked(value)
                    getattr(self, attr + '_CB').setDisabled(disabled)
                elif attr == 'constant' or attr == 'saving_path':
                    continue
                elif attr == 'stddev':
                    self.stddev_S.setValue(value)
                    self.stddev_S.setDisabled(disabled)
                else:
                    getattr(self, attr + '_TE').setText(str(value))
                    if attr not in ['saving_path', 'quantity']:
                        getattr(self, attr + '_TE').setDisabled(disabled)

        def dump_config():
            data = {}
            for key in self.config_attr:
                data[key] = getattr(self, key)

            with open(os.path.join(self.saving_path, self.md.get('data_dir'), self.config_filename), 'w') as f:
                yaml.dump(data, f)

        def is_form_invalid():
            if self.grid_h < 1 or self.grid_h > 9:
                return 'grid height invalid'
            elif self.grid_w < 1 or self.grid_w > 9:
                return 'grid width invalid'
            elif self.min_angle < -90 or self.min_angle > self.max_angle:
                return 'min angle invalid'
            elif self.max_angle < self.min_angle or self.max_angle > 90:
                return 'max angle invalid'
            elif self.quantity < 1 or self.quantity > 1000000:
                return '# models invalid'
            elif not os.path.isdir(self.saving_path) or not os.access(self.saving_path, os.W_OK):
                return 'saving path invalid'
            elif self.min_age < 0 or self.min_age > self.max_age:
                return 'min age invalid'
            elif self.max_age < self.min_age or self.max_age > 70:
                return 'max age invalid'
            if self.canvas_size < 300 or self.canvas_size > 1400:
                return 'canvas size invalid'
            else:
                return None

        def show_reminder():
            msg = "You seem to be ready to start generating some ugly faces, but before, please make sure to:\n\n"
            msg = msg + "Select a background image for all sides:\n"
            msg = msg + "\t1.1: Go to Settings > Background\n"
            msg = msg + "\t1.2: Choose side \"Other\"\n"
            msg = msg + "\t1.3: Set opacity to 100%\n"
            msg = msg + "\t1.4: Select the image: \"Selected\"\n"

            self.msg = QMessageBox()
            self.msg.setIcon(QMessageBox.Information)
            self.msg.setText(msg)
            self.msg.setWindowTitle('Faces generation prerequisites')
            self.msg.setStandardButtons(QMessageBox.Ok)
            self.msg.show()
            self.is_warned = True

        def set_canvas_size(size):
            main_win = G.app.mainwin
            central = main_win.centralWidget()
            c_width = central.frameSize().width()
            c_height = central.frameSize().height()

            c_width = c_width + size - G.windowWidth
            c_height = c_height + size - G.windowHeight

            central.setFixedSize(c_width, c_height)
            main_win.adjustSize()
