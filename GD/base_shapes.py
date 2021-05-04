from create import *
from util import rot_around
from copy import deepcopy
import math

# in case it ever changes
smallest_scale = 2
one_block = 30
screen_res_x, screen_res_y = 750, 390

class Shape:
    
    def __init__(self, center: "tuple[int, int]", side_length: int, color: int, group):
        self.center = center
        self.side_length = side_length
        self.rot = 0
        self.color = color
        self.group = group
        self.bound_edge = [0, -1]
        self.string = ""
        self.type = ""

    # update the object for added movement and rotation
    def move(self, vector, rot, ease, x, length):
        if not vector == [0,0]:
            y = 0
            self.string += move_trigger((x,y), length, self.group, vector)

        if not rot == 0:
            y = 0
            self.string += rot_trigger((x,y), length, self.group, self.group, rot, ease)
    
    # find the corners of the space the object takes up inside the level
    # rot is clockwise
    def corners(self, center, rot, add_to=True, degrees=False):
        scale = self.side_length/smallest_scale
        if degrees: rot = math.radians(rot)
        if add_to:
            center = [self.center[0]+center[0], self.center[1]+center[1]]
            rot += self.rot
        new_corners = deepcopy(self.base_corners)
        # for each base corner, adjust for scale, offset by center, then rotate around center
        for i, c in enumerate(new_corners):
            c[0] = c[0]*scale + center[0]
            c[1] = c[1]*scale + center[1]
            new_corners[i] = rot_around(c, center, rot)
        return new_corners

class Line(Shape):

    base_corners = [[-smallest_scale/2, 0], [smallest_scale/2, 0]] # corners with center at 0, 0 at min scale

    def __init__(self, center: "tuple[int, int]", color: int, group):
        super().__init__(center, 1, color, group)
        self.string = solid_object(1753, center, scale=1, color=color, groups=group)
        self.type = "line"

class SharpTriangle(Shape):

    base_corners = [[-smallest_scale, -smallest_scale/2], [smallest_scale, -smallest_scale/2], [smallest_scale, smallest_scale/2]] # corners with center at 0, 0

    # generate a new object with various properties
    def __init__(self, center: "tuple[int, int]", side_length: int, color: int, group: "list[int]", flip: bool):
        super().__init__(center, side_length, color, group)
        self.flip = flip
        if flip: self.base_corners = [[-smallest_scale, -smallest_scale/2], [smallest_scale, -smallest_scale/2], [-smallest_scale, smallest_scale/2]]
        self.string = solid_object(694, center, scale=one_block/side_length, color=color, groups=[1, group], flipx=flip)
        self.type = "sharp_triangle"

class Triangle(Shape):

    base_corners = [[-smallest_scale/2, -smallest_scale/2], [smallest_scale/2, -smallest_scale/2], [smallest_scale/2, smallest_scale/2]] # corners with center at 0, 0

    # generate a new object with various properties
    def __init__(self, center: "tuple[int, int]", side_length: int, color: int, group: "list[int]", flip: bool):
        super().__init__(center, side_length, color, group)
        self.flip = flip
        if flip: self.base_corners = [[-smallest_scale/2, -smallest_scale/2], [smallest_scale/2, -smallest_scale/2], [-smallest_scale/2, smallest_scale/2]]
        self.string = solid_object(693, center, scale=one_block/side_length, color=color, groups=[1, group], flipx=flip)
        self.type = "triangle"

class Square(Shape):
    
    base_corners = [[-smallest_scale/2, -smallest_scale/2], [smallest_scale/2, -smallest_scale/2], [smallest_scale/2, smallest_scale/2], [-smallest_scale/2, smallest_scale/2]] # corners with center at 0, 0

    def __init__(self, center: "tuple[int, int]", side_length, color: int, group: "list[int]"):
        super().__init__(center, side_length, color, group)
        self.string = solid_object(211, center, scale=one_block/side_length, color=color, groups=[1, group])
        self.type = "square"

def shape_at(shape, side_length, pos, rot, flip=None):
    if not flip == None: s = shape([0,0], side_length, 1004, 2, flip)
    else: s = shape([0,0], side_length, 1004, 2)
    return s.corners(pos, rot)

if __name__ == "__main__":
    pass