from .constant import is_constant_key


class ModelData:

    data = {
        'saving_path': '',
        'data_dir': '',
        'model_uid': '',
        'image': '',
        'expression': '',
        'skin': '',
        'eye_color': '',
        'eyebrows': '',
        'eyelashes': '',
        'eyes': '',
        'teeth': '',
        'tongue': '',
        'ethnicity': '',
        'real_age': '',
        'camera_x': '',
        'camera_y': '',
        'center_x': '',
        'center_y': '',
        'center_z': '',
        'l_color_r': '',
        'l_color_g': '',
        'l_color_b': '',
        'l_position_x': '',
        'l_position_y': '',
        'l_position_z': '',
        'l_specular_r': '',
        'l_specular_g': '',
        'l_specular_b': '',
    }

    def __init__(self):
        pass

    def get(self, key):
        if self.data.__contains__(key):
            return self.data[key]
        else:
            return None

    def set(self, key, value):
        if self.data.__contains__(key):
            self.data[key] = value
        else:
            if is_constant_key(key):
                self.data[key] = value
