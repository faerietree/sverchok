# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
import bmesh
import mathutils

from bpy.props import EnumProperty, BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import Vector_generate
from sverchok.utils.sv_bmesh_utils import pydata_from_bmesh, bmesh_from_pydata


def make_hull(vertices, params):
    if not vertices:
        return False

    verts, faces = [], []
    bm = bmesh_from_pydata(vertices, [], [])

    if params.hull_mode == '3D':

        res = bmesh.ops.convex_hull(bm, input=bm_verts, use_existing_faces=False)
        print(res)
        verts, _, faces = pydata_from_bmesh(bm)
        bm.clear()
        bm.free()

    elif params.hull_mode == '2D':
       
        if params.plane == 'Z':
            vertices_2d = [(v[0], v[1]) for v in vertices]
        elif params.plane == 'Y':
            vertices_2d = [(v[0], v[2]) for v in vertices]
        else:
            vertices_2d = [(v[1], v[2]) for v in vertices]

        GG = mathutils.geometry.convex_hull_2d(vertices_2d)

        if params.outside and not params.inside:
            unused_v_indices = set(GG) - set(range(len(vertices)))
            bmesh.ops.delete(bm, geom=[bm.verts[i] for i in unused_v_indices], context=0)
            verts, _, faces = pydata_from_bmesh(bm)

    return (verts, faces)

class SvConvexHullNodeMK2(bpy.types.Node, SverchCustomTreeNode):
    ''' cvh 2D/3D conv.hull'''
    bl_idname = 'SvConvexHullNodeMK2'
    bl_label = 'Convex Hull MK2'
    # bl_icon = 'OUTLINER_OB_EMPTY'

    hull_mode_options = [(k, k, '', i) for i, k in enumerate(["3D", "2D"])]
    hull_mode = EnumProperty(
        description=" 3d or 2d?", default="3D", items=hull_mode_options, update=updateNode
    )

    plane_choices = [(k, k, '', i) for i, k in enumerate(["X", "Y", "Z"])]
    plane = EnumProperty(
        description="track 2D plane", default="X", items=plane_choices, update=updateNode
    )

    outer = BoolProperty(default=True, update=updateNode)
    inner = BoolProperty(default=False, update=updateNode)


    def sv_init(self, context):
        self.inputs.new('VerticesSocket', 'Vertices')

        self.outputs.new('VerticesSocket', 'Vertices')
        self.outputs.new('StringsSocket', 'Polygons')

    def draw_buttons(self, context, layout):
        pass

    def process(self):

        if self.inputs['Vertices'].is_linked:

            verts = Vector_generate(self.inputs['Vertices'].sv_get())
            verts_out = []
            polys_out = []

            for v_obj in verts:
                res = make_hull(v_obj, self)
                if not res:
                    return

                verts_out.append(res[0])
                polys_out.append(res[1])

            self.outputs['Vertices'].sv_set(verts_out)
            self.outputs['Polygons'].sv_set(polys_out)


def register():
    bpy.utils.register_class(SvConvexHullNodeMK2)


def unregister():
    bpy.utils.unregister_class(SvConvexHullNodeMK2)
