import numpy as np

# general 2D rotation matrix (positive theta is CCW, negative theta is CW)
def rot_2D(theta):
    return np.array(((np.cos(theta), -np.sin(theta)), 
                     (np.sin(theta), np.cos(theta))))


# maybe it's overkill, this just matrix version of saying x = x + dx and y = y + dy
def affine_translation(coordinates, dx = 503.796/2, dy = 45):
    matrix = np.array(((1, 0, dx),
                       (0, 1, -dy),
                       (0, 0, 1)))
    out = np.empty_like(coordinates)
    for i in range(len(coordinates)):
        pair = coordinates[i]
        translated = matrix @ np.array([pair[0], pair[1], 1])
        pair = translated[0:2]
        out[i] = pair
    return out

# takes transformation matrix and rotation matrix and applies it to u, v pair
def transform(coords, p, theta):
    mat_trans =  p * rot_2D(theta/2 + np.pi/2)@np.array(((1/np.sin(theta), 0), 
                                                          (-1/np.tan(theta), 1))).T
    out_coords = mat_trans@np.array((coords[0], coords[1]))
    return out_coords