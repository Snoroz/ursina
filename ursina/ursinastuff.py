import sys
import os

from ursina import application
from ursina.scene import instance as scene
from ursina.sequence import Sequence, Func, Wait


class Empty():
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key ,value)

class DotDict(dict):
    """Custom dictionary class to allow dot notation access."""
    def __getattr__(self, attr):
        try:
            return self[attr]
        except KeyError:
            raise AttributeError(f"'DotDict' object has no attribute '{attr}'")

    def __setattr__(self, attr, value):
        self[attr] = value

    def __delattr__(self, attr):
        try:
            del self[attr]
        except KeyError:
            raise AttributeError(f"'DotDict' object has no attribute '{attr}'")


class Default:
    pass


def invoke(function, *args, **kwargs):  # reserved keywords: 'delay', 'unscaled'
    delay = 0
    if 'delay' in kwargs:
        delay = kwargs['delay']
        del kwargs['delay']

    unscaled = False
    if 'unscaled' in kwargs:
        unscaled = kwargs['unscaled']
        del kwargs['unscaled']

    ignore_paused = False
    if 'ignore_paused' in kwargs:
        ignore_paused = kwargs['ignore_paused']
        del kwargs['ignore_paused']

    if not delay:
        function(*args, **kwargs)
        return None

    if ignore_paused:
        unscaled = True

    return Sequence(
        Wait(delay),
        Func(function, *args, **kwargs),
        auto_destroy=True, ignore_paused=ignore_paused, unscaled=unscaled, started=True,
    )


def after(delay, unscaled=True):    # function for @after decorator. Use the docrator, not this.
    '''@after decorator for calling a function after some time.

        example:
        @after(.4)
        def reset_cooldown():
            self.on_cooldown = False
            self.color = color.green
    '''
    def _decorator(func):
        def wrapper(*args, **kwargs):
            invoke(func, *args, **kwargs, delay=delay, unscaled=unscaled)
        return wrapper()
    return _decorator



def destroy(entity, delay=0):
    if delay == 0:
        _destroy(entity)
        return True

    return invoke(_destroy, entity, delay=delay)
    # return Sequence(Wait(delay), Func(_destroy, entity), auto_destroy=True, started=True)


def _destroy(entity, force_destroy=False):
    # from ursina import camera
    # if not entity or entity == camera:
    #     return

    if entity.eternal and not force_destroy:
        return

    for child in entity.children:
        _destroy(child)

    if entity.collider:
        entity.collider.remove()

    if hasattr(entity, 'clip') and hasattr(entity, 'stop'): # stop audio
        entity.stop(False)

    if hasattr(entity, 'on_destroy'):
        entity.on_destroy()

    if entity in scene.entities:
        scene.entities.remove(entity)

    if entity in scene.collidables:
        scene.collidables.remove(entity)

    if hasattr(entity, '_parent') and entity._parent and hasattr(entity._parent, '_children') and entity in entity._parent._children:
        entity._parent._children.remove(entity)
        
    for e in entity.loose_children:
        destroy(e)
        
    if hasattr(entity, '_loose_parent') and entity._loose_parent and hasattr(entity._loose_parent, '_loose_children') and entity in entity._loose_parent._loose_children:
        entity._loose_parent._loose_children.remove(entity)

    if hasattr(entity, 'scripts'):
        for s in entity.scripts:
            del s

    if hasattr(entity, 'animations'):
        for anim in entity.animations:
            anim.kill()

    if hasattr(entity, 'tooltip'):
        _destroy(entity.tooltip)

    if hasattr(entity, '_on_click') and isinstance(entity._on_click, Sequence):
        entity._on_click.kill()

    if entity.hasPythonTag("Entity"):
        entity.clearPythonTag("Entity")

    entity.removeNode()

    if hasattr(entity.__class__, 'instances') and entity in entity.__class__.instances:
        entity.__class__.instances.remove(entity)
    #unload texture
    # if hasattr(entity, 'texture') and entity.texture != None:
    #     entity.texture.releaseAll()

    del entity

from typing import List
class Array2D(list):
    __slots__ = ('width', 'height', 'default_value')

    def __init__(self, width:int=None, height:int=None, default_value=0, data:List[List]=None):    
        self.default_value = default_value

        if data is not None:                # initialize with provided data
            self.width = len(data)
            self.height = len(data[0]) if self.width > 0 else 0
            if any(len(row) != self.height for row in data):
                raise ValueError("All rows in the data must have the same length.")
            super().__init__(data)
        
        else:   # Initialize with default values 
            if width is None or height is None:
                raise ValueError("Width and height must be provided if no data is given.")
            
            self.width = width
            self.height = height
            super().__init__([[self.default_value for _ in range(self.height)] for _ in range(self.width)])


    def reset(self):
        for x in range(self.width):
            for y in range(self.height):
                self[x][y] = self.default_value



class Array3D(list):
    __slots__ = ('width', 'height', 'depth', 'default_value', 'data')

    def __init__(self, width:int, height:int, depth:int, default_value=0):
        self.width = int(width)
        self.height = int(height)
        self.depth = int(depth)
        self.default_value = default_value
        super().__init__([Array2D(self.height, self.depth) for x in range(self.width)])

    def reset(self):
        for x in range(self.width):
            for y in range(self.height):
                for z in range(self.depth):
                    self[x][y][z] = self.default_value


def chunk_list(target_list, chunk_size):
    # yield successive chunks from list
    for i in range(0, len(target_list), chunk_size):
        yield target_list[i:i + chunk_size]


def flatten_list(target_list):
    # return [item for sublist in l for item in sublist]
    import itertools
    return list(itertools.chain(*target_list))


def flatten_completely(target_list):
    for i in target_list:
        if isinstance(i, (sub_list, tuple)):
            for j in flatten_list(i):
                yield j
        else:
            yield i


def enumerate_2d(target_2d_list):    # usage: for (x, y), value in enumerate_2d(my_2d_list)
    for x, line in enumerate(target_2d_list):
        for y, value in enumerate(line):
            yield (x, y), value


def enumerate_3d(target_3d_list):   # usage: for (x, y, z), value in enumerate_3d(my_3d_list)
    for x, vertical_slice in enumerate(target_3d_list):
        for y, log in enumerate(vertical_slice):
            for z, value in enumerate(log):
                yield (x, y, z), value


def rotate_2d_list(target_2d_list):
    return list(zip(*target_2d_list[::-1]))   # rotate


def list_2d_to_string(target_2d_list, characters='.#'):
    return '\n'.join([''.join([characters[e] for e in line]) for line in target_2d_list])


def size_list():    # return a list of current python objects sorted by size
    import operator

    globals_list = []
    globals_list.clear()
    for e in globals():
        # object, size
        globals_list.append([e, sys.getsizeof(e)])
    globals_list.sort(key=operator.itemgetter(1), reverse=True)
    print('scene size:', globals_list)


def find_sequence(name, file_types, folders): # find frame_0, frame_1, frame_2 and so on
    for folder in folders:
        for file_type in file_types:
            files = list(folder.glob(f'**/{name}*.{file_type}'))
            if files:
                files.sort()
                return files
    return []


def import_all_classes(path=application.asset_folder, debug=False):
    path = str(path)
    sys.path.append(path)
    from ursina.string_utilities import snake_to_camel
    from glob import iglob
    imported_successfully = []

    for file_path in iglob(path + '**/*.py', recursive=True):
        if '\\build\\' in file_path or '__' in file_path:
            continue

        rel_path = file_path[len(path):][:-3].replace('\\', '.')
        if rel_path.startswith('.'):
            rel_path = rel_path[1:]
        module_name = os.path.basename(file_path).split('.')[0]
        # class_name = snake_to_camel(module_name)
        module_name = module_name
        import_statement = 'from ' + rel_path + ' import *'

        try:
            exec(import_statement, globals())
            imported_successfully.append(module_name)
            if debug:
                print(import_statement)
        except:
            if debug:
                print('     x', import_statement)
            pass

    return imported_successfully


def print_on_screen(text, position=(0,0), origin=(-.5,.5), scale=1, duration=1):
    from ursina.text import Text
    text_entity = Text(text=text, position=position, origin=origin, scale=scale)
    destroy(text_entity, delay=duration)


class LoopingList(list):
    def __getitem__(self, i):
        return super().__getitem__(i % len(self))


# define a new metaclass which overrides the "__call__" function
class PostInitCaller(type):
    def __call__(cls, *args, **kwargs):
        obj = type.__call__(cls, *args, **kwargs)
        obj.__post_init__()
        return obj

if __name__ == '__main__':

    from ursina import *
    app = Ursina()


    list_2d = [
        [1,0,0,1, 0, 1,1,1,0, 0, 1,1,1,1, 0, 0,1,0,0],
        [1,0,0,1, 0, 1,0,0,1, 0, 1,1,1,0, 0, 0,1,0,0],
        [1,0,0,1, 0, 1,1,1,0, 0, 0,0,0,1, 0, 0,1,0,0],
        [0,1,1,0, 0, 1,0,0,1, 0, 1,1,1,1, 0, 0,1,0,0],
    ]
    print(list_2d_to_string(list_2d))


    a = Audio('sine')
    a.play()
    destroy(a, delay=1)
    # Player()
    app.run()
