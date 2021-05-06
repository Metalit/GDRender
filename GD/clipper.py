# pyclipper has weird syntax
# https://sourceforge.net/p/jsclipper/wiki/documentation/
from base_shapes import Square
from copy import deepcopy
import pyclipper as pc
from visualize import *
from util import *
import math

def straight_skeleton(polygon)->"tuple[list,list]":
    """Returns the straight skeleton in the form of a list of polygons for a given polygon.
    
    Also returns a list of the edge indices that each polygon contains."""
    # make the polygon clockwise
    if area(polygon) < 0: polygon = polygon[::-1]
    paths = [[] for _ in polygon]
    polygons = []
    # add all bisectors to paths
    for i, p3 in enumerate(polygon):
        # get three consecutive points
        p1, p2 = polygon[i-2], polygon[i-1]
        paths[i-1] = [bisector(p1, p2, p3, not angle_leq(p1, p2, p3))]*2
    while len(paths) > 2:
        # find closest path's intersection with neighbors
        close = [1<<31]
        # closest intersection for each path
        close_paths = [1<<31 for _ in paths]
        for i, path3 in enumerate(paths):
            # find intersections with adjacent paths
            path1, path2 = paths[i-2], paths[i-1]
            i1, i2 = intersection(path2[0][-2:], path1[0][-2:], True), intersection(path2[0][-2:], path3[0][-2:], True)
            # check for parallel endpoints
            #if close_enough(path2[0][-1], path1[0][-2]) or close_enough(path2[0][-1], path1[0][-1]):
            #    i1 = path2[0][-2]
            #if close_enough(path2[0][-1], path3[0][-2]) or close_enough(path2[0][-1], path3[0][-1]):
            #    i2 = path2[0][-2]
            # find distances to intersections
            d1, d2 = 1<<31, 1<<31
            if i1: d1 = math.dist(path2[0][-2], i1)
            if i2: d2 = math.dist(path2[0][-2], i2)
            # imprecision errors possible
            if d1 > 1<<16: i1 = False
            if d2 > 1<<16: i2 = False
            # no intersection in either (maybe shouldn't happen?)
            if not i1 and not i2: continue
            if i1:
                # make sure the other path hasn't been hit earlier
                hit_d = math.dist(path1[0][-2], i1)
                if close_paths[i-2] >= hit_d:
                    close_paths[i-2] = hit_d
                    # line was hit earlier
                    if close_paths[i-1] < d1: continue
                    close_paths[i-1] = d1
                    # new shortest, or it was hit earlier but that intersection was the closest so far
                    if min(d1, hit_d) < close[0] or paths[close[3]] == path1:
                        close = [min(d1, hit_d), i1, i-1, i-2, 0]
            if i2:
                # make sure the other path hasn't been hit earlier
                hit_d = math.dist(path3[0][-2], i2)
                if close_paths[i] >= hit_d:
                    close_paths[i] = hit_d
                    # line was hit earlier
                    if close_paths[i-1] < d2: continue
                    close_paths[i-1] = d2
                    # new shortest, or it was hit earlier but that intersection was the closest so far
                    if min(d2, hit_d) < close[0] or paths[close[3]] == path3:
                        close = [min(d2, hit_d), i2, i-1, i, 1]
        # add closed polygon to polygons
        # close = [dist, intersection, index of starting path, index of hit path, inner side of starting path]
        # prevent extra points in polygons if the intersection is not a new point
        inter_at_end = close[1] == paths[close[2]][0][-2] or close[1] == paths[close[3]][0][-2]
        if inter_at_end: polygons.append(paths[close[2]][close[4]][:-1] + paths[close[3]][abs(close[4]-1)][-2::-1])
        else: polygons.append(paths[close[2]][close[4]][:-1] + [close[1]] + paths[close[3]][abs(close[4]-1)][-2::-1])
        # update paths: delete removed and update sides of remaining
        # find the lines away from the paths that intersected
        d = close[3] - close[2]
        # first point of the outer side of each path
        l1_1, l2_1 = paths[close[2]][abs(close[4]-1)][0], paths[close[3]][close[4]][0]
        # second point of the line
        in1, in2 = polygon.index(l1_1), polygon.index(l2_1)
        l1_2, l2_2 = polygon[(in1 - d)%len(polygon)], polygon[(in2 + d)%len(polygon)]
        # swap lines if necessary to make them in clockwise order
        if d < 0: l1_1, l1_2, l2_1, l2_2 = l2_1, l2_2, l1_1, l1_2
        # update side of original path
        paths[close[2]][close[4]] = paths[close[3]][close[4]]
        # intersect the lines to find the point to start the bisector at
        inter = intersection((l1_1, l1_2), (l2_1, l2_2))
        # point close[1] translated by l1
        add = translate(close[1], [l1_1, l1_2])
        # find y intercepts (checking for vertical beforehand)
        if close_enough(l1_2[0], l1_1[0]): l1_b = (1<<16) - 128
        else: l1_b = l1_1[1] - ((l1_2[1] - l1_1[1])*l1_1[0])/(l1_2[0] - l1_1[0])
        if close_enough(l2_2[0], l2_1[0]): l2_b = (1<<16) + 128
        else: l2_b = l2_1[1] - ((l2_2[1] - l2_1[1])*l2_1[0])/(l2_2[0] - l2_1[0])
        # check for precision error
        if inter and math.dist(close[1], inter) > 1<<16: inter = False
        if inter:
            # check if the intersection is in front or behind of the path, by checking if the edges would be convex
            if angle_leq(translate(l1_2, [l1_1, l2_1]), l2_1, l2_2): inter = one_dist_to(-1, close[1], inter)
            b = [close[1], inter]
        # remaining edges were parallel but still intersect (checking if y intercepts are close enough)
        elif close_enough(l1_b, l2_b):
            perpendicular = one_dist_to(1, close[1], add, added_rotation=90, degrees=True)
            b = [close[1], intersection([close[1], perpendicular], [l1_1, l1_2])]
        # remaining edges were parallel
        else: b = [close[1], add]
        # remove duplicates
        if paths[close[2]][0][-2] == close[1]: paths[close[2]][0].pop(-2)
        if paths[close[2]][1][-2] == close[1]: paths[close[2]][1].pop(-2)
        # update path
        paths[close[2]][0][-1] = close[1]; paths[close[2]][0].append(b[1])
        paths[close[2]][1][-1] = close[1]; paths[close[2]][1].append(b[1])
        # remove merged path
        paths.pop(close[3])
    # add last two polygons to polygons
    polygons.append(paths[0][0][:-1] + paths[1][1][-2::-1])
    polygons.append(paths[0][1][:-1] + paths[1][0][-2::-1])
    # find greater endpoint of the line segment for each polygon
    edges = []
    for poly in polygons:
        p1, p2 = poly[0], poly[-1]
        i1, i2 = polygon.index(p1), polygon.index(p2)
        if len(polygon)-1 in [i1, i2] and 0 in [i1, i2]: edges.append(0)
        else: edges.append(max(i1, i2))
    # sort polygons into matching order
    ret = [[] for _ in polygons]
    for i, index in enumerate(edges):
        ret[index] = polygons[i]
    return ret

def miter(polygon, distance, pointy=False, amount=8):
    """Returns a mitered polygon of the given distance."""
    if not polygon: return polygon
    offset = pc.PyclipperOffset(miter_limit=amount)
    if not pointy: join_type = pc.JT_SQUARE
    else: join_type = pc.JT_MITER
    offset.AddPath(pc.scale_to_clipper(polygon), join_type, pc.ET_CLOSEDPOLYGON)

    ret = offset.Execute(pc.scale_to_clipper(distance))
    return pc.scale_from_clipper(ret)

def clean(polygon):
    """Returns a polygon with very close vertices merged."""
    # miter then unmiter to remove thin bits
    m = miter(polygon, -1/10000, pointy=True, amount=2**31)
    if not m: return []
    polygon = miter(m[0], 1/10000, pointy=True, amount=2**31)[0]
    return pc.scale_from_clipper(pc.CleanPolygon(pc.scale_to_clipper(polygon), 16))

def poly_intersection(polygon1, polygon2)->"list":
    """Returns the polygon created by the intersection of the two polygons."""
    if not polygon1 or not polygon2: return []
    # miter the polygons a bit because this thing can't even do its job properly
    polygon1 = miter(polygon1, 1/10000, True)[0]
    polygon2 = miter(polygon2, 1/10000, True)[0]
    clipper = pc.Pyclipper()
    clipper.AddPath(pc.scale_to_clipper(polygon1), pc.PT_SUBJECT, True)
    clipper.AddPath(pc.scale_to_clipper(polygon2), pc.PT_CLIP, True)

    ret = clipper.Execute(pc.CT_INTERSECTION, pc.PFT_EVENODD, pc.PFT_EVENODD)
    ret: list = pc.scale_from_clipper(ret)

    # didn't overlap
    if ret == []:
        return ret
    # holes
    if len(ret) > 1:
        # return biggest polygon
        ret.sort(key=lambda x: abs(area(x)), reverse=True)
    return clean(ret[0])

def poly_subtraction(polygon, subtracted_polygons: list)->"list":
    """Returns the polygon created by subtracting the list of polygons from the first polygon."""
    if not polygon or not subtracted_polygons: return polygon
    clipper = pc.Pyclipper()
    clipper.AddPath(pc.scale_to_clipper(polygon), pc.PT_SUBJECT, True)
    for sub_poly in subtracted_polygons:
        # miter the subtracted polygons a bit because this thing can't even do its job properly
        sub_poly = miter(sub_poly, 1/1000, True)[0]
        clipper.AddPath(pc.scale_to_clipper(sub_poly), pc.PT_CLIP, True)

    ret = clipper.Execute(pc.CT_DIFFERENCE, pc.PFT_NONZERO, pc.PFT_NONZERO)
    ret: list = pc.scale_from_clipper(ret)

    # nothing left
    if ret == []:
        return ret
    # holes
    if len(ret) > 1:
        # return biggest polygon
        ret.sort(key=lambda x: abs(area(x)), reverse=True)
    # ensure ret is a shape
    if abs(area(ret[0])) < 1/10000: return []
    return clean(ret[0])

def poly_center(polygon)->"tuple[float, float]":
    """Finds the centroid for the given polygon."""
    sum_x, sum_y, sum_weight = 0, 0, 0

    for i, p3 in enumerate(polygon):
        # get three consecutive points
        p1 = polygon[i-2]
        p2 = polygon[i-1]
        # weight the middle point's addition to the center by the length of its edges
        weight = math.dist(p1, p2) + math.dist(p2, p3)
        sum_x += p2[0]*weight
        sum_y += p2[1]*weight
        sum_weight += weight
        
    # divide the center by the total weight of the sum
    return sum_x/sum_weight, sum_y/sum_weight

def line_clip(line, clip)->"list":
    """Returns the part of the line inside the polygon."""
    clipper = pc.Pyclipper()
    clipper.AddPath(pc.scale_to_clipper(clip), pc.PT_CLIP, True)
    clipper.AddPath(pc.scale_to_clipper(line), pc.PT_SUBJECT, False)

    tree = clipper.Execute2(pc.CT_INTERSECTION, pc.PFT_EVENODD, pc.PFT_EVENODD)
    ret = [node.Contour for node in tree.Childs]
    ret = pc.scale_from_clipper(ret)

    # nothing left
    if ret == [] or math.dist(ret[0][0], ret[0][1]) < math.dist(line[0], line[1])/(1<<10):
        return []
    # holes
    if len(ret) > 1:
        print("Shapes created a hole")
        # return longest line
        ret.sort(key=lambda x: math.dist(x[0],x[1]), reverse=True)
    # make sure the line is in the same direction
    a1 = angle(line[0], line[1])
    a2 = angle(ret[0][0], ret[0][1])
    if not close_enough(a1, a2): return ret[0][::-1]
    return ret[0]

def line_subtraction(line, subtracted_line):
    """Finds the leftover line if the area from the start of the lines up to the end of the subtracted line is removed.
    
    The returned line will naturally be longer if the subtracted line points in the opposite direction of the line."""
    # make their starting points match
    moved_sub_end = translate(subtracted_line[1], [subtracted_line[0], line[0]])
    # rotate around the starting point so that the line has angle 0
    a = angle(line[0], line[1])
    moved_sub_end, moved_line_end = rot_around(moved_sub_end, line[0], -a), rot_around(line[1], line[0], -a)
    # don't return what should be negative lines
    if moved_sub_end[0] >= moved_line_end[0]: return []
    # use just x values to find the subtraction
    sub_line =  [[moved_sub_end[0], moved_line_end[1]], moved_line_end]
    # rotate the result back to its original angle
    return [rot_around(sub_line[0], line[0], a), rot_around(sub_line[1], line[0], a)]

def on_edge(polygon, edge_polygon, other_edge_polygons: list)->"bool":
    """Returns whether or not a polygon contains an edge of another polygon."""
    # make the shape very slightly bigger
    polygon = miter(polygon, 1/(1<<16))
    offset = pc.PyclipperOffset()
    offset.AddPath(pc.scale_to_clipper(polygon), pc.JT_SQUARE, pc.ET_CLOSEDPOLYGON)

    bigger = offset.Execute(1)
    bigger = pc.scale_from_clipper(bigger)[0]
    
    # check each edge for intersection with the shape
    # keep track of edges with any length
    edges = [[]]
    for n, point1 in enumerate(edge_polygon):
        point2 = edge_polygon[n-1]
        inside = line_clip([point1, point2], bigger)
        if inside:
            length = math.dist(inside[0], inside[1])
            edges[0].append((n, length))
    # include edges of other passed shapes in the check
    for i, edgeList in enumerate(other_edge_polygons):
        edges.append([])
        for n, point1 in enumerate(edgeList):
            point2 = edgeList[n-1]
            inside = line_clip([point1, point2], bigger)
            if inside:
                length = math.dist(inside[0], inside[1])
                edges[i].append((n, length))
    # sort edges so that the longest is first
    for l in edges:
        l.sort(key=lambda x:x[1], reverse=True)
        # only return the edge index
        l = [e[0] for e in l]
    return not edges == [[]]

def inside(point, polygon)->"bool":
    """Returns if a point is inside a polygon."""
    return not pc.PointInPolygon(pc.scale_to_clipper(point), pc.scale_to_clipper(polygon)) == 0

def offset_of_type(square_side_length, point1, point2, point3, type, mit_p2=None, reverse=False)->"float":
    """Finds the offset from a miter that a shape would require to fit in the corner made by the given three points.
    
    The points must be in clockwise order around the polygon, or counterclockwise if reverse == True."""
    # rotate around p2 such that p1-p2 line is horizontal
    a = angle(point1, point2)
    point1, point2, point3 = [rot_around(p, point2, -a) for p in [point1,point2,point3]]
    if reverse: point3[1] = -point3[1]
    if mit_p2: mit_p2 = rot_around(mit_p2, point2, -a)
    # find the angle difference of p2-p1 and p2-p3
    angle_dif = angle(point2, point3) + math.pi
    # find the x value that the offset is from if not given
    if mit_p2: mit_x = mit_p2[0]
    else: mit_x = point2[0] - square_side_length/(2*math.tan(angle_dif/2))
    # find the x value if aligned touching the corner
    align_x = point2[0] - square_side_length/2
    # x value of the edge of a square in the corner
    line_x = point2[0] - square_side_length/math.tan(angle_dif)
    if type == "sharp_triangle":
        if angle_dif >= 0.463647609: return mit_x - align_x + square_side_length/2
        return mit_x - (line_x + square_side_length)
    elif type == "triangle":
        if angle_dif >= math.pi/4: return mit_x - align_x
        return mit_x - (line_x + square_side_length/2)
    elif type == "square":
        if angle_dif >= math.pi/2: return mit_x - align_x
        return mit_x - (line_x - square_side_length/2)
    else: return 0

def miter_edge(polygon, square_side_length, edge_index):
    """Returns one edge of a miter."""
    # make the polygon clockwise and update the edge index if needed
    if area(polygon) < 0: polygon = polygon[::-1]; edge_index = len(polygon) - edge_index - 1
    # get the part of the straight skeleton with the edge
    skel = straight_skeleton(polygon)
    edge_poly = skel[edge_index]
    # get basic miter
    mits = miter(polygon, -square_side_length/2, pointy=True)
    for mit in mits:
        # ensure miter polygon is clockwise
        if area(mit) < 0: mit = mit[::-1]
        # return if a line is inside the edge's polygon in the straight skeleton
        for i, p2 in enumerate(mit):
            p1 = mit[i-1]
            l = line_clip([p1,p2], edge_poly)
            if l: return mit[i-1], mit[i]
    return []

def offset_miter_edge(polygon, square_side_length, edge_index, type, flip=False):
    """Returns one edge of a miter, offset if necessary for a shape of the given type to fit."""
    # make the polygon clockwise and update the edge index if needed
    if area(polygon) < 0: polygon = polygon[::-1]; edge_index = len(polygon) - edge_index - 1
    # find basic miter
    mits = miter(polygon, -square_side_length/2, pointy=True)
    # find the edge in the miter
    line = miter_edge(polygon, square_side_length, edge_index)
    if not line: return []
    mit = None
    line_index = None
    for m in mits:
        # ensure miter polygon is clockwise
        if area(m) < 0: m = m[::-1]
        for i, p in enumerate(m):
            if p == line[1]: mit = m; line_index = (i+1)%len(m)
    if not mit: return None
    # get the points on mit around the line
    p1, p2, p3, p4 = mit[line_index-3], mit[line_index-2], mit[line_index-1], mit[line_index]
    # get the points on the polygon around the line
    o_p1, o_p2, o_p3, o_p4 = polygon[edge_index-2], polygon[edge_index-1], polygon[edge_index], polygon[(edge_index+1)%len(polygon)]
    # find the pointy side of the triangle and set the other side to find the offset like a square
    type1, type2 = type if flip else "square", type if not flip else "square"
    # get offsets
    off1, off2 = offset_of_type(square_side_length, o_p3, o_p2, o_p1, type1, p2, True), offset_of_type(square_side_length, o_p2, o_p3, o_p4, type2, p3)
    mit_off1, mit_off2 = offset_of_type(square_side_length, p1, p2, p3, type1), offset_of_type(square_side_length, p2, p3, p4, type2)
    off1 = max(off1, mit_off1); off2 = max(off2, mit_off2)
    # adjust for extra length if the shape is a sharp triangle
    if type1 == "sharp_triangle" and angle_leq(p2, p3, p4): off2 += square_side_length/2
    if type2 == "sharp_triangle" and angle_leq(p1, p2, p3): off1 += square_side_length/2
    # make sure line is long enough
    line_length = math.dist(p2, p3)
    if off1 + off2 >= line_length: return []
    return [one_dist_to(off1, p2, p3), one_dist_to(off2, p3, p2)]

def offset_miter(polygon, square_side_length):
    """Returns the miter of a polygon, with the corners offset if necessary for a square to fit."""
    # make the polygon clockwise
    if area(polygon) < 0: polygon = polygon[::-1]
    # get the edge of the miter for each edge, with offset
    edges = [[] for _ in polygon]
    for i in range(len(polygon)):
        edges[i] = offset_miter_edge(polygon, square_side_length, i, "square")
    ret_polygon = []
    # add each edge to the new polygon
    for i, edge2 in enumerate(edges):
        if not edge2: continue
        # find last edge
        j = 1
        edge1 = edges[i-j]
        while not edge1:
            j += 1
            edge1 = edges[i-j]
        if close_enough(edge1, edge2): return []
        # parallel, somehow
        inter = intersection(edge1, edge2)
        if not inter: ret_polygon += edge2
        # no offset
        elif close_enough(edge1[1], edge2[0]): ret_polygon.append(edge2[1])
        else:
            dist = math.dist(edge1[1], inter)
            # find the point the offset distance inside the polygon
            inside_point = one_dist_to(dist, edge2[0], edge2[1], added_rotation=angle(edge1[1], edge1[0]) - angle(edge2[0], edge2[1]))
            ret_polygon += [inside_point] + edge2
    return ret_polygon

if __name__ == "__main__":
    #new_poly = poly_subtraction([[1,1],[4,2],[3,3],[0,3]],[[5,5]])
    shape = [[4, 3], [6, 7], [5, 10], [8, 9], [8, 4], [6, 4]][::-1]
    shape = [[10, 14], [6, 14], [8, 12], [3, 12], [3, 5], [5, 3], [10, 4], [11, 5]][::-1]
    #shape = [[1, 1], [14, 1], [14, 5], [8, 5], [7.5, 1.2], [7, 5], [1, 5]]
    #shape = [[1, 3], [3, 3], [2, 1], [4, 1], [5, 2], [8, 2], [9, 1], [11, 1], [10, 3], [12, 3], [6.5, 15]][::-1]
    #shape = [[3, 3], [12, 3], [9, 3.5], [10, 10], [6, 10]]
    #shape = [[60.0, 30.0], [30.0, 30.0], [30.0, 75.0], [75.0, 75.0], [75.0, 45.0], [60.0, 45.0]]
    #shape = poly_subtraction([[150, 120], [150, 165], [225, 201], [215, 118]], [(200.64725345549775, 118.44162297066018), (215.64015790164754, 117.98030283385557), (216.10147803845214, 132.97320728000537), (201.10857359230235, 133.43452741680997)])
    shape = [[225.0, 126.0], [220.78651870042086, 127.23321403888986], [224.99999999953434, 141.62927514314651], [210.60393889481202, 145.84275644226], [206.39045759569854, 131.44669533800334], [184.0, 138.0], [150.0, 165.0], [225.0, 201.0]]
    shape = [[225.0, 126.0], [224.09257409349084, 126.05499550933018], [224.99999999953434, 141.02752295834944], [210.02747255051509, 141.93494886439294], [209.12004664447159, 126.96242141537368], [159.0, 130.0], [150.0, 165.0], [225.0, 201.0]]
    shape = [[140.0, 118.0], [164.0, 216.0], [225.0, 201.0], [196.34718213928863, 127.98152867751196], [195.6669565429911, 137.16457422962412], [180.7079402259551, 136.05649894708768], [181.81601550849155, 121.09748263005167]]
    #shape = [[10, 1], [9, 7], [7, 7], [6, 3], [5, 7], [3, 7], [2, 1]]
    shape = [[6, 5], [5, 10], [10, 10], [12, 5]]
    #shape = [[2, 2], [9, 2], [7, 7], [2.1, 3]]
    #shape = [[3, 2], [2.5, 3], [7, 5], [9, 2]][::-1]
    polygons = straight_skeleton(shape)
    img = Img(2048)
    scale = 128
    shape = pc.scale_to_clipper(shape, scale)
    img.draw_polygon(shape, width=5, outline=[0,0,0])
    l = offset_miter_edge(shape, 128*2, 0, "square")
    img.draw_line(l)
    from base_shapes import *
    #img.draw_polygon(shape_at(Triangle, 256, l[0], angle(shape[1], shape[2]), True))
    #img.draw_polygon(shape_at(Triangle, 256, l[1], angle(shape[1], shape[2]), True))
    #p = offset_miter(shape, 256)
    #img.draw_polygon(p)
    for p in polygons:
        img.draw_polygon(pc.scale_to_clipper(p, scale), fill=None, outline=[10,200,10])
    
    img.show()