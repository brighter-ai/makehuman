import gui3d
import gui
import os
import uuid
from core import G

from PyQt5.QtWidgets import *

from .util.selectors import EyelashesSelector, EyebrowsSelector, EyeColorSelector, EyesSelector, TeethSelector, \
    TongueSelector, ExpressionSelector, SkinSelector, BackgroundSelector
from .util.regressors import AgeRegressor, BetaRegressor, ConstRegressor, EthnicityRegressor, FaceRegressor
from .util.savers import AttributeSaver, UVMapSaver, VerticesSaver, ScreenSaver, CenterPointSaver
from .util.camera import Camera
from .util.model_data import ModelData
from .util.constant import EXPRESSIONS


class BrighterAITaskView(gui3d.TaskView):

    def __init__(self, category):

        self.sampling = 0
        self.grid_h = 3
        self.grid_w = 3
        self.min_angle = -90
        self.max_angle = 90
        self.quantity = 10
        self.canvas_size = 800
        self.exp_nbr = 5
        self.saving_path = ''
        self.min_age = 0
        self.max_age = 70
        self.stop_gen = False
        self.counter = 0
        self.community = False
        self.special = False
        self.is_warned = False

        self.md = ModelData()
        self.app = G.app
        # set smoothed to True => better rendering, more details
        self.app.selectedHuman.setSubdivided(True)

        gui3d.TaskView.__init__(self, category, 'Brighter AI')

        bai_box = self.addLeftWidget(gui.GroupBox('Generate 3D Faces'))

        self.samplingLabel = bai_box.addWidget(gui.TextView('Probability distribution (Face):'))
        self.samplingRBGroup = []

        # We make the first one selected
        self.samplingRB1 = bai_box.addWidget(gui.RadioButton(self.samplingRBGroup, 'Uniform', selected=True))
        self.samplingRB2 = bai_box.addWidget(gui.RadioButton(self.samplingRBGroup, 'N(0.5, 1/6)'))
        self.samplingRB3 = bai_box.addWidget(gui.RadioButton(self.samplingRBGroup, 'N(0.5, 1/3)'))
        self.samplingRB4 = bai_box.addWidget(gui.RadioButton(self.samplingRBGroup, 'N(0.5, 1/2)'))
        self.samplingRB5 = bai_box.addWidget(gui.RadioButton(self.samplingRBGroup, 'N(0.5, 2/3)'))

        self.camSizeLabel = bai_box.addWidget(gui.TextView('Camera Grid Size:'))
        self.camHeight = bai_box.addWidget(gui.TextEdit(text=''))
        self.camHeight.setPlaceholderText('Height')
        self.camWidth = bai_box.addWidget(gui.TextEdit(text=''))
        self.camWidth.setPlaceholderText('Width')
        self.camSizeError = bai_box.addWidget(gui.TextView('grid size: {} x {}'.format(self.grid_w, self.grid_h)))

        self.camAngleLabel = bai_box.addWidget(gui.TextView('Camera Angle Interval:'))
        self.camMin = bai_box.addWidget(gui.TextEdit(text=''))
        self.camMin.setPlaceholderText('Min angle')
        self.camMax = bai_box.addWidget(gui.TextEdit(text=''))
        self.camMax.setPlaceholderText('Max angle')
        self.camAngleError = bai_box.addWidget(gui.TextView('[{}, {}]'.format(self.min_angle, self.max_angle)))

        self.ageIntervalLabel = bai_box.addWidget(gui.TextView('Age interval:'))
        self.ageMin = bai_box.addWidget(gui.TextEdit(text=''))
        self.ageMin.setPlaceholderText('Min age')
        self.ageMax = bai_box.addWidget(gui.TextEdit(text=''))
        self.ageMax.setPlaceholderText('Max age')
        self.ageErrorLabel = bai_box.addWidget(gui.TextView('{} <= age <= {}'.format(self.min_age, self.max_age)))

        self.communityButton = bai_box.addWidget(gui.CheckBox('Community Skins'))
        self.specialButton = bai_box.addWidget(gui.CheckBox('Special Skins'))

        self.expLabel = bai_box.addWidget(gui.TextView('# expression per model:'))
        self.expTE = bai_box.addWidget(gui.TextEdit(text=''))
        self.expErrorLabel = bai_box.addWidget(gui.TextView('# = {}'.format(self.exp_nbr)))

        self.CSLabel = bai_box.addWidget(gui.TextView('Image Shape (height = width)'))
        self.canvasSizeTE = bai_box.addWidget(gui.TextEdit(text=''))
        self.csErrorLabel = bai_box.addWidget(gui.TextView('Image shape = {}x{}'.format(self.canvas_size, self.canvas_size)))

        self.quantityLabel = bai_box.addWidget(gui.TextView('# models to generate:'))
        self.quantityTE = bai_box.addWidget(gui.TextEdit(text=''))
        self.qErrorLabel = bai_box.addWidget(gui.TextView('# = {}'.format(self.quantity)))

        self.savingPathLabel = bai_box.addWidget(gui.TextView('Saving directory path:'))
        self.savingPathTE = bai_box.addWidget(gui.TextEdit(text=''))
        self.savingPathTE.setPlaceholderText('Absolute path')
        self.spErrorLabel = bai_box.addWidget(gui.TextView(''))

        self.startButton = bai_box.addWidget(gui.Button("Start"))

        @self.samplingRB1.mhEvent
        def onClicked(event):
            self.sampling = 0

        @self.samplingRB2.mhEvent
        def onClicked(event):
            self.sampling = 1 / 6.

        @self.samplingRB3.mhEvent
        def onClicked(event):
            self.sampling = 1 / 3.

        @self.samplingRB4.mhEvent
        def onClicked(event):
            self.sampling = 1 / 2.

        @self.samplingRB5.mhEvent
        def onClicked(event):
            self.sampling = 2 / 3.

        @self.camHeight.mhEvent
        def onChange(event):
            try:
                self.grid_h = int(self.camHeight.getText())
                if self.grid_h < 1 or self.grid_h > 9:
                    raise ValueError()
                self.camSizeError.setTextFormat('grid size: %d x %d', self.grid_w, self.grid_h)
            except ValueError:
                self.camSizeError.setText('1 <= Height <= 9')

        @self.camWidth.mhEvent
        def onChange(event):
            try:
                self.grid_w = int(self.camWidth.getText())
                if self.grid_w < 1 or self.grid_w > 9:
                    raise ValueError()
                self.camSizeError.setTextFormat('grid size: %d x %d', self.grid_w, self.grid_h)
            except ValueError:
                self.camSizeError.setText('1 <= Width <= 9')

        @self.camMin.mhEvent
        def onChange(event):
            try:
                self.min_angle = int(self.camMin.getText())
                if self.min_angle < -90 or self.min_angle >= self.max_angle:
                    raise ValueError()
                self.camAngleError.setTextFormat('[{}, {}]'.format(self.min_angle, self.max_angle))
            except ValueError:
                self.camAngleError.setText('-90 <= Max Angle <= {}'.format(self.max_angle))

        @self.camMax.mhEvent
        def onChange(event):
            try:
                self.max_angle = int(self.camMax.getText())
                if self.max_angle > 90 or self.max_angle <= self.min_angle:
                    raise ValueError()
                self.camAngleError.setTextFormat('[{}, {}]'.format(self.min_angle, self.max_angle))
            except ValueError:
                self.camAngleError.setText('{} <= Max Angle <= 90'.format(self.min_angle))

        @self.ageMin.mhEvent
        def onChange(event):
            try:
                self.ageErrorLabel.setText('')
                self.min_age = int(self.ageMin.getText())
                if self.min_age < 0 or self.min_age >= self.max_age or self.max_age > 70:
                    raise ValueError()
                self.ageErrorLabel.setTextFormat('%d <= age <= %d', self.min_age, self.max_age)
            except ValueError:
                self.ageErrorLabel.setText('0 <= min < max <= 70')

        @self.ageMax.mhEvent
        def onChange(event):
            try:
                self.ageErrorLabel.setText('')
                self.max_age = int(self.ageMax.getText())
                if self.min_age < 0 or self.min_age >= self.max_age or self.max_age > 70:
                    raise ValueError()
                self.ageErrorLabel.setTextFormat('%d <= age <= %d', self.min_age, self.max_age)
            except ValueError:
                self.ageErrorLabel.setText('0 <= min < max <= 70')

        @self.communityButton.mhEvent
        def onClicked(event):
            self.community = self.communityButton.selected

        @self.specialButton.mhEvent
        def onClicked(event):
            self.special = self.specialButton.selected

        @self.savingPathTE.mhEvent
        def onChange(event):
            self.saving_path = self.savingPathTE.getText()
            self.md.set('saving_path', self.saving_path)
            if not os.path.isdir(self.saving_path):
                self.spErrorLabel.setText('Directory does not exist.')
            elif not os.access(self.saving_path, os.W_OK):
                self.spErrorLabel.setText('Directory is not writable.')
            else:
                self.spErrorLabel.setText('')

        @self.expTE.mhEvent
        def onChange(event):
            try:
                self.exp_nbr = int(self.expTE.getText())
                self.expErrorLabel.setText('# = {}'.format(self.exp_nbr))
                if self.exp_nbr < 1 or self.exp_nbr > len(EXPRESSIONS):
                    raise ValueError()
            except ValueError:
                self.expErrorLabel.setText('1 <= # expression/model <= {}'.format(len(EXPRESSIONS)))

        @self.quantityTE.mhEvent
        def onChange(event):
            try:
                self.quantity = int(self.quantityTE.getText())
                self.qErrorLabel.setText('# = {}'.format(self.quantity))
                if self.quantity < 1 or self.quantity > 1000000:
                    raise ValueError()
            except ValueError:
                self.qErrorLabel.setText('1 <= # models <= 1000000')

        @self.canvasSizeTE.mhEvent
        def onChange(event):
            try:
                self.canvas_size = int(self.canvasSizeTE.getText())
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

                for age in [0, 7, 14, 21, 28, 35, 42, 49, 56, 63, 70]:

                    self.min_age = age

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
                    const_reg = ConstRegressor(self.app.selectedHuman, 0.5)
                    ethnicity_reg = EthnicityRegressor(self.app.selectedHuman)
                    face_reg = FaceRegressor(self.app.selectedHuman, self.sampling)
                    camera = Camera(self.app, self.grid_w, self.grid_h, self.min_angle, self.max_angle)

                    screen_saver = ScreenSaver(G.windowWidth, G.windowHeight)
                    uv_map_saver = UVMapSaver(self.app.selectedHuman.material)
                    vertices_saver = VerticesSaver(self.app.mhapi.mesh, G.app.mhapi.locations.getInstallationPath())
                    cp_saver = CenterPointSaver(self.app.selectedHuman)
                    skin_selector = SkinSelector(self.app.selectedHuman, community=self.community, special=self.special)
                    bg_selector = BackgroundSelector()

                    with AttributeSaver() as w:
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
                            ethnicity_reg.apply()
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

        def is_form_invalid():
            if self.sampling not in [0, 1 / 6., 1 / 3., 1 / 2., 2 / 3.]:
                return 'sampling invalid'
            elif self.grid_h < 1 or self.grid_h > 9:
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
