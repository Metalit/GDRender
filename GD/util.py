import math
from copy import deepcopy

def one_dist_to(distance, point1, point2, added_rotation=0, degrees=False):
    """Returns a line dist away from point 1 in the direction of point 2, with an optional angle offset."""
    if distance == 0: return point1
    if degrees: added_rotation = math.radians(added_rotation)
    return [point1[0] + math.cos(angle(point1, point2) + added_rotation)*distance, point1[1] + math.sin(angle(point1, point2) + added_rotation)*distance]

def angle(point1, point2):
    """Returns the angle of the line starting at point 1 and ending at point 2.

    The angle given is counterclockwise, starting at a horizontal line pointing to the right."""
    x_dif = point2[0] - point1[0]
    y_dif = point2[1] - point1[1]
    return math.atan2(y_dif, x_dif)

def close_enough(subject1, subject2, max_difference=1/(1<<16))->"bool":
    """Returns true if values or potentially nested iterables of values are very close to another."""
    # neither are iterable - will give an error if values are not numbers
    if not hasattr(subject1, '__iter__') and not hasattr(subject2, '__iter__'):
        return abs(subject1 - subject2) < max_difference
    # both are iterable - will call recursively on all elements, stopping at whichever ends first
    elif hasattr(subject1, '__iter__') and hasattr(subject2, '__iter__'):
        min_len = min(len(subject1), len(subject2))
        for i in range(min_len):
            if not close_enough(subject1[i], subject2[i], max_difference):
                return False
        return True
    # one is iterable and one is not - two different data structures are not very close
    else: return False

def nest_map(subject, function, func_args):
    """Returns a list containing every value of a potentially nested list run through a function, in the same structure as the original."""
    ret = list()
    if not hasattr(subject, '__iter__'):
        return function(subject, func_args)
    else:
        for ele in subject:
            ret.append(nest_map(ele, function, func_args))
    return ret

def collapse(to_collapse: list):
    """Returns the elements of the list with one list layer stripped off.
    
    [ [1, 2], [3, 4] ] -> [1, 2, 3, 4]"""
    l = list()
    for ele in to_collapse:
        l += ele
    return l

def bounds(shapes):
    min_x, min_y, max_x, max_y = 1<<31, 1<<31, -(1<<31), -(1<<31)
    for p in collapse(shapes):
        if p[0] < min_x: min_x = p[0]
        if p[1] < min_y: min_y = p[1]
        if p[0] > max_x: max_x = p[0]
        if p[1] > max_y: max_y = p[1]
    return min_x, min_y, max_x, max_y

def circle(center):
    rt2 = math.sqrt(2)/2
    base = deepcopy([[1,0],[rt2,-rt2],[0,-1],[-rt2,-rt2],[-1,0],[-rt2,rt2],[0,1],[rt2,rt2]])
    for point in base:
        point[0], point[1] = point[0] + center[0], point[1] + center[1]
    return base

def intersection(line1, line2, only_forward=False)->"tuple[int, int]":
    """Returns the intersection of two lines, or false if the lines do not intersect."""
    d = (line2[1][1] - line2[0][1]) * (line1[1][0] - line1[0][0]) - (line2[1][0] - line2[0][0]) * (line1[1][1] - line1[0][1])
    if d == 0: return False
    uA = ((line2[1][0] - line2[0][0]) * (line1[0][1] - line2[0][1]) - (line2[1][1] - line2[0][1]) * (line1[0][0] - line2[0][0])) / d
    # uB = ((l1[1][0] - l1[0][0]) * (l1[0][1] - l2[0][1]) - (l1[1][1] - l1[0][1]) * (l1[0][0] - l2[0][0])) / d
    x = line1[0][0] + uA * (line1[1][0] - line1[0][0])
    y = line1[0][1] + uA * (line1[1][1] - line1[0][1])
    if only_forward:
        if abs(angle(line1[0], (x,y))%(math.pi*2) - angle(line1[0], line1[1])%(math.pi*2)) > 1: return False
        if abs(angle(line2[0], (x,y))%(math.pi*2) - angle(line2[0], line2[1])%(math.pi*2)) > 1: return False
    return [x, y]

def rot_around(point, center, angle, degrees=False)->"tuple[int, int]":
    """Returns the point rotated the angle counterclockwise around the center."""
    if degrees:
        angle = math.radians(angle)
    ox, oy = center
    px, py = point

    qx = ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy)
    qy = oy + math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy)
    return [qx, qy]

def translate(point, by_line):
    """Moves the point along the distance and direction specified by the line."""
    return [point[0] + by_line[1][0] - by_line[0][0], point[1] + by_line[1][1] - by_line[0][1]]

def area(polygon)->"int":
    """Returns the area of a polygon, negative if the points are in counterclockwise order."""
    if polygon == []:
        return 0
    ret = 0
    for i, p2 in enumerate(polygon):
        p1 = polygon[i-1]
        ret += (p2[0]-p1[0])*(p2[1]+p1[1])
    return ret/2

def angle_leq(point1, point2, point3, max_angle=math.pi, degrees=False)->"bool":
    """Returns if an angle is less than or equal to the given degrees, defaulting to 180.

    Requires the points to be in clockwise order around the polygon."""
    if degrees: max_angle = math.radians(max_angle)
    # rotate around p2 such that p2-p1 line is pointing to the right
    a = angle(point2, point1)
    point1, point2, point3 = [rot_around(p, point2, -a) for p in [point1,point2,point3]]
    # check side of angle
    return angle(point2, point3)%(math.pi*2) <= max_angle

def bisector(point1, point2, point3, over_180=False)->"list":
    """Returns a line from point 2 that bisects the angle."""
    m = 1
    if over_180: m = -1
    # check if lines are parallel
    if angle(point1, point2) == angle(point2, point3):
        return [point2, one_dist_to(1, point2, point3, added_rotation=-90*m, degrees=True)]
    # find same lengths along lines
    e1, e3 = one_dist_to(m, point2, point1), one_dist_to(m, point2, point3)
    # return line to midpoint of those lengths
    return [point2, [(e1[0]+e3[0])/2, (e1[1]+e3[1])/2]]

