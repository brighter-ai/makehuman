from numpy.random import randint
from .model_data import ModelData


class Camera:

    def __init__(self, app, grid_w, grid_h, min_angle, max_angle):
        self.app = app
        self.grid_w = grid_w
        self.grid_h = grid_h
        self.min_angle = min_angle
        self.max_angle = max_angle
        self.x_intervals = self.get_intervals(grid_w)
        self.y_intervals = self.get_intervals(grid_h)
        self.md = ModelData()

    def get_intervals(self, cells):
        diff = self.max_angle - self.min_angle

        def calc(ws, c):
            step = diff / ws
            return self.min_angle + c * step

        return [(calc(cells, i), calc(cells, i + 1)) for i in range(cells)]

    def get_cam_position(self):
        # counter = 0
        # for x_min, x_max in self.x_intervals:
        for counter in range(3):
            if counter == 0:
                a0, a1 = 0, 0
            elif counter == 1:
                a0, a1 = 90, 0
            else:
                a0, a1 = 0, 90
            self.app.setFaceCamera()
            # self.md.set('camera_x', randint(x_min, x_max))
            self.md.set('camera_x', a0)
            # self.md.set('camera_y', randint(y_min, y_max))
            self.md.set('camera_y', a1)
            self.app.zoomCamera(10)
            self.app.rotateCamera(0, self.md.get('camera_x'))
            self.app.rotateCamera(1, self.md.get('camera_y'))
            counter += 1
            yield counter
