from base_shapes import *
from clipper import *
from util import *
from visualize import *

def find_corner_triangles(start_corners, end_corners):
    s_triangles = [[] for _ in start_corners]; e_triangles = [[] for _ in start_corners] # each element is the two triangles for the corresponding corner
    # triangle: type, position, rotation, side length, flip, extra offset
    for i, (s_p3, e_p3) in enumerate(zip(start_corners, end_corners)):
        s_p1, s_p2 = start_corners[i-2], start_corners[i-1]
        e_p1, e_p2 = end_corners[i-2], end_corners[i-1]
        if angle_leq(s_p1, s_p2, s_p3, 0.46364, degrees=False) or angle_leq(e_p1, e_p2, e_p3, 0.46364, degrees=False): # needs smallest triangle
            # find placement for triangle
            s_off_e1 = offset_miter_edge(start_corners, smallest_scale, (i-1)%len(start_corners), "sharp_triangle")
            s_off_e2 = offset_miter_edge(start_corners, smallest_scale, i, "sharp_triangle", True)
            e_off_e1 = offset_miter_edge(end_corners, smallest_scale, (i-1)%len(end_corners), "sharp_triangle")
            e_off_e2 = offset_miter_edge(end_corners, smallest_scale, i, "sharp_triangle", True)
            # shape is too small
            if not s_off_e1 or not s_off_e2: return False
            if not e_off_e1 or not e_off_e2: return False
            # find the extra offsets
            s_extra_off = max(smallest_scale/math.tan((angle(s_p2, s_p3)%math.tau-angle(s_p2, s_p1)%math.tau)%math.tau) - smallest_scale*2, 0)
            e_extra_off = max(smallest_scale/math.tan((angle(e_p2, e_p3)%math.tau-angle(e_p2, e_p1)%math.tau)%math.tau) - smallest_scale*2, 0)
            # add to list
            s_triangles[i-1].append(["sharp_triangle", s_off_e1[1], angle(s_off_e1[1], s_off_e1[0]), smallest_scale, False, s_extra_off])
            s_triangles[i-1].append(["sharp_triangle", s_off_e2[0], angle(s_off_e2[1], s_off_e2[0]), smallest_scale, True, s_extra_off])
            e_triangles[i-1].append(["sharp_triangle", e_off_e1[1], angle(e_off_e1[1], e_off_e1[0]), smallest_scale, False, e_extra_off])
            e_triangles[i-1].append(["sharp_triangle", e_off_e2[0], angle(e_off_e2[1], e_off_e2[0]), smallest_scale, True, e_extra_off])
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
        s_triangles[i-1].append([type, s_off_e1[1], angle(s_off_e1[1], s_off_e1[0]), smallest_scale*mult, False, 0])
        e_triangles[i-1].append([type, e_off_e1[1], angle(e_off_e1[1], e_off_e1[0]), smallest_scale*mult, False, 0])
        # find largest triangle for second edge
        mult = 1
        while t_s_off_e2 and t_e_off_e2:
            mult *= 2
            s_off_e2 = t_s_off_e2
            t_s_off_e2 = offset_miter_edge(start_corners, smallest_scale*mult, i, type, True)
            e_off_e2 = t_e_off_e2
            t_e_off_e2 = offset_miter_edge(end_corners, smallest_scale*mult, i, type, True)
        mult /= 2
        s_triangles[i-1].append([type, s_off_e2[0], angle(s_off_e2[1], s_off_e2[0]), smallest_scale*mult, True, 0])
        e_triangles[i-1].append([type, e_off_e2[0], angle(e_off_e2[1], e_off_e2[0]), smallest_scale*mult, True, 0])
    return s_triangles, e_triangles

def touches_end(line, outer_line, offsets, max_dist): # helper for find_edge_placement
    # x value of the outer line with the offset
    off_x = outer_line[0][0] + offsets[0]
    # check if the start of the line isn't close enough to the offset start
    # check if the end of the line is greater than max_dist behind the offset start
    return line[0][0] - 1/10000 < off_x + max_dist, off_x - max_dist < line[1][0] - 1/10000

def find_edge_placement(start_corners, end_corners, edge_index, start_offs, end_offs):
    # start_offs in same order as line, represent length of end triangles/squares into the edge
    start_corner_edge, end_corner_edge = [start_corners[edge_index-1], start_corners[edge_index]], [end_corners[edge_index-1], end_corners[edge_index]]
    # find angles to rotate lines by
    start_angle, end_angle = angle(start_corner_edge[0], start_corner_edge[1]), angle(end_corner_edge[0], end_corner_edge[1])
    # rotate all points around the first point of the edge clockwise such that the edge is horizontal
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
    s_touches_end, s_new_area = touches_end(t_start_edge, start_corner_edge, start_offs, smallest_scale/2)
    e_touches_end, e_new_area = touches_end(t_end_edge, end_corner_edge, end_offs, smallest_scale/2)
    # check if both edges are filled up
    if sum(start_offs) > start_corner_edge[1][0]-start_corner_edge[0][0]-1/10000 and sum(end_offs) > end_corner_edge[1][0]-end_corner_edge[0][0]-1/10000:
        return False
    # idk how this could happen
    if not s_touches_end and not e_touches_end: return False
    # increase square size up until no space is left
    mult = 1
    starting_loop = True
    # ensure that:           squares fit at all in both         room at the end of edges           covers some new area
    while starting_loop or (t_start_edge and t_end_edge and s_touches_end and e_touches_end and (s_new_area or e_new_area)):
        starting_loop = False
        mult *= 2
        # set prevous size fits
        start_edge = t_start_edge
        end_edge = t_end_edge
        t_start_edge = offset_miter_edge(rot_start_corners, smallest_scale*mult, edge_index, "square")
        t_end_edge = offset_miter_edge(rot_end_corners, smallest_scale*mult, edge_index, "square")
        # check if they can be placed at the ends
        if t_start_edge: s_touches_end, s_new_area = touches_end(t_start_edge, start_corner_edge, start_offs, smallest_scale*mult/2)
        if t_end_edge: e_touches_end, e_new_area = touches_end(t_end_edge, end_corner_edge, end_offs, smallest_scale*mult/2)
    mult /= 2
    # find farthest (so most filled area) placement for each side
    # min of ideal farthest x value and calculated maximum x value (x value for the center)
    start_low_x = min(start_corner_edge[0][0] + smallest_scale*mult/2 + start_offs[0], start_edge[1][0])
    end_low_x = min(end_corner_edge[0][0] + smallest_scale*mult/2 + end_offs[0], end_edge[1][0])
    # turn everything into values to be returned
    new_s_off0 = start_low_x + smallest_scale*mult/2 - start_corner_edge[0][0]
    new_s_off0 = max(start_offs[0], new_s_off0)
    new_e_off0 = end_low_x + smallest_scale*mult/2 - end_corner_edge[0][0]
    new_e_off0 = max(end_offs[0], new_e_off0)
    start_pos = rot_around([start_low_x, start_edge[0][1]], start_corner_edge[0], start_angle)
    end_pos = rot_around([end_low_x, end_edge[0][1]], end_corner_edge[0], end_angle)
    # return placements and new offsets
    return mult, start_pos, end_pos, [new_s_off0, start_offs[1]], [new_e_off0, end_offs[1]]

def find_edge_placements(start_corners, end_corners, start_offs_s, end_offs_s):
    start_shapes, end_shapes = [], []
    for i, (s_offs, e_offs) in enumerate(zip(start_offs_s, end_offs_s)):
        still_space = find_edge_placement(start_corners, end_corners, i, s_offs, e_offs)
        while still_space:
            mult, s_pos, e_pos, s_offs[:], e_offs[:] = still_space
            s_rot, e_rot = angle(start_corners[i-1], start_corners[i]), angle(end_corners[i-1], end_corners[i])
            start_shapes.append([s_pos, s_rot, smallest_scale*mult])
            end_shapes.append([e_pos, e_rot, smallest_scale*mult])
            still_space = find_edge_placement(start_corners, end_corners, i, s_offs, e_offs)
    return start_shapes, end_shapes

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
    if not valid_start:
        min_x, min_y, max_x, max_y = bounds([search_space])
        x_m, y_m = 0, 0
        position = [min_x, min_y]
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
        if not inside(position, search_space): continue
        valid_start = abs(area(poly_intersection(shape_at(Square, scale, position, rotation), shape_to_fill))) > 1/10000
    # find center
    centroid = poly_center(shape_to_fill)
    # starting area
    min_mult = 0.99; max_mult = 1.01
    ideal_dist = math.sqrt(abs(area(shape_to_fill)))/2
    ret_area = abs(area(poly_intersection(shape_at(Square, scale, position, rotation), shape_to_fill)))
    # weight area based on distance from center
    dist = math.dist(position, centroid)
    # if dist = 0: ret_area *= min_mult, if dist = ideal_dist: ret_area *= 1, if dist -> infinity: ret_area *= max_mult
    b = 1/(max_mult-min_mult); a = 1/(max_mult-1) - b
    ret_area *= (-ideal_dist)/(a*dist+b*ideal_dist) + max_mult
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
            # if dist = 0: ret_area *= min_mult, if dist = ideal_dist: ret_area *= 1, if dist -> infinity: ret_area *= max_mult
            b = 1/(max_mult-min_mult); a = 1/(max_mult-1) - b
            new_area *= (-ideal_dist)/(a*dist+b*ideal_dist) + max_mult
            # compare areas of old and new positions
            if new_area > ret_area: ret_area = new_area; position = new_pos; break
        # move to a smaller search if all directions areas are smaller
        else: search = next(searches, False)
    if ret_area < 1/10000: return False
    return position

def find_inner_placement(start_corners, end_corners, start_minus_corners, end_minus_corners):
    # note: I hardcoded squares because I'm smart like that
    # find straight skeletons of shapes
    start_skel, end_skel = straight_skeleton(start_corners), straight_skeleton(end_corners)
    # find centroids of polygons
    start_center, end_center = poly_center(start_corners), poly_center(end_corners)
    # find the offset miters of the max corners for a global search space
    t_start_mit, t_end_mit = offset_miter(start_corners, smallest_scale), offset_miter(end_corners, smallest_scale)
    # check if offset miters intersect with the areas to be covered
    if start_minus_corners: start_covers = poly_intersection(t_start_mit, miter(start_minus_corners, smallest_scale/2)[0])
    else: start_covers = []
    if end_minus_corners: end_covers = poly_intersection(t_end_mit, miter(end_minus_corners, smallest_scale/2)[0])
    else: end_covers = []
    # no space for even the smallest square
    if not t_start_mit or not t_end_mit: return []
    mult = 1; starting_loop = True
    # check if:             fits at all in the shapes           can cover areas to be filled if there is any
    while starting_loop or (t_start_mit and t_end_mit and (start_covers or not start_minus_corners) and (end_covers or not end_minus_corners)):
        starting_loop = False
        mult *= 2
        # apply miters that worked
        start_mit = t_start_mit
        end_mit = t_end_mit
        # find new miters
        t_start_mit = offset_miter(start_corners, smallest_scale*mult)
        t_end_mit = offset_miter(end_corners, smallest_scale*mult)
        # check if offset miters intersect with the areas to be covered
        if start_minus_corners: start_covers = poly_intersection(t_start_mit, miter(start_minus_corners, smallest_scale*mult/2)[0])
        if end_minus_corners: end_covers = poly_intersection(t_end_mit, miter(end_minus_corners, smallest_scale*mult/2)[0])
    mult /= 2
    # find sectors that contain the miter
    start_search_spaces = []; end_search_spaces = []
    for sector in start_skel:
        start_search_spaces.append(poly_intersection(sector, start_mit))
    for sector in end_skel:
        end_search_spaces.append(poly_intersection(sector, end_mit))
    # find placements for squares until no space is left
    for i, (start_search_space, end_search_space) in enumerate(zip(start_search_spaces, end_search_spaces)):
        # only work with search spaces in both
        if not start_search_space or not end_search_space: continue
        start_rot, end_rot = angle(start_corners[i], start_corners[i-1]), angle(end_corners[i], end_corners[i-1])
        # search for placement if necessary
        if start_minus_corners:
            # find the best position for the area
            max_pos = maximize_area(mult, poly_center(start_search_space), start_rot, start_search_space, start_minus_corners)
            if max_pos:
                start_shape = [max_pos, start_rot, smallest_scale*mult]
                start_minus_corners = poly_subtraction(start_minus_corners, miter(shape_at(Square, smallest_scale*mult, max_pos, start_rot), 1/10, True))
            else: continue
        else:
            # find closest point in search space to the center
            min_point = []
            for point in start_search_space:
                d = math.dist(point, start_center)
                if not min_point or d < min_point[1]:
                    min_point = [point, d]
            start_shape = [min_point[0], start_rot, smallest_scale*mult]
        if end_minus_corners:
            # find the best position for the area
            max_pos = maximize_area(mult, poly_center(end_search_space), end_rot, end_search_space, end_minus_corners)
            if max_pos:
                end_shape = [max_pos, end_rot, smallest_scale*mult]
                end_minus_corners = poly_subtraction(end_minus_corners, miter(shape_at(Square, smallest_scale*mult, max_pos, end_rot), 1/10, True))
            else: continue
        else:
            # find closest point in search space to the center
            min_point = []
            for point in end_search_space:
                d = math.dist(point, end_center)
                if not min_point or d < min_point[1]:
                    min_point = [point, d]
            end_shape = [min_point[0], end_rot, smallest_scale*mult]
        return start_shape, end_shape, start_minus_corners, end_minus_corners
    # couldn't find anything in all the search spaces
    return False

def find_inner_placements(start_corners, end_corners, start_placed_shapes, end_placed_shapes):
    # miter to avoid trying to place shapes far in the corners
    start_minus_corners = miter(start_corners, -smallest_scale, True); end_minus_corners = miter(end_corners, -smallest_scale, True)
    # find space to be filled
    if start_minus_corners: start_minus_corners = poly_subtraction(start_minus_corners[0], start_placed_shapes)
    if end_minus_corners: end_minus_corners = poly_subtraction(end_minus_corners[0], end_placed_shapes)
    # loop while area still needs to be covered
    start_shapes, end_shapes = [], []
    while abs(area(start_minus_corners)) > 1/10000 or abs(area(end_minus_corners)) > 1/10000:
        fill = find_inner_placement(start_corners, end_corners, start_minus_corners, end_minus_corners)
        if not fill: break
        s_shape, e_shape, start_minus_corners, end_minus_corners = fill
        start_shapes.append(s_shape); end_shapes.append(e_shape)
    return start_shapes, end_shapes

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
    for i, triangle_pair in enumerate(s_triangles):
        if not triangle_pair: continue
        if triangle_pair[0][0] == "triangle":
            type = Triangle; m = 1
        else:
            type = SharpTriangle; m = 2
        triangle = triangle_pair[0]
        start_shapes.append(shape_at(type, triangle[3], triangle[1], triangle[2], triangle[4]))
        start_offs_s[i][1] = triangle[3]*m + triangle[5]
        triangle = triangle_pair[1]
        start_shapes.append(shape_at(type, triangle[3], triangle[1], triangle[2], triangle[4]))
        start_offs_s[(i+1)%len(start_offs_s)][0] = triangle[3]*m + triangle[5]
    for i, triangle_pair in enumerate(e_triangles):
        if not triangle_pair: continue
        if triangle_pair[0][0] == "triangle":
            type = Triangle; m = 1
        else:
            type = SharpTriangle; m = 2
        triangle = triangle_pair[0]
        end_shapes.append(shape_at(type, triangle[3], triangle[1], triangle[2], triangle[4]))
        end_offs_s[i][1] = triangle[3]*m + triangle[5]
        triangle = triangle_pair[1]
        end_shapes.append(shape_at(type, triangle[3], triangle[1], triangle[2], triangle[4]))
        end_offs_s[(i+1)%len(end_offs_s)][0] = triangle[3]*m + triangle[5]
    # find and append all the edge placements
    new_s_shapes, new_e_shapes = find_edge_placements(start_corners, end_corners, start_offs_s, end_offs_s)
    for shape in new_s_shapes:
        start_shapes.append(shape_at(Square, shape[2], shape[0], shape[1]))
    for shape in new_e_shapes:
        end_shapes.append(shape_at(Square, shape[2], shape[0], shape[1]))
    # find and append inner placements
    new_s_shapes, new_e_shapes = find_inner_placements(start_corners, end_corners, start_shapes, end_shapes)
    for shape in new_s_shapes:
        start_shapes.append(shape_at(Square, shape[2], shape[0], shape[1]))
    for shape in new_e_shapes:
        end_shapes.append(shape_at(Square, shape[2], shape[0], shape[1]))
    return start_shapes + end_shapes

if __name__ == "__main__":
    big_corners = [[30, 30], [30, 75], [75, 75], [75, 30]]
    s = Screen(500)
    s.add_polygons([big_corners, [[150, 120], [150, 165], [200, 225], [215, 140]]])
    s.add_poly_method(lambda x: find_shapes(x[0], x[1]), ((0,0),(0,1)))
    run_screens()
    #start_pos, start_rot, end_pos, end_rot = big_shape.find_placement(rect, [[10, 0], [10, 15], [25, 17], [25, 2]])