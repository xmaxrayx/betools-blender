#################################################################
# Be Tools by Bruce Evans                                       #
# brucein3d@gmail.com                                           #
#################################################################

import bpy
import bmesh
import math
from mathutils import Vector

from .. import _settings

class BETOOLS_OT_RecalcNormals(bpy.types.Operator):
    bl_idname = "mesh.be_recalc_normals"
    bl_label = "Recalculate Normals"
    bl_description = "Recalculate exterior normals, must be in EDIT mode with FACE selection"
    bl_options = {'REGISTER', 'UNDO'}

    def consistentNormals(self):
        bpy.ops.mesh.select_mode(type='FACE')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.normals_make_consistent(inside=False)

    def execute(self, context):

        if bpy.context.active_object.mode == 'OBJECT':
            bpy.ops.object.editmode_toggle()
            self.consistentNormals()
            bpy.ops.object.editmode_toggle()
        else:
            self.consistentNormals()
        return {"FINISHED"}

    @classmethod
    def poll(cls, context):
        if context.object is None:
            return False
        if context.object.type != 'MESH':
            return False
        if _settings.edit_pivot_mode:
            return False
        return True


class BETOOLS_OT_SnapToFace(bpy.types.Operator):
    bl_idname = "mesh.be_snap_to_face"
    bl_label = "Snap to Face"
    bl_description = "Snap mesh to selected face"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        
        targetTransform, targetRotation = getFaceCenter()

        if not targetTransform or bpy.context.object.mode == 'OBJECT':
            self.report({'INFO'}, 'Switch to FACE mode and select a face to snap.')
            return {"FINISHED"}

        bpy.ops.object.mode_set(mode='OBJECT')

        faceObject = bpy.context.selected_objects[0]
        targetTransform += faceObject.location
        
        bpy.ops.object.select_all(action='DESELECT')
        bpy.data.objects[context.scene.snap_object].select_set(True)

        if faceObject == bpy.data.objects[context.scene.snap_object]:
            self.report({'INFO'}, 'Invalid selection! Choose a different object to snap.')
            return {"FINISHED"}

        location = bpy.data.objects[context.scene.snap_object].location
        translateToCoordinates(location, targetTransform)
        rotateToCoordinates(context.scene.snap_object, targetRotation)

        return {"FINISHED"}

    @classmethod
    def poll(cls, context):
        if context.object is None:
            return False
        if _settings.edit_pivot_mode:
            return False
        if not bpy.types.Scene.snap_object:
            return False
        if context.object.type != 'MESH':
            return False
        return True


class BETOOLS_OT_ResizeObjects(bpy.types.Operator):
    bl_idname = "mesh.be_resize"
    bl_label = "Resize Objects"
    bl_description = "Resize objects to unit scale"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # TODO
        # for scaling, get the target unit and current unit
        # target unit / current unit to get scalar
        # for each object in scene, scale by scalar
        return {'FINISHED'}


################################################
#   Utilities
################################################

def getFaceCenter():
    """ Get the center position of the selected face

        args:
            face (face?)

        returns:
            pos (Vec3)
            normal (Vec3)
    """

    bm = get_mesh()
    if not bm:
        return (None, None)
    faces = [face for face in bm.faces if face.select]
    if not len(faces) == 1:
        return (None, None)
    return faces[0].calc_center_median_weighted(), faces[0].normal

def get_mesh():
    """ Small helper to get the current bmesh in edit mode
    """
    
    ob = bpy.context.active_object
    
    if not ob.mode == 'EDIT':
        print("Must be in EDIT mode when getting a BMESH object")
        return
    
    return bmesh.from_edit_mesh(ob.data)

def getSelectedVerts():
    bm = get_mesh()
    return [vert for vert in bm.verts if vert.select]

def getSelectedEdges():
    bm = get_mesh()
    return [edge for edge in bm.edges if edge.select]

def getSelectedFaces():
    """ The data gets destroyed, try global?
    """
    bm = get_mesh()
    return [face for face in bm.faces if face.select]

def get_mesh_bounding_box(bm):
    """ Return the min, max, and span of the bounding box
    """

    bounding_box = {}
    bounds_min = Vector((99999999.0, 99999999.0, 99999999.0))
    bounds_max = Vector((-99999999.0, -99999999.0, -99999999.0))
    bounds_center = Vector((0.0, 0.0, 0.0))

    for vert in bm.verts:

        bounds_min.x = min(bounds_min.x, vert.co.x)
        bounds_min.y = min(bounds_min.y, vert.co.y)
        bounds_min.z = min(bounds_min.z, vert.co.z)

        bounds_max.x = max(bounds_max.x, vert.co.x)
        bounds_max.y = max(bounds_max.y, vert.co.y)
        bounds_max.z = max(bounds_max.z, vert.co.z)

    bounding_box['min'] = bounds_min
    bounding_box['max'] = bounds_max
    bounding_box['width'] = (bounds_max - bounds_min).y
    bounding_box['height'] = (bounds_max - bounds_min).z
    bounding_box['depth'] = (bounds_max - bounds_min).x

    bounds_center.x = (bounds_max - bounds_min).x / 2
    bounds_center.y = (bounds_max - bounds_min).y / 2
    bounds_center.z = (bounds_max - bounds_min).z / 2

    bounding_box['center'] = bounds_center
    bounding_box['area'] = bounding_box['width'] * bounding_box['height'] * bounding_box['depth']
    bounding_box['min_length'] = min(bounding_box['width'], bounding_box['height'], bounding_box['depth'])

    return bounding_box

def get_face_bounding_box(face):
    bounding_box = {}
    bounds_min = Vector((99999999.0, 99999999.0, 99999999.0))
    bounds_max = Vector((-99999999.0, -99999999.0, -99999999.0))

    for vert in face.verts:
        bounds_min.x = min(bounds_min.x, vert.co.x)
        bounds_min.y = min(bounds_min.y, vert.co.y)
        bounds_min.z = min(bounds_min.z, vert.co.z)
        bounds_max.x = max(bounds_max.x, vert.co.x)
        bounds_max.y = max(bounds_max.y, vert.co.y)
        bounds_max.z = max(bounds_max.z, vert.co.z)

    bounding_box['min'] = bounds_min
    bounding_box['max'] = bounds_max

    return bounding_box

def rotateToCoordinates(obj, direction):

    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.objects[obj].select_set(True)

    bpy.data.objects[obj].rotation_mode = 'QUATERNION'
    bpy.data.objects[obj].rotation_quaternion = direction.to_track_quat('X','Z')

def translateToCoordinates(objectLocation, targetLocation):
    """ Translate object to a target coordinate location

        args:
            objectLocation (vec3)
            targetLocation (vec3)
    """
    delta = mathutils.Vector(targetLocation - objectLocation)
    bpy.ops.transform.translate(value=delta)


bpy.utils.register_class(BETOOLS_OT_RecalcNormals)
bpy.utils.register_class(BETOOLS_OT_SnapToFace)
bpy.utils.register_class(BETOOLS_OT_ResizeObjects)
