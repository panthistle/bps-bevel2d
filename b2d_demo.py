##############################################################################
#                                                                            #
#   'b2d_demo' Blender Python script  ---  Pan Thistle, 2022                 #
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

from mathutils import Matrix, Quaternion, Vector


# *** DEMO REQUIREMENT:
def req_check(scene):
    try:
        coll = scene.collection.children["bevelobs"]
        names = ["a", "b", "c", "ab", "ac", "p1", "p2", "pc", "pn", "bme"]
        for n in names:
            ob = coll.objects[n]
    except Exception:
        print("missing required objects")
        return False
    return True


# ------------------------------------------------------------------------------
#
# ----------------------------- PROPERTIES -------------------------------------


class PTDBEV2D_props(bpy.types.PropertyGroup):
    # 3 points to define the plane
    a: bpy.props.FloatVectorProperty(size=3, default=[0, 0, 0])
    b: bpy.props.FloatVectorProperty(size=3, default=[4, 0, 0])
    c: bpy.props.FloatVectorProperty(size=3, default=[0, 4, 0])
    # bevel offset/segments
    offset: bpy.props.FloatProperty(default=1.5, min=0.001)
    segs: bpy.props.IntProperty(default=8, min=1, max=16)
    # display
    show_norm: bpy.props.BoolProperty(default=True)
    show_mesh: bpy.props.BoolProperty(default=True)
    show_pts: bpy.props.BoolProperty(default=True)


# ------------------------------------------------------------------------------
#
# ------------------------- BEVEL2D DEMO FUNCTION ------------------------------


def bevelocs_demo(a, b, c, segs, offset):
    # return bevel points [list of vector] *** demo version

    ab = b - a
    ac = c - a
    vcross = ab.cross(ac)
    p1 = a + ab.normalized() * offset
    uac = ac.normalized()
    p2 = a + uac * offset
    pc = p1 + uac * offset
    pn = vcross.normalized()
    oblocs = [a, b, c, ab, ac, p1.copy(), p2.copy(), pc.copy(), pn]
    if vcross.length == 0:
        return {"belocs": [a], "oblocs": oblocs}
    z = Vector((0, 0, 1))
    xy_plane = 1 - abs(z.dot(pn)) < 1e-4
    if not xy_plane:
        mrd = z.rotation_difference(pn).to_matrix().to_4x4()
        p1, p2, pc = [mrd.inverted() @ v for v in [p1, p2, pc]]
    mloc = Matrix.Translation(pc)
    p1, p2 = [mloc.inverted() @ v for v in [p1, p2]]
    ang = p1.to_2d().angle_signed(Vector((1, 0)), 0)
    mrot = Quaternion(z, ang).to_matrix().to_4x4()
    p1, p2 = [mrot.inverted() @ v for v in [p1, p2]]
    mshe = Matrix.Shear("XZ", 4, (p2[0] / p2[1], 0))
    p2 = mshe.inverted() @ p2
    msca = Matrix.Diagonal((p1[0], p2[1], 1, 1))
    mat = mloc @ mrot @ mshe @ msca
    if not xy_plane:
        mat = mrd @ mat
    npts = list(range(segs + 1))
    dt = 0.5 * math.pi / segs
    belocs = [mat @ Vector((math.cos(dt * i), math.sin(dt * i), 0)) for i in npts]
    return {"belocs": belocs, "oblocs": oblocs}


# ------------------------------------------------------------------------------
#
# ------------------------------ OPERATOR --------------------------------------


class PTDBEV2D_OT_demo(bpy.types.Operator):
    bl_label = "Demo"
    bl_idname = "ptdbev2d.demo"
    bl_description = "bevel 2d demo"
    bl_options = {"REGISTER", "INTERNAL", "UNDO"}

    a: bpy.props.FloatVectorProperty(size=3, default=[0, 0, 0])
    b: bpy.props.FloatVectorProperty(size=3, default=[4, 0, 0])
    c: bpy.props.FloatVectorProperty(size=3, default=[0, 4, 0])
    offset: bpy.props.FloatProperty(default=1.5, min=0.001)
    segs: bpy.props.IntProperty(default=8, min=1, max=16)
    show_norm: bpy.props.BoolProperty(name="Norm", default=True)
    show_mesh: bpy.props.BoolProperty(name="Mesh", default=True)
    show_pts: bpy.props.BoolProperty(name="Points", default=True)

    def invoke(self, context, event):
        props = context.scene.ptdb2_props
        pd = self.as_keywords()
        for key in pd.keys():
            setattr(self, key, getattr(props, key))
        return self.execute(context)

    def execute(self, context):
        scene = context.scene
        props = scene.ptdb2_props
        a = Vector(self.a)
        b = Vector(self.b)
        c = Vector(self.c)
        self.offset_adjust(a, b, c)
        pd = self.as_keywords()
        for key in pd.keys():
            setattr(props, key, getattr(self, key))
        try:
            d = bevelocs_demo(a, b, c, self.segs, self.offset)
            coll = scene.collection.children["bevelobs"]
            self.update_bevelobs(d, coll, "bev_pt")
            self.update_bevelmesh(d, coll)
        except Exception as my_err:
            print(f"bevel 2d demo: {my_err.args}")
            return {"CANCELLED"}
        return {"FINISHED"}

    def offset_adjust(self, a, b, c):
        ab = (b - a).length
        ac = (c - a).length
        limit = min(ab, ac) - 0.01
        lo = 0.001
        hi = max(limit, lo)
        val = self.offset
        self.offset = min(max(lo, val), hi)

    def update_bevelobs(self, d, coll, name):
        lst = [ob for ob in coll.objects if ob.name.startswith(name)]
        for ob in lst:
            bpy.data.objects.remove(ob)
        a, b, c, ab, ac, p1, p2, pc, norm = d["oblocs"]
        coll.objects["a"].location = a
        coll.objects["b"].location = b
        coll.objects["c"].location = c
        coll.objects["p1"].location = p1
        coll.objects["p2"].location = p2
        coll.objects["pc"].location = pc
        vab = coll.objects["ab"]
        vab.location = a
        y = Vector((0, 1, 0))
        vab.rotation_euler = y.rotation_difference(ab).to_euler()
        vab.scale[1] = ab.length
        vac = coll.objects["ac"]
        vac.location = a
        vac.rotation_euler = y.rotation_difference(ac).to_euler()
        vac.scale[1] = ac.length
        # update/display plane normal
        pn = coll.objects["pn"]
        if self.show_norm:
            pn.location = pc
            pn.rotation_euler = y.rotation_difference(norm).to_euler()
            pn.hide_viewport = False
        else:
            pn.hide_viewport = True
        # create/display bevel points
        if self.show_pts and len(d["belocs"]) > 2:
            locs = d["belocs"][1:-1]
            sample = coll.objects["p1"]
            for loc in locs:
                ob = sample.copy()
                coll.objects.link(ob)
                ob.name = name
                ob.location = loc
                ob.color = (0.20, 0.8, 0.45, 1)
                ob.hide_viewport = False

    def update_bevelmesh(self, d, coll):
        ob = coll.objects["bme"]
        # update/display mesh object
        if self.show_mesh:
            locs = [d["oblocs"][2]] + d["belocs"][::-1] + [d["oblocs"][1]]
            bm = bmesh.new(use_operators=False)
            mvs = [bm.verts.new(loc) for loc in locs]
            bm.faces.new(mvs)
            me = ob.data
            bm.to_mesh(me)
            me.update()
            bm.free()
            ob.hide_viewport = False
        else:
            ob.hide_viewport = True

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        row = box.row(align=True)
        s = row.split(factor=0.4)
        sc = s.column(align=True)
        names = ["Anchor", "B", "C", "Offset", "Segments", "Display"]
        for name in names:
            row = sc.row()
            row.label(text=name)
        sc = s.column(align=True)
        row = sc.row(align=True)
        row.prop(self, "a", text="")
        row = sc.row(align=True)
        row.prop(self, "b", text="")
        row = sc.row(align=True)
        row.prop(self, "c", text="")
        row = sc.row(align=True)
        row.prop(self, "offset", text="")
        row = sc.row(align=True)
        row.prop(self, "segs", text="")
        row = sc.row(align=True)
        row.prop(self, "show_pts", toggle=True)
        row.prop(self, "show_mesh", toggle=True)
        row.prop(self, "show_norm", toggle=True)


# ------------------------------------------------------------------------------
#
# ------------------------------ SIDE PANEL ------------------------------------


class PTDBEV2D_PT_ui(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_context = "objectmode"
    bl_category = "B2D"
    bl_label = "Bevel 2D"

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.enabled = req_check(context.scene)
        row.operator("ptdbev2d.demo")


# ------------------------------------------------------------------------------
#
# ------------------------------- REGISTRATION ---------------------------------

classes = (
    PTDBEV2D_props,
    PTDBEV2D_OT_demo,
    PTDBEV2D_PT_ui,
)


def register():
    from bpy.utils import register_class

    for cls in classes:
        register_class(cls)
    bpy.types.Scene.ptdb2_props = bpy.props.PointerProperty(type=PTDBEV2D_props)


def unregister():
    from bpy.utils import unregister_class

    for cls in reversed(classes):
        unregister_class(cls)
    del bpy.types.Scene.ptdb2_props


# ------------------------------------------------------------------------------
#
# ------------------------------ RUN MODULE ------------------------------------

if __name__ == "__main__":
    print("-" * 30)
    register()
    unregister()
