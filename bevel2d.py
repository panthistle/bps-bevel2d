##############################################################################
#                                                                            #
#   'bevel2d' Blender Python script  ---  Pan Thistle, 2022                  #
#                                                                            #
#   This program is free software: you can redistribute it and/or modify     #
#   it under the terms of the GNU General Public License as published by     #
#   the Free Software Foundation, either version 3 of the License, or        #
#   (at your option) any later version.                                      #
#                                                                            #
#   This program is distributed in the hope that it will be useful,          #
#   but WITHOUT ANY WARRANTY; without even the implied warranty of           #
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            #
#   GNU General Public License for more details.                             #
#                                                                            #
#   You should have received a copy of the GNU General Public License        #
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.   #
#                                                                            #
##############################################################################


import math

from mathutils import Matrix, Quaternion, Vector


# ------------------------------------------------------------------------------
#
# --------------------------- BEVEL2D FUNCTION ---------------------------------


def bevel_2d(a, b, c, segs, offset):
    # return bevel points [list of Vector]
    # - a, b, c : mathutils Vector objects (a is the intersection point)
    # - segs : int > 1
    # - offset : float > 0

    # the sides of interest
    ab = b - a
    ac = c - a

    # check the length and direction of the sides:
    # if two vectors are parallel, or if either one has zero length, 
    # then their cross product is a zero-length vector
    vcross = ab.cross(ac)
    if vcross.length == 0:
        # cannot bevel straight line or single point: return corner point
        return [a]

    # the 3 vectors we will use to calculate the transformation matrix are
    # obtained from the input parameters
    p1 = a + ab.normalized() * offset
    uac = ac.normalized()
    p2 = a + uac * offset
    pc = p1 + uac * offset

    # 1. align abc-plane with xy-plane - Rotation
    pn = vcross.normalized()  # abc-plane normal
    z = Vector((0, 0, 1))  # xy-plane normal
    # if two unit vectors are parallel, then their dot product (the cosine 
    # of their angle) is either -1 or 1, depending on their direction
    dot = abs(z.dot(pn))
    # the condition is: dot == 1, but we must account for floating point error
    xy_plane = 1 - dot < 1e-4
    if not xy_plane:
        mrd = z.rotation_difference(pn).to_matrix().to_4x4()
        pc, p1, p2 = [mrd.inverted() @ v for v in [pc, p1, p2]]

    # 2. move pc to origin - Translation
    mt = Matrix.Translation(pc)
    p1, p2 = [mt.inverted() @ v for v in [p1, p2]]

    # 3. align p1 with x-axis - Rotation
    # get signed angle between the vectors (clockwise is positive)..
    ang = p1.to_2d().angle_signed(Vector((1, 0)), 0)
    mr = Quaternion(z, ang).to_matrix().to_4x4()
    # or:  mr = p1.to_track_quat('X', 'Z').to_matrix().to_4x4()
    p1, p2 = [mr.inverted() @ v for v in [p1, p2]]

    # 4. align p2 with y-axis - Shear
    msh = Matrix.Shear("XZ", 4, (p2[0] / p2[1], 0))
    # or:  msh = Matrix.Shear('X', 2, p2[0] / p2[1]).to_4x4()
    p2 = msh.inverted() @ p2

    # 5. get the scale from p1 and p2 - Scale
    mdg = Matrix.Diagonal((p1[0], p2[1], 1, 1))

    # create bevel-points on the first quadrant of unit circle
    npts = list(range(segs + 1))
    dt = 0.5 * math.pi / segs
    bvs = [Vector((math.cos(dt * i), math.sin(dt * i), 0)) for i in npts]

    # compile transformation matrix (transforms applied in reverse order)
    mat = mt @ mr @ msh @ mdg
    if not xy_plane:
        mat = mrd @ mat

    # return adjusted coordinates
    return [mat @ v for v in bvs]
