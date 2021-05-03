from base_shapes import *
from clipper import *
from util import *
from visualize import *

def find_corner_triangles(start_corners, end_corners):
    s_triangles = [[] for _ in start_corners]; e_triangles = [[] for _ in start_corners] # each element is the two triangles for the corresponding corner
    # triangle: type, side_length, position, rotation, flip
    for i, (s_p3, e_p3) in enumerate(zip(start_corners, end_corners)):
        s_p1, s_p2 = start_corners[i-2], start_corners[i-1]
        e_p1, e_p2 = end_corners[i-2], end_corners[i-1]
        if angle_leq(s_p1, s_p2, s_p3, 22.4999, degrees=True) or angle_leq(e_p1, e_p2, e_p3, 22.4999, degrees=True): # needs smallest triangle
            # find placement for triangle
            s_off_e1 = offset_miter_edge(start_corners, smallest_scale, (i-1)%len(start_corners), "sharp_triangle")
            s_off_e2 = offset_miter_edge(start_corners, smallest_scale, i, "sharp_triangle", True)
            e_off_e1 = offset_miter_edge(end_corners, smallest_scale, (i-1)%len(end_corners), "sharp_triangle")
            e_off_e2 = offset_miter_edge(end_corners, smallest_scale, i, "sharp_triangle", True)
            # shape is too small
            if not s_off_e1 or not s_off_e2: return False
            if not e_off_e1 or not e_off_e2: return False
            # add to list
            s_triangles[i-1].append(["sharp_triangle", smallest_scale, s_off_e1[1], angle(s_off_e1[1], s_off_e1[0]), False])
            s_triangles[i-1].append(["sharp_triangle", smallest_scale, s_off_e2[0], angle(s_off_e2[1], s_off_e2[0]), True])
            e_triangles[i-1].append(["sharp_triangle", smallest_scale, e_off_e1[1], angle(e_off_e1[1], e_off_e1[0]), False])
            e_triangles[i-1].append(["sharp_triangle", smallest_scale, e_off_e2[0], angle(e_off_e2[1], e_off_e2[0]), True])
            continue
        elif angle_leq(s_p1, s_p2, s_p3, 44.999, degrees=True) or angle_leq(e_p1, e_p2, e_p3, 44.999, degrees=True): # largest sharp triangle necessary
            type = "sharp_triangle"
        elif angle_leq(s_p1, s_p2, s_p3, 89.999, degrees=True) or angle_leq(e_p1, e_p2, e_p3, 89.999, degrees=True): # largest regular triangle necessary
            type = "triangle"
        else: continue # no triangles necessary
        # prime with smallest triangles
        s_off_e1 = []; t_s_off_e1 = offset_miter_edge(start_corners, smallest_scale, (i-1)%len(start_corners), type)
        s_off_e2 = []; t_s_off_e2 = offset_miter_edge(start_corners, smallest_scale, i, type, True)
        e_off_e1 = []; t_e_off_e1 = offset_miter_edge(end_corners, smallest_scale, (i-1)%len(end_corners), type)
        e_off_e2 = []; t_e_off_e2 = offset_miter_edge(end_corners, smallest_scale, i, type, True)
        # shape is too small
        if not t_s_off_e1 or not t_s_off_e2: return False
        if not t_e_off_e1 or not t_e_off_e2: return False
        # find largest triangle for first edge
        mult = 1
        while t_s_off_e1 and t_e_off_e1:
            mult *= 2
            s_off_e1 = t_s_off_e1
            t_s_off_e1 = offset_miter_edge(start_corners, smallest_scale*mult, (i-1)%len(start_corners), type)
            e_off_e1 = t_e_off_e1
            t_e_off_e1 = offset_miter_edge(end_corners, smallest_scale*mult, (i-1)%len(end_corners), type)
        mult /= 2
        s_triangles[i-1].append([type, smallest_scale*mult, s_off_e1[1], angle(s_off_e1[1], s_off_e1[0]), False])
        e_triangles[i-1].append([type, smallest_scale*mult, e_off_e1[1], angle(e_off_e1[1], e_off_e1[0]), False])
        # find largest triangle for second edge
        mult = 1
        while t_s_off_e2 and t_e_off_e2:
            mult *= 2
            s_off_e2 = t_s_off_e2
            t_s_off_e2 = offset_miter_edge(start_corners, smallest_scale*mult, i, type, True)
            e_off_e2 = t_e_off_e2
            t_e_off_e2 = offset_miter_edge(end_corners, smallest_scale*mult, i, type, True)
        mult /= 2
        s_triangles[i-1].append([type, smallest_scale*mult, s_off_e2[0], angle(s_off_e2[1], s_off_e2[0]), True])
        e_triangles[i-1].append([type, smallest_scale*mult, e_off_e2[0], angle(e_off_e2[1], e_off_e2[0]), True])
    return s_triangles, e_triangles

def weird_crop(line, outer_line, offsets, max_dist): # helper for find_edge_placement
    newline = deepcopy(line)
    if sum(offsets) >= math.dist(outer_line[0], outer_line[1]) - 1/10000: return False
    # first points of edges
    d = line[0][0] - (outer_line[0][0] + offsets[0])
    if d < 0: newline[0][0] = outer_line[0][0] + offsets[0]
    elif d > max_dist + 1/10000: return False
    # last points of edges
    d = (outer_line[1][0] - offsets[1]) - line[1][0]
    if d < 0: newline[1][0] = outer_line[1][0] - offsets[1]
    # make sure some edge is left
    if newline[1][0] - newline[0][0] < 1/10000: return False
    # don't check for max distance on end edge because it wouldn't be placed there
    return newline

def find_edge_placement(start_corners, end_corners, edge_index, start_offs, end_offs):
    # start_offs in same order as line, represent length of end triangles/squares into the edge
    start_corner_edge, end_corner_edge = [start_corners[edge_index-1], start_corners[edge_index]], [end_corners[edge_index-1], end_corners[edge_index]]
    # find angles to rotate lines by
    start_angle, end_angle = angle(start_corner_edge[0], start_corner_edge[1]), angle(end_corner_edge[0], end_corner_edge[1])
    # rotate all points around the first point of the edge clockwise
    # second point in edge will have higher x
    rot_start_corners = []; rot_end_corners = []
    for p in start_corners:
        rot_start_corners.append(rot_around(p, start_corner_edge[0], -start_angle))
    for p in end_corners:
        rot_end_corners.append(rot_around(p, end_corner_edge[0], -end_angle))
    # update corner edges
    start_corner_edge, end_corner_edge = [rot_start_corners[edge_index-1], rot_start_corners[edge_index]], [rot_end_corners[edge_index-1], rot_end_corners[edge_index]]
    # find largest square that fits in both
    t_start_edge = offset_miter_edge(rot_start_corners, smallest_scale, edge_index, "square")
    t_end_edge = offset_miter_edge(rot_end_corners, smallest_scale, edge_index, "square")
    # no space for anything
    if not t_start_edge or not t_end_edge: return False
    # crop miter edges based on filled area
    t_start_edge = weird_crop(t_start_edge, start_corner_edge, start_offs, smallest_scale/2)
    t_end_edge = weird_crop(t_end_edge, end_corner_edge, end_offs, smallest_scale/2)
    # check if edge is filled up already
    if not t_start_edge and not t_end_edge: return False
    # increase square size up until no space is left
    mult = 1
    starting_loop = True; s_miter = True; e_miter = True
    while starting_loop or (s_miter and e_miter and (t_start_edge or t_end_edge)):
        starting_loop = False
        mult *= 2
        # set prevous size fits
        start_edge = t_start_edge
        end_edge = t_end_edge
        t_start_edge = offset_miter_edge(rot_start_corners, smallest_scale*mult, edge_index, "square"); s_miter = t_start_edge
        t_end_edge = offset_miter_edge(rot_end_corners, smallest_scale*mult, edge_index, "square"); e_miter = t_end_edge
        # crop miter edges based on filled area
        if t_start_edge: t_start_edge = weird_crop(t_start_edge, start_corner_edge, start_offs, smallest_scale*mult/2)
        if t_end_edge: t_end_edge = weird_crop(t_end_edge, end_corner_edge, end_offs, smallest_scale*mult/2)
    mult /= 2
    # find placement position if an edge is filled
    if not start_edge: start_edge = [offset_miter_edge(rot_start_corners, smallest_scale*mult, edge_index, "square")[1]]*2
    if not end_edge: end_edge = [offset_miter_edge(rot_end_corners, smallest_scale*mult, edge_index, "square")[1]]*2
    # find farthest (so most filled area) placement for each side
    # min of ideal farthest x value and calculated maximum x value
    start_low_x = min(start_corner_edge[0][0] + smallest_scale*mult/2 + start_offs[0], start_edge[1][0])
    end_low_x = min(end_corner_edge[0][0] + smallest_scale*mult/2 + end_offs[0], end_edge[1][0])
    # turn everything into values to be returned
    new_s_off0 = start_low_x + smallest_scale*mult/2 - start_corner_edge[0][0]
    new_e_off0 = end_low_x + smallest_scale*mult/2 - end_corner_edge[0][0]
    start_pos = rot_around([start_low_x, start_edge[0][1]], start_corner_edge[0], start_angle)
    end_pos = rot_around([end_low_x, end_edge[0][1]], end_corner_edge[0], end_angle)
    # return placements and new offsets
    return mult, start_pos, end_pos, [new_s_off0, start_offs[1]], [new_e_off0, end_offs[1]]

def maximize_area(scale, start_position, rotation, search_space, shape_to_fill):
    # increments to search by
    searches = iter((1/10, 1/1_000, 1/1_000_000))
    bounds_search = 1
    # values for searching
    directions = ((1, 0), (0, 1), (-1, 0), (0, -1))
    # find a start position that contains some area
    position = list(start_position)
    valid_start = abs(area(poly_intersection(shape_at(Square, scale, position, rotation), shape_to_fill))) > 1/10000
    # loop over all values in a grid, spaced in increments of bounds_search, that are inside the search space to find a starting position containing area
    min_x, min_y, max_x, max_y = bounds([search_space])
    x_m, y_m = 0, 0
    while not valid_start:
        # increment x
        position[0] = min_x + bounds_search*x_m; x_m += 1
        # reset x and increment y
        if position[0] > max_x:
            position[0] = min_x; x_m = 0
            position[1] = min_y + bounds_search*y_m; y_m += 1
        # searched entire area
        if position[1] > max_y:
            return False
        # check if now valid
        valid_start = abs(area(poly_intersection(shape_at(Square, scale, position, rotation), shape_to_fill))) > 1/10000
    # find center
    centroid = poly_center(shape_to_fill)
    # starting area
    ret_area = abs(area(poly_intersection(shape_at(Square, scale, position, rotation), shape_to_fill)))
    search = next(searches)
    while search:
        # check the new area in each direction and use the position if greater
        for d in directions:
            new_pos = [position[0] + d[0]*search, position[1] + d[1]*search]
            # ensure it remains inside the search space
            if not inside(new_pos, search_space): continue
            new_area = abs(area(poly_intersection(shape_at(Square, smallest_scale*scale, new_pos, rotation), shape_to_fill)))
            # weight area based on distance from center
            dist = math.dist(position, centroid)
            min_mult = 0.9; max_mult = 1.1
            # if dist = 0: ret_area *= min_mult, if dist = ideal_dist: ret_area *= 1, if dist -> infinity: ret_area *= max_mult
            ideal_dist = math.sqrt(abs(area(shape_to_fill)))/2
            b = 1/(max_mult-min_mult); a = 1/(max_mult-1) - b
            new_area *= (-ideal_dist)/(a*dist+b*ideal_dist) + max_mult
            # compare areas of old and new positions
            if new_area > ret_area: ret_area = new_area; position = new_pos; break
        # move to a smaller search if all directions areas are smaller
        search = next(searches, False)
    if ret_area < 1/10000: return False
    return position

def find_inner_placements(start_corners, end_corners, start_minus_corners, end_minus_corners):
    # note: I hardcoded squares because I'm smart like that
    # find straight skeletons of shapes
    start_skel, end_skel = straight_skeleton(start_corners), straight_skeleton(end_corners)
    # find centroids of polygons
    start_center, end_center = poly_center(start_corners), poly_center(end_corners)
    # find the offset miters of the max corners for a global search space
    t_start_mit, t_end_mit = offset_miter(start_corners, smallest_scale), offset_miter(end_corners, smallest_scale)
    # no space for even the smallest square
    if not t_start_mit or not t_end_mit: return []
    mult = 1; starting_loop = True
    while starting_loop or (t_start_mit and t_end_mit):
        starting_loop = False
        mult *= 2
        start_mit = t_start_mit
        end_mit = t_end_mit
        t_start_mit = offset_miter(start_corners, smallest_scale*mult)
        t_end_mit = offset_miter(end_corners, smallest_scale*mult)
    mult /= 2
    # find sectors that contain the miter
    start_search_spaces = []; end_search_spaces = []
    for sector in start_skel:
        start_search_spaces.append(poly_intersection(sector, start_mit))
    for sector in end_skel:
        end_search_spaces.append(poly_intersection(sector, end_mit))
    # find placements for squares until no space is left
    placed_shapes = []
    while start_minus_corners or end_minus_corners:
        for i, (start_search_space, end_search_space) in enumerate(zip(start_search_spaces, end_search_spaces)):
            new_shape = []
            # only work with search spaces in both
            if not start_search_space or not end_search_space: continue
            start_rot, end_rot = angle(start_corners[i], start_corners[i-1]), angle(end_corners[i], end_corners[i-1])
            # search for placement if necessary
            if start_minus_corners:
                # find the best position for the area
                max_pos = maximize_area(mult, poly_center(start_search_space), start_rot, start_search_space, start_minus_corners)
                if max_pos:
                    new_shape += [max_pos, start_rot]
                    start_minus_corners = poly_subtraction(start_minus_corners, [shape_at(Square, smallest_scale*mult, max_pos, start_rot)])
                else: continue
            else:
                # find closest point in search space to the center
                min_point = []
                for point in start_search_space:
                    d = math.dist(point, start_center)
                    if not min_point or d < min_point[1]:
                        min_point = [point, d]
                new_shape += [min_point[0], start_rot]
            if end_minus_corners:
                # find the best position for the area
                max_pos = maximize_area(mult, poly_center(end_search_space), end_rot, end_search_space, end_minus_corners)
                if max_pos:
                    new_shape += [max_pos, end_rot]
                    end_minus_corners = poly_subtraction(end_minus_corners, [shape_at(Square, smallest_scale*mult, max_pos, end_rot)])
                else: continue
            else:
                # find closest point in search space to the center
                min_point = []
                for point in end_search_space:
                    d = math.dist(point, end_center)
                    if not min_point or d < min_point[1]:
                        min_point = [point, d]
                new_shape += [min_point[0], end_rot]
            placed_shapes.append(new_shape)
            break
    return placed_shapes, mult

class Combination:
    def __init__(self, corners, max_corners):
        self.corners = corners
        self.start_shapes = []
        self.moved_shapes = []
    
    def find_shapes(self, new_corners):
        shapes = []
        s_triangles, e_triangles = find_corner_triangles(self.corners, new_corners)

def find_shapes(start_corners, end_corners):
    start_shapes, end_shapes = [], []
    start_offs_s = [[0,0] for _ in start_corners]
    end_offs_s = [[0,0] for _ in end_corners]
    # find and append the corner triangles and the offsets
    s_triangles, e_triangles = find_corner_triangles(start_corners, end_corners)
    for i, triangles in enumerate(s_triangles):
        if not triangles: continue
        if triangles[0][0] == "triangle":
            type = Triangle; m = 1
        else:
            type = SharpTriangle; m = 2
        triangle = triangles[0]
        start_shapes.append(shape_at(type, triangle[1], triangle[2], triangle[3], triangle[4]))
        start_offs_s[i][1] = triangle[1]*m
        triangle = triangles[1]
        start_shapes.append(shape_at(type, triangle[1], triangle[2], triangle[3], triangle[4]))
        start_offs_s[(i+1)%len(start_offs_s)][0] = triangle[1]*m
    for i, triangles in enumerate(e_triangles):
        if not triangles: continue
        if triangles[0][0] == "triangle":
            type = Triangle; m = 1
        else:
            type = SharpTriangle; m = 2
        triangle = triangles[0]
        end_shapes.append(shape_at(type, triangle[1], triangle[2], triangle[3], triangle[4]))
        end_offs_s[i][1] = triangle[1]*m
        triangle = triangles[1]
        end_shapes.append(shape_at(type, triangle[1], triangle[2], triangle[3], triangle[4]))
        end_offs_s[(i+1)%len(end_offs_s)][0] = triangle[1]*m
    # find and append all the edge placements
    for i, (s_offs, e_offs) in enumerate(zip(start_offs_s, end_offs_s)):
        still_space = find_edge_placement(start_corners, end_corners, i, s_offs, e_offs)
        while still_space:
            scale, s_pos, e_pos, s_offs[:], e_offs[:] = still_space
            s_rot, e_rot = angle(start_corners[i-1], start_corners[i]), angle(end_corners[i-1], end_corners[i])
            start_shapes.append(shape_at(Square, smallest_scale*scale, s_pos, s_rot))
            end_shapes.append(shape_at(Square, smallest_scale*scale, e_pos, e_rot))
            still_space = find_edge_placement(start_corners, end_corners, i, s_offs, e_offs)
    # find remaining space
    # miter to avoid corner shoving
    start_minus_corners, end_minus_corners = miter(start_corners, -smallest_scale, True), miter(end_corners, -smallest_scale, True)
    start_minus_corners, end_minus_corners = poly_subtraction(start_corners, start_shapes), poly_subtraction(end_corners, end_shapes)
    if start_minus_corners or end_minus_corners:
        placements, scale = find_inner_placements(start_corners, end_corners, start_minus_corners, end_minus_corners)
        for placement in placements:
            start_shapes.append(shape_at(Square, smallest_scale*scale, placement[0], placement[1]))
            end_shapes.append(shape_at(Square, smallest_scale*scale, placement[2], placement[3]))
    return start_shapes + end_shapes

if __name__ == "__main__":
    big_corners = [[30, 30], [30, 75], [75, 75], [75, 30]]
    big_shape = Combination(big_corners, max_corners=big_corners)
    s = Screen(500)
    s.add_polygons([big_corners, [[150, 120], [150, 165], [225, 201], [225, 126]]])
    s.add_poly_method(lambda x: find_shapes(x[0], x[1]), ((0,0),(0,1)))
    s.add_poly_method(lambda x: find_shapes(x[0], x[1]), ((0,0),(0,1),(1,0),(1,1)))
    run_screens()
    #start_pos, start_rot, end_pos, end_rot = big_shape.find_placement(rect, [[10, 0], [10, 15], [25, 17], [25, 2]])