from PIL import Image, ImageDraw
from PIL.ImageOps import flip
from util import collapse, nest_map
import pyglet
import math

class Img:
    def __init__(self, dim: int, bg: list=[255,255,255]) -> None:
        self.img = Image.new("RGB", (dim,dim), f'rgb({bg[0]},{bg[1]},{bg[2]})')
        self.draw_img = ImageDraw.Draw(self.img)
        self.scale = dim

    def draw_polygon(self, polygon, width=1, fill=[200,200,200], outline=[10,10,255]):
        tuple_copy = []
        for point in polygon:
            tuple_copy.append((point[0], point[1]))
        if not fill == None:
            self.draw_img.polygon(tuple_copy, fill=f'rgb({fill[0]},{fill[1]},{fill[2]})', outline=f'rgb({outline[0]},{outline[1]},{outline[2]})')
        if not width == 1 or fill == None:
            for i, p2 in enumerate(tuple_copy):
                p1 = tuple_copy[i-1]
                self.draw_img.line([p1, p2], fill=f'rgb({outline[0]},{outline[1]},{outline[2]})', width=width)
    
    def draw_line(self, line, width=1, outline=[10,10,255]):
        self.draw_img.line([tuple(line[0]), tuple(line[1])], fill=f'rgb({outline[0]},{outline[1]},{outline[2]})', width=width)
    
    def show(self):
        self.img = flip(self.img)
        self.img.show()

def quickdraw(lines=[], polygons=[]):
    min_x, min_y, max_x, max_y = 1<<31, 1<<31, -(1<<31), -(1<<31)
    for p in collapse(lines):
        if p[0] < min_x: min_x = p[0]
        if p[1] < min_y: min_y = p[1]
        if p[0] > max_x: max_x = p[0]
        if p[1] > max_y: max_y = p[1]
    for p in collapse(polygons):
        if p[0] < min_x: min_x = p[0]
        if p[1] < min_y: min_y = p[1]
        if p[0] > max_x: max_x = p[0]
        if p[1] > max_y: max_y = p[1]
    max_bound, min_bound = max(max_x, max_y), min(min_x, min_y)
    mult = 2000/(max_bound-min_bound)
    s = Img(2048)
    for p in polygons: s.draw_polygon(nest_map(nest_map(p, lambda x, y: x-y, min_bound), lambda x, y: x*y, mult))
    for l in lines: s.draw_line(nest_map(nest_map(l, lambda x, y: x-y, min_bound), lambda x, y: x*y, mult))
    s.show()

def run_screens(): pyglet.app.run()
class Screen:

    def __init__(self, dim: int, bg: list=[255,255,255], tolerance: int=5):
        self.window = pyglet.window.Window(width=dim, height=dim)
        self.tolerance = tolerance

        self.l_mouse_held = False
        self.dragged_point = []

        self.poly_methods = []
        self.temp_polygons = []

        self.points = []
        self.lines = []
        self.polygons = []
        self.p_v_list = pyglet.graphics.vertex_list(0, ('v2f', ()))
        self.l_v_list = pyglet.graphics.vertex_list(0, ('v2f', ()))
    
        @self.window.event
        def on_draw():
            
            self.temp_polygons = [[] for _ in self.poly_methods]
            for i, method in enumerate(self.poly_methods):
                polys_used = [self.polygons] + self.temp_polygons
                self.temp_polygons[i] = method[0]([polys_used[index[0]][index[1]] for index in method[1]])
            
            self.window.clear()
            # draw points
            self.p_v_list.resize(len(self.points))
            self.p_v_list.vertices = collapse(self.points)
            self.p_v_list.draw(pyglet.gl.GL_POINTS)
            # draw lines
            self.l_v_list.resize(len(self.lines)*2)
            self.l_v_list.vertices = collapse(collapse(self.lines))
            self.l_v_list.draw(pyglet.gl.GL_LINES)
            # draw polygons
            for polygon in collapse(self.temp_polygons):
                pyglet.graphics.draw(len(polygon), pyglet.gl.GL_TRIANGLE_FAN, ('v2f', collapse(polygon)))
        
        @self.window.event
        def on_key_press(symbol, modifiers):
            pass
            
        @self.window.event
        def on_key_release(symbol, modifiers):
            pass
        
        @self.window.event
        def on_mouse_press(x, y, button, modifiers):
            if button & pyglet.window.mouse.LEFT:
                self.l_mouse_held = True
                self.dragged_point = []
                for point in self.points:
                    if math.dist(point, (x,y)) < self.tolerance:
                        self.dragged_point = point

        @self.window.event
        def on_mouse_release(x, y, button, modifiers):
            if button & pyglet.window.mouse.LEFT:
                self.l_mouse_held = False

        @self.window.event
        def on_mouse_drag(x, y, dx, dy, button, modifiers):
            if self.l_mouse_held and self.dragged_point:
                self.dragged_point[0] = x
                self.dragged_point[1] = y
    
    def add_points(self, points):
        for point in points:
            if point not in self.points:
                self.points.append(point)

    def add_lines(self, lines):
        for line in lines:
            if line not in self.lines:
                self.add_points(line)
                self.lines.append(line)
    
    def add_polygons(self, polygons):
        for polygon in polygons:
            if polygon not in self.polygons:
                for i, point2 in enumerate(polygon):
                    point1 = polygon[i-1]
                    self.add_lines([[point1, point2]])
                self.polygons.append(polygon)
    
    def add_poly_method(self, method, polygon_indices):
        """Methods must take an array of n polygons in, where n is the number of indices passed, and return a list of polygons back.
        
        Indices are in the form (polygon list, index of polygon in list). By using a polygon list greater than 0, methods can access polygons created by previous methods."""
        self.poly_methods.append([method, polygon_indices])

if __name__ == "__main__":
    quickdraw(polygons=[[[151, 119], [150, 165], [225, 201], [225, 126]]])
    s = Screen(500)
    s.add_points([[10, 10]])
    s.add_lines([[[50, 50], [200, 200]], [[90, 250], [300, 100]]])
    run_screens()