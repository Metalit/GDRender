
def solid_object(id, pos, rot=0, scale=1, color=1004, groups=None, flipx=0, flipy=0, level=0, level2=0, zlayer=0, foreground=False):
    string = [1, id, 2, pos[0], 3, pos[1]]
    if flipx:
        string += [4, 1]
    if flipy:
        string += [5, 1]
    if not rot == 0:
        string += [6, rot]
    if not level == 0:
        string += [20, level]
    if not color == 1004:
        string += [21, color]
    if foreground:
        string += [24, 5]
    if not zlayer == 0:
        string += [25, zlayer]
    if not scale == 1:
        string += [32, scale]
    if not groups == None:
        string += [57, '.'.join([str(e) for e in groups])]
    if not level2 == 0:
        string += [61, level2]
    return ','.join([str(e) for e in string]) + ';'

def move_trigger(pos, length, target, movement):
    string = [1, 901, 2, pos[0], 3, pos[1], 10, length, 28, movement[0], 29, movement[1], 30,11,51, target]
    return ','.join([str(e) for e in string]) + ';'

# rotates clockwise
def rot_trigger(pos, length, target, target2, degrees, easelvl):
    if abs(degrees) >= 360:
        degrees = degrees%360
        times360 = int(degrees/360)
    string = [1, 1346, 2, pos[0], 3, pos[1], 10, length, 68, degrees]
    if not times360 == 0:
        string += [69, times360]
    if not easelvl == 1:
        string += [30, 11, 85, easelvl]
    return ','.join([str(e) for e in string]) + ';'