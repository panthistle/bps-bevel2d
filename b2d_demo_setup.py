##############################################################################
#                                                                            #
#   'b2d_demo_setup' Blender Python script  ---  Pan Thistle, 2022           #
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


import bpy
import math
import bmesh

from mathutils import Vector

# RUN THIS MODULE "ONCE" TO CREATE THE OBJECTS REQUIRED FOR THE DEMO


def new_mesh_object(name, coll, vcs, fcs):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new(use_operators=False)
    bmvs = [bm.verts.new(v) for v in vcs]
    for f in fcs:
        bm.faces.new((bmvs[i] for i in f))
    bm.to_mesh(me)
    me.update()
    bm.free()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


def polysmooth(ob):
    me = ob.data
    me.use_auto_smooth = True
    lst = [True] * len(me.polygons)
    me.polygons.foreach_set("use_smooth", lst)
    me.update()


# demo collection ----------------------------------------


name = "bevelobs"
if name in bpy.data.collections:
    coll = bpy.data.collections[name]
else:
    coll = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(coll)


# plane object -------------------------------------------


name = "bme"
if name not in coll.objects:
    me = bpy.data.meshes.new(name)
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    ob.color = (0.8, 0.8, 0.8, 1)


# node objects -------------------------------------------


def node_object(name, coll):
    ups = 32
    dt = 0.0625 * math.pi
    ufax = [dt * i for i in range(ups)]
    vps = 16
    dt = (math.pi - 0.002) / (vps - 1)
    vfax = [0.001 + dt * i for i in range(vps)]
    rad = 0.1
    nvs = []
    scan = []
    for j in range(vps):
        loop = j * ups
        vloc = vfax[j]
        sinvloc = math.sin(vloc)
        z = rad * math.cos(vloc)
        for i in range(ups):
            uloc = ufax[i]
            x = rad * sinvloc * math.cos(uloc)
            y = rad * sinvloc * math.sin(uloc)
            nvs.append(Vector((x, y, z)))
            scan.append(i + loop)
        scan.append(loop)
    pts = ups + 1
    fcs = [
        [
            scan[i + j * pts],
            scan[i + pts + j * pts],
            scan[i + pts + 1 + j * pts],
            scan[i + 1 + j * pts],
        ]
        for j in range(vps - 1)
        for i in range(ups)
    ]
    npts = ups * vps
    fcs += [list(range(ups))] + [list(range(npts - ups, npts))[::-1]]
    return new_mesh_object(name, coll, nvs, fcs)


ob = node_object("a", coll)
polysmooth(ob)
ob.color = (0.23, 0.46, 0.8, 1)

names = ["b", "c", "p1", "p2", "pc"]
for n in names:
    t = ob.copy()
    coll.objects.link(t)
    t.name = n
    if n in ["p1", "p2"]:
        t.color = (0.8, 0.8, 0.8, 1)
    elif n == "pc":
        t.color = (0.993, 0.415, 1, 1)


# side objects --------------------------------------------


def side_object(name, coll, cap=False):
    r = 0.05
    n = 16
    t = 0.125 * math.pi
    cvs = [Vector((r * math.cos(t * i), 0, r * math.sin(t * i))) for i in range(n)]
    y = Vector((0, 1, 0))
    cvs = cvs + [v + y for v in cvs]
    scan = list(range(n)) + [0] + list(range(n, n * 2)) + [n]
    fcs = [[scan[i], scan[i + n + 1], scan[i + n + 2], scan[i + 1]] for i in range(n)]
    if cap:
        fcs += [list(range(n, n * 2))[::-1]]
    return new_mesh_object(name, coll, cvs, fcs)


ob = side_object("ab", coll)
polysmooth(ob)
ob.color = (0.8, 0.49, 0.36, 1)

ac = ob.copy()
coll.objects.link(ac)
ac.name = "ac"

pn = side_object("pn", coll, True)
polysmooth(pn)
pn.color = (0.36, 0.49, 0.8, 1)
