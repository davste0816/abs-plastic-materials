# Copyright (C) 2018 Christopher Gearhart
# chris@bblanimation.com
# http://bblanimation.com/
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# System imports
import bpy
import os
import time
from mathutils import Matrix, Vector

# Blender imports
# NONE!

# Addon imports
from ..functions import *
from ..colors import *
from ..lib.mat_properties import mat_properties

def appendFrom(directory, filename):
    filepath = directory + filename
    bpy.ops.wm.append(
        filepath=filepath,
        filename=filename,
        directory=directory)


class ABS_OT_append_materials(bpy.types.Operator):
    """Append ABS Plastic Materials from external blender file"""               # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "abs.append_materials"                                          # unique identifier for buttons and menu items to reference.
    bl_label = "Append ABS Plastic Materials"                                   # display name in the interface.
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(self, context):
        return context.scene.render.engine in ("CYCLES", "BLENDER_EEVEE")

    def execute(self, context):
        # initialize variables
        scn = context.scene
        mat_names = getMatNames()  # list of materials to append from 'abs_plastic_materials.blend'
        alreadyImported = [mn for mn in mat_names if bpy.data.materials.get(mn) is not None]
        matsToReplace = []
        failed = []

        # define file paths
        # addonsPath = bpy.utils.user_resource('SCRIPTS', "addons")
        addonPath = os.path.dirname(os.path.abspath(__file__))[:-8]
        blendfile = "%(addonPath)s/abs_plastic_materials.blend" % locals()
        nodeDirectory = "%(blendfile)s/NodeTree/" % locals()
        imDirectory = "%(blendfile)s/Image/" % locals()

        imagesToReplace = ("ABS Fingerprints and Dust")
        nodeGroupsToReplace = ("ABS_Absorbtion", "ABS_Basic Noise", "ABS_Bump", "ABS_Dialectric", "ABS_Dialectric 2", "ABS_Fingerprint", "ABS_Fresnel", "ABS_GlassAbsorption", "ABS_Parallel_Scratches", "ABS_PBR Glass", "ABS_Random Value", "ABS_Randomize Color", "ABS_Reflection", "ABS_Scale", "ABS_Scratches", "ABS_Specular Map", "ABS_Transparent", "ABS_Uniform Scale", "Translate", "RotateZ", "RotateY", "RotateX", "RotateXYZ")

        # set cm.brickMaterialsAreDirty for all models in Bricker, if it's installed
        if hasattr(scn, "cmlist"):
            for cm in scn.cmlist:
                if cm.materialType == "Random":
                    cm.brickMaterialsAreDirty = True

        # remove existing bump/specular maps
        for im in bpy.data.images:
            if im.name in imagesToReplace:
                bpy.data.images.remove(im)
        # remove old existing node groups
        for ng in bpy.data.node_groups:
            if ng.name.startswith("ABS_") and ng.name[4:] in nodeGroupsToReplace:
                bpy.data.node_groups.remove(ng)

        # temporarily switch to object mode
        current_mode = str(bpy.context.mode)
        if current_mode == "EDIT_MESH":
            bpy.ops.object.mode_set(mode="OBJECT")

        # append node groups from nodeDirectory
        group_names = ("ABS_Bump", "ABS_Dialectric", "ABS_Transparent", "ABS_Uniform Scale")
        for gn in group_names:
            appendFrom(nodeDirectory, filename=gn)
        # append fingerprints and dust image from imDirectory
        appendFrom(imDirectory, filename="ABS Fingerprints and Dust")

        for mat_name in mat_names:
            # if material exists, remove or skip
            m = bpy.data.materials.get(mat_name)
            if m is not None:
                # mark material to replace
                m.name = m.name + "__replaced"
                matsToReplace.append(m)

            # get the current length of bpy.data.materials
            last_len_mats = len(bpy.data.materials)

            # create new material
            m = bpy.data.materials.new(mat_name)
            m.use_nodes = True

            # create/get all necessary nodes
            nodes = m.node_tree.nodes
            nodes.remove(nodes.get("Principled BSDF"))
            n_shader = nodes.new("ShaderNodeGroup")
            if mat_name.startswith("ABS Plastic Trans-"):
                n_shader.node_tree = bpy.data.node_groups.get("ABS_Transparent")
            else:
                n_shader.node_tree = bpy.data.node_groups.get("ABS_Dialectric")
            n_bump = nodes.new("ShaderNodeGroup")
            n_bump.node_tree = bpy.data.node_groups.get("ABS_Bump")
            n_scale = nodes.new("ShaderNodeGroup")
            n_scale.node_tree = bpy.data.node_groups.get("ABS_Uniform Scale")
            n_displace = nodes.new("ShaderNodeDisplacement")
            n_uv = nodes.new("ShaderNodeUVMap")
            n_output = nodes.get("Material Output")

            # connect the nodes together
            links = m.node_tree.links
            links.new(n_shader.outputs["Shader"], n_output.inputs["Surface"])
            links.new(n_displace.outputs["Displacement"], n_output.inputs["Displacement"])
            links.new(n_bump.outputs["Color"], n_displace.inputs["Height"])
            links.new(n_uv.outputs["UV"], n_scale.inputs["Vector"])
            links.new(n_scale.outputs["Vector"], n_shader.inputs["Vector"])
            links.new(n_scale.outputs["Vector"], n_bump.inputs["Vector"])

            # position the nodes in 2D space
            starting_loc = n_output.location
            n_shader.location = n_output.location - Vector((400, -250))
            n_bump.location = n_output.location - Vector((400, 200))
            n_displace.location = n_output.location - Vector((200, 200))
            n_scale.location = n_output.location - Vector((600, 200))
            n_uv.location = n_output.location - Vector((800, 200))

            # set properties
            if mat_name in mat_properties.keys():
                for k in mat_properties[mat_name].keys():
                    n_shader.inputs[k].default_value = mat_properties[mat_name][k]

            # get compare last length of bpy.data.materials to current (if the same, material not imported)
            if len(bpy.data.materials) == last_len_mats:
                self.report({"WARNING"}, "'%(mat_name)s' could not be imported. Try reinstalling the addon." % locals())
                if m in matsToReplace:
                    matsToReplace.remove(m)
                failed.append(mat_name)
                continue

        # replace old material node trees
        for old_mat in matsToReplace:
            origName = old_mat.name.split("__")[0]
            new_mat = bpy.data.materials.get(origName)
            old_mat.user_remap(new_mat)
            bpy.data.materials.remove(old_mat)

        # switch back to last mode
        if current_mode == "EDIT_MESH":
            bpy.ops.object.mode_set(mode="EDIT")

        # update subsurf/reflection amounts
        update_abs_subsurf(self, bpy.context)
        update_abs_reflect(self, bpy.context)
        update_abs_randomize(self, bpy.context)
        update_abs_fingerprints(self, context)
        update_abs_displace(self, bpy.context)
        toggle_save_datablocks(self, bpy.context)

        # remap node groups to one group
        for groupName in nodeGroupsToReplace:
            firstGroup = None
            for g in bpy.data.node_groups:
                if g is None or not g.name.startswith(groupName):
                    continue
                if g.users == 0:
                    bpy.data.node_groups.remove(g)
                elif firstGroup is None:
                    firstGroup = g
                else:
                    g.user_remap(firstGroup)
                    bpy.data.node_groups.remove(g)
            if firstGroup is not None:
                firstGroup.name = groupName

        # report status
        if len(alreadyImported) == len(mat_names):
            self.report({"INFO"}, "Materials already imported")
        elif len(alreadyImported) > 0:
            self.report({"INFO"}, "The following Materials were skipped: " + str(alreadyImported)[1:-1].replace("'", "").replace("ABS Plastic ", ""))
        elif len(failed) > 0:
            self.report({"INFO"}, "The following Materials failed to import (try reinstalling the addon): " + str(failed)[1:-1].replace("'", "").replace("ABS Plastic ", ""))
        else:
            self.report({"INFO"}, "Materials imported successfully!")

        return{"FINISHED"}
