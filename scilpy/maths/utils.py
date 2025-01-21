# -*- coding: utf-8 -*-
import numpy as np
from scipy.linalg import svd


def fit_circle_2d(x, y, dist_w):
    """
    Least square for circle fitting in 2D
    dist_w allows for re-weighting of points
    """
    if dist_w is None:
        dist_w = np.ones(len(x))

    # Fit a circle in 2D using least-squares
    A = np.array([x, y, dist_w]).T
    b = x**2 + y**2
    params = np.linalg.lstsq(A, b, rcond=None)[0]

    # Get circle parameters from solution
    x_c = params[0]/2
    y_c = params[1]/2
    r = np.sqrt(params[2] + x_c**2 + y_c**2)

    return x_c, y_c, r

def rodrigues_rot(P, n0, n1):
    """
    Rodrigues rotation (not mine, see URL)
    - Rotate given points based on a starting and ending vector
    - Axis k and angle of rotation theta given by vectors n0,n1
    P_rot = P*cos(theta) + (k x P)*sin(theta) + k*<k,P>*(1-cos(theta))
    https://meshlogic.github.io/posts/jupyter/curve-fitting/fitting-a-circle-to-cluster-of-3d-points/
    """

    # If P is only 1d array (coords of single point), fix it to be matrix
    if P.ndim == 1:
        P = P[np.newaxis, :]

    # Get vector of rotation k and angle theta
    n0 /= np.linalg.norm(n0)
    n1 /= np.linalg.norm(n1)
    k = np.cross(n0, n1)
    k = k / np.linalg.norm(k)
    theta = np.arccos(np.dot(n0, n1))

    # Compute rotated points
    P_rot = np.zeros((len(P), 3))
    for i in range(len(P)):
        P_rot[i] = P[i]*np.cos(theta) + np.cross(k, P[i]) * \
            np.sin(theta) + k*np.dot(k, P[i])*(1-np.cos(theta))

    return P_rot


def fit_circle_planar(pts, dist_w):
    # Fitting plane by SVD for the mean-centered data
    pts_mean = pts.mean(axis=0)
    pts_centered = pts - pts_mean

    _, _, V = svd(pts_centered, full_matrices=False)
    normal = V[2, :]

    # Project points to coords X-Y in 2D plane
    pts_xy = rodrigues_rot(pts_centered, normal, [0, 0, 1])

    # Fit circle in new 2D coords
    dist = np.linalg.norm(pts_centered, axis=1)
    if dist_w == 'lin_up':
        dist /= np.max(dist)
    elif dist_w == 'lin_down':
        dist /= np.max(dist)
        dist = 1 - dist
    elif dist_w == 'exp':
        dist /= np.max(dist)
        dist = np.exp(dist)
    elif dist_w == 'inv':
        dist /= np.max(dist)
        dist = 1 / dist
    elif dist_w == 'log':
        dist /= np.max(dist)
        dist = np.log(dist+1)
    else:
        dist = None

    x_c, y_c, radius = fit_circle_2d(pts_xy[:, 0], pts_xy[:, 1], dist)

    # Transform circle center back to 3D coords
    pts_recentered = rodrigues_rot(np.array([x_c, y_c, 0]),
                                   [0, 0, 1], normal) + pts_mean

    return pts_recentered, radius


def fit_circle_in_space(positions, directions, dist_w=None):
    # Project all points to a plane perpendicular to the centroid
    u_directions = np.average(directions, axis=0)
    u_directions /= np.linalg.norm(u_directions)
    barycenter = np.average(positions, axis=0)
    vector = positions - barycenter

    dist = np.zeros((len(vector)))
    proj_positions = np.zeros((len(vector), 3))
    for i in range(len(vector)):
        dist[i] = np.dot(vector[i], u_directions)
        proj_positions[i] = positions[i] - dist[i]*u_directions

    # With all points on a fixed plane, estimate a circle
    center, radius = fit_circle_planar(proj_positions, dist_w)
    dist = np.linalg.norm(proj_positions - center, axis=1)
    error = np.average(np.sqrt((dist - radius)**2))

    return center, radius, error
