from base_shapes import *
from scipy.optimize import minimize, curve_fit
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

def area_for_minimize(position, *args):
    """Gives the area of the intersection of a shape at a given position and rotation and another.

    Answer weighted and arguments ordered in a way intended to be used in Scipy.minimize."""
    # get values from *args
    rotation, shape, shape_inside_corners = args
    # find the actual polygon to intersect
    inter_corners = shape.corners(position, rotation, add_to=False)
    # get the exact area
    ret_area = abs(area(poly_intersection(inter_corners, shape_inside_corners)))
    # weight the area slightly towards being farther away from the center
    if ret_area < 1/(1<<16): return 0
    centroid = poly_center(shape_inside_corners)
    dist = math.dist(position, centroid)
    min_mult = 0.9; max_mult = 1.1
    # dist = 0: ret_area *= min_mult, dist = ideal_dist: ret_area *= 1, dist -> infinity: ret_area *= max_mult
    ideal_dist = math.sqrt(ret_area)
    b = 1/(max_mult-min_mult); a = 1/(max_mult-1) - b
    ret_area *= (-ideal_dist)/(a*dist+b*ideal_dist) + max_mult
    return -ret_area

class Combination:
    def __init__(self, corners, max_corners):
        self.corners = corners
        self.start_shapes = []
        self.moved_shapes = []
    
    def find_shapes(self, new_corners):
        shapes = []
        s_triangles, e_triangles = find_corner_triangles(self.corners, new_corners)
    
    def find_placement_old(self, shape: Shape, new_corners, other_shape_corners=[], new_other_shape_corners=[]):
        """Finds a placement for a shape inside the combination object, taking into account previously placed shapes if any.

        Returns the position and rotation of the placement for the start and then for the end."""
        # find the remaining corners for start and end
        remaining_corners = deepcopy(self.corners)
        for other_shape in other_shape_corners: remaining_corners = clean(poly_subtraction(remaining_corners, other_shape))
        new_remaining_corners = deepcopy(new_corners)
        for other_shape in new_other_shape_corners: new_remaining_corners = clean(poly_subtraction(new_remaining_corners, other_shape))
        # find if the shape fits in both remaining corners
        fits = len(offset_miter(remaining_corners, shape.side_length, shape.type)) > 0 and len(offset_miter(new_remaining_corners, shape.side_length, shape.type))
        (start_skel, start_skel_edges), (end_skel, end_skel_edges) = straight_skeleton(self.corners), straight_skeleton(new_corners)
        if fits:
            # find the offset miter edges inside each edge's part of the straight skeleton
            start_sector_edges, end_sector_edges = [[] for _ in new_corners], [[] for _ in new_corners]
            # find all the offset edges for the start and end remaining shapes
            start_offset_edges = [offset_miter_edge(remaining_corners, shape.side_length, i, shape.type) for i in range(len(remaining_corners))]
            end_offset_edges = [offset_miter_edge(new_remaining_corners, shape.side_length, i, shape.type) for i in range(len(new_remaining_corners))]
            for i, sector in enumerate(start_skel):
                for offset_edge in start_offset_edges:
                    if not offset_edge: continue
                    # clip the offset with every sector
                    contained = line_clip(offset_edge, sector)
                    # add the edge if it is contained
                    if contained: start_sector_edges[start_skel_edges[i]].append(contained)
            for i, sector in enumerate(end_skel):
                for offset_edge in end_offset_edges:
                    if not offset_edge: continue
                    # clip the offset with every sector
                    contained = line_clip(offset_edge, sector)
                    # add the edge if it is contained
                    if contained: end_sector_edges[end_skel_edges[i]].append(contained)
            # use the inner endpoint of an edge if its sector contains another edge
            for start_sector_edge, end_sector_edge in zip(start_sector_edges, end_sector_edges):
                if len(start_sector_edge) > 1 and end_sector_edge:
                    return start_sector_edge[0][1], angle(self.corners[i], self.corners[i-1]), end_sector_edge[0][1%len(end_sector_edge)], angle(new_corners[i], new_corners[i-1])
                if len(end_sector_edge) > 1 and start_sector_edge:
                    return start_sector_edge[0][1%len(start_sector_edge)], angle(self.corners[i], self.corners[i-1]), end_sector_edge[0][1], angle(new_corners[i], new_corners[i-1])
            # no sectors contain more than one edge on at least one and at least one edge on the other
            for start_sector_edge, end_sector_edge in zip(start_sector_edges, end_sector_edges):
                if start_sector_edge and end_sector_edge:
                    return start_sector_edge[0][0], angle(self.corners[i], self.corners[i-1]), end_sector_edge[0][0], angle(new_corners[i], new_corners[i-1])
            # else: sectors are completely mismatched, use other method
        # doesn't fit in remaining corners
        start_miter, end_miter = offset_miter(self.corners, shape.side_length, shape.type), offset_miter(new_corners, shape.side_length, shape.type)
        # doesn't fit at all
        if not start_miter or not end_miter: return False
        # find search spaces for placements
        start_remain_miter, end_remain_miter = miter(remaining_corners, shape.side_length/2), miter(new_remaining_corners, shape.side_length/2)
        # divide into spaces for aligning rotation to each edge
        start_sector_searches, end_sector_searches = [[] for _ in new_corners], [[] for _ in new_corners]
        for i, sector in enumerate(start_skel):
            clip = poly_intersection(sector, start_remain_miter[0])
            if clip: start_sector_searches[start_skel_edges[i]] = clip
        for i, sector in enumerate(end_skel):
            clip = poly_intersection(sector, end_remain_miter[0])
            if clip: end_sector_searches[end_skel_edges[i]] = clip
        # find best position in search spaces that are in both start and end
        start_poss, end_poss = [], []
        for i in range(len(start_sector_searches)):
            start_search_space, end_search_space = start_sector_searches[i], end_sector_searches[i]
            if not start_search_space or not end_search_space: continue
            start_rot, end_rot = angle(self.corners[i], self.corners[i-1]), angle(new_corners[i], new_corners[i-1])
            # constraints to search inside the search space
            start_constraint = ({'type': 'eq', 'fun': lambda x: int(not inside(x, start_search_space))})
            end_constraint = ({'type': 'eq', 'fun': lambda x: int(not inside(x, end_search_space))})
            start_minimize_result = minimize(area_for_minimize, poly_center(start_search_space), args=(start_rot, shape, remaining_corners), constraints=start_constraint, method="trust-constr")
            end_minimize_result = minimize(area_for_minimize, poly_center(end_search_space), args=(end_rot, shape, new_remaining_corners), constraints=end_constraint, method="trust-constr")
            start_poss.append([-start_minimize_result.fun, start_minimize_result.x])
            end_poss.append([-end_minimize_result.fun, end_minimize_result.x])
        best = [0, 0]
        # find the found positions that cover the most area, then return them with their correct rotations
        for i, (start_pos, end_pos) in enumerate(zip(start_poss, end_poss)):
            # skip empty ones
            if not start_pos or not end_pos: continue
            if start_pos[0] + end_pos[0] > best[0]:
                best = [start_pos[0] + end_pos[0], i]
        if not best[0] == 0:
            return start_poss[best[1]][1], angle(self.corners[best[1]], self.corners[best[1]-1]), end_poss[best[1]][1], angle(new_corners[best[1]], new_corners[best[1]-1])
        # no overlap of regular shape and remaining shape? pretty weird
        print('No overlap, bug probably')
        return False

def untyped_find_placement_old(start_corners, end_corners, other_start, other_end, shape: Shape):
    c = Combination(start_corners, None)
    place = c.find_placement_old(shape, end_corners, other_start, other_end)
    if not place: return []
    start_pos, start_rot, end_pos, end_rot = place
    start_placement = shape.corners(start_pos, start_rot, add_to=False)
    end_placement = shape.corners(end_pos, end_rot, add_to=False)
    return start_placement, end_placement

def find_shapes(start_corners, end_corners):
    shapes = []
    start_offs_s = [[0,0] for _ in start_corners]
    end_offs_s = [[0,0] for _ in end_corners]
    s_triangles, e_triangles = find_corner_triangles(start_corners, end_corners)
    for i, triangles in enumerate(s_triangles):
        if not triangles: continue
        if triangles[0][0] == "triangle":
            type = Triangle; m = 1
        else:
            type = SharpTriangle; m = 2
        triangle = triangles[0]
        shapes.append(shape_at(type, triangle[1], triangle[2], triangle[3], triangle[4]))
        start_offs_s[i][1] = triangle[1]*m
        triangle = triangles[1]
        shapes.append(shape_at(type, triangle[1], triangle[2], triangle[3], triangle[4]))
        start_offs_s[(i+1)%len(start_offs_s)][0] = triangle[1]*m
    for i, triangles in enumerate(e_triangles):
        if not triangles: continue
        if triangles[0][0] == "triangle":
            type = Triangle; m = 1
        else:
            type = SharpTriangle; m = 2
        triangle = triangles[0]
        shapes.append(shape_at(type, triangle[1], triangle[2], triangle[3], triangle[4]))
        end_offs_s[i][1] = triangle[1]*m
        triangle = triangles[1]
        shapes.append(shape_at(type, triangle[1], triangle[2], triangle[3], triangle[4]))
        end_offs_s[(i+1)%len(end_offs_s)][0] = triangle[1]*m
    for i, (s_offs, e_offs) in enumerate(zip(start_offs_s, end_offs_s)):
        still_space = find_edge_placement(start_corners, end_corners, i, s_offs, e_offs)
        while still_space:
            scale, s_pos, e_pos, s_offs[:], e_offs[:] = still_space
            s_rot, e_rot = angle(start_corners[i-1], start_corners[i]), angle(end_corners[i-1], end_corners[i])
            shapes.append(shape_at(Square, smallest_scale*scale, s_pos, s_rot))
            shapes.append(shape_at(Square, smallest_scale*scale, e_pos, e_rot))
            still_space = find_edge_placement(start_corners, end_corners, i, s_offs, e_offs)
    return shapes

if __name__ == "__main__":
    big_corners = [[30, 30], [30, 75], [75, 75], [75, 30]]
    big_shape = Combination(big_corners, max_corners=big_corners)
    s = Screen(500)
    s.add_polygons([big_corners, [[150, 120], [150, 165], [225, 201], [225, 126]]])
    s.add_poly_method(lambda x: find_shapes(x[0], x[1]), ((0,0),(0,1)))
    s.add_poly_method(lambda x: find_shapes(x[0], x[1]), ((0,0),(0,1),(1,0),(1,1)))
    run_screens()
    #start_pos, start_rot, end_pos, end_rot = big_shape.find_placement(rect, [[10, 0], [10, 15], [25, 17], [25, 2]])