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
import time

# Blender imports
import bpy
from bpy.props import *

# Addon imports
# NONE!


def getMatNames(all=False):
    scn = bpy.context.scene
    materials = bpy.props.abs_mats_common.copy()
    if scn.include_transparent or all:
        materials += bpy.props.abs_mats_transparent
    if scn.include_uncommon or all:
        materials += bpy.props.abs_mats_uncommon
    return materials


def update_abs_subsurf(self, context):
    scn = context.scene
    for mat_name in getMatNames(all=True):
        mat = bpy.data.materials.get(mat_name)
        if mat is None:
            continue
        nodes = mat.node_tree.nodes
        target_node = nodes.get("ABS Dialectric")
        if target_node is None:
            continue
        input1 = target_node.inputs.get("SSS Default")
        input2 = target_node.inputs.get("SSS Amount")
        if input1 is None or input2 is None:
            continue
        default_amount = input1.default_value
        input2.default_value = default_amount * scn.abs_subsurf


def update_abs_reflect(self, context):
    scn = context.scene
    for mat_name in getMatNames(all=True):
        mat = bpy.data.materials.get(mat_name)
        if mat is None:
            continue
        nodes = mat.node_tree.nodes
        target_node = nodes.get("ABS Dialectric") or nodes.get("ABS Transparent")
        if target_node is None:
            continue
        input1 = target_node.inputs.get("Reflection")
        if input1 is None:
            continue
        input1.default_value = scn.abs_reflect * (0.4 if mat.name in ["ABS Plastic Silver", "ABS Plastic Gold"] else 0.005)


def update_abs_randomize(self, context):
    scn = context.scene
    for mat_name in getMatNames(all=True):
        mat = bpy.data.materials.get(mat_name)
        if mat is None:
            continue
        nodes = mat.node_tree.nodes
        target_node = nodes.get("ABS Dialectric") or nodes.get("ABS Transparent")
        if target_node is None:
            continue
        input1 = target_node.inputs.get("Random")
        if input1 is None:
            continue
        input1.default_value = scn.abs_randomize


def update_abs_fingerprints(self, context):
    scn = context.scene
    for mat_name in getMatNames(all=True):
        mat = bpy.data.materials.get(mat_name)
        if mat is None:
            continue
        nodes = mat.node_tree.nodes
        target_node1 = nodes.get("ABS Dialectric") or nodes.get("ABS Transparent")
        target_node2 = nodes.get("ABS Bump")
        if target_node1 is None or target_node2 is None:
            continue
        input1 = target_node1.inputs.get("Fingerprints")
        input2 = target_node2.inputs.get("Fingerprints")
        if input1 is None or input2 is None:
            continue
        input1.default_value = scn.abs_fingerprints if mat.name not in ["ABS Plastic Silver", "ABS Plastic Gold"] else scn.abs_fingerprints / 8
        input2.default_value = scn.abs_fingerprints * scn.abs_displace



def update_abs_displace(self, context):
    scn = context.scene
    for mat_name in getMatNames(all=True):
        mat = bpy.data.materials.get(mat_name)
        if mat is None:
            continue
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        target_node = nodes.get("ABS Bump")
        if target_node is None:
            continue
        noise = target_node.inputs.get("Noise")
        waves = target_node.inputs.get("Waves")
        scratches = target_node.inputs.get("Scratches")
        fingerprints = target_node.inputs.get("Fingerprints")
        if noise is None or waves is None or scratches is None or fingerprints is None:
            continue
        noise.default_value = scn.abs_displace if mat.name not in ["ABS Plastic Silver", "ABS Plastic Gold"] else scn.abs_displace * 20
        waves.default_value = scn.abs_displace
        scratches.default_value = scn.abs_displace
        fingerprints.default_value = scn.abs_fingerprints * scn.abs_displace
        # disconnect displacement node if not used
        color_out = target_node.outputs[0]
        mo_node = nodes.get("Material Output")
        if mo_node is None:
            continue
        displace = mo_node.inputs.get("Displacement")
        if displace is None:
            continue
        if scn.abs_displace == 0:
            for l in displace.links:
                links.remove(l)
        else:
            links.new(target_node.outputs["Color"], displace)


def toggle_save_datablocks(self, context):
    scn = context.scene
    for mat_name in getMatNames(all=True):
        mat = bpy.data.materials.get(mat_name)
        if mat is not None:
            mat.use_fake_user = scn.save_datablocks


def update_image(self, context):
    scn = context.scene
    res = round(scn.uv_detail_quality, 1)
    resizedImg = getDetailImage(res, bpy.data.images.get("ABS Fingerprints and Dust"))
    fnode = bpy.data.node_groups.get("ABS_Fingerprint")
    snode = bpy.data.node_groups.get("ABS_Specular Map")
    imageNode1 = fnode.nodes.get("ABS_Fingerprints and Dust")
    imageNode2 = snode.nodes.get("ABS_Fingerprints and Dust")
    print(resizedImg.name)
    for img_node in (imageNode1, imageNode2):
        img_node.image = resizedImg


def getDetailImage(res, full_img):
    # create smaller fingerprints/dust images
    newImgName = "ABS Fingerprints and Dust" if res == 1 else "ABS Fingerprints and Dust (%(res)s)" % locals()
    detail_img_scaled = bpy.data.images.get(newImgName)
    if detail_img_scaled is None:
        detail_img_scaled = duplicateImage(full_img, newImgName)
        newScale = 2000 * res
        detail_img_scaled.scale(newScale, newScale)
    return detail_img_scaled


def duplicateImage(img, name):
    width, height = img.size
    newImage = bpy.data.images.new(name, width, height)
    newImage.pixels = img.pixels[:]
    return newImage


def stopWatch(text, lastTime, precision=5):
    """From seconds to Days;Hours:Minutes;Seconds"""
    value = time.time()-lastTime

    valueD = (((value/365)/24)/60)
    Days = int(valueD)

    valueH = (valueD-Days)*365
    Hours = int(valueH)

    valueM = (valueH - Hours)*24
    Minutes = int(valueM)

    valueS = (valueM - Minutes)*60
    Seconds = round(valueS, precision)

    outputString = str(text) + ": " + str(Days) + ";" + str(Hours) + ":" + str(Minutes) + ";" + str(Seconds)
    print(outputString)
    return time.time()
