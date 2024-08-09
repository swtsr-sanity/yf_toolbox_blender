import bpy

def get_selected_objects() -> list[bpy.types.Object]:
    return bpy.context.selected_objects


"""
OBJECT:         Object Mode.
EDIT:           Edit Mode.
POSE:           Pose Mode.
SCULPT:         Sculpt Mode.
VERTEX_PAINT:   Vertex Paint.
WEIGHT_PAINT:   Weight Paint.
TEXTURE_PAINT:  Texture Paint.
PARTICLE_EDIT:  Particle Edit.
EDIT_GPENCIL:   Edit Mode. Edit Grease Pencil Strokes.
SCULPT_GPENCIL: Sculpt Mode. Sculpt Grease Pencil Strokes.
PAINT_GPENCIL:  Draw Mode. Paint Grease Pencil Strokes.
WEIGHT_GPENCIL: Weight Paint. Grease Pencil Weight Paint Strokes.
VERTEX_GPENCIL: Vertex Paint.
Grease Pencil   Vertex Paint Strokes.
SCULPT_CURVES:  Sculpt Mode.
"""
# Get the current interaction mode of the active object
def get_active_object_interaction_mode() -> str:
    return bpy.context.object.mode

# Sets the object interaction mode
def set_active_object_interaction_mode(mode_):
    bpy.ops.object.mode_set(mode=mode_)


def get_all_collections(armature_):
    def recursively_get_children_collections(ret_, coll):
        if len(coll.children) == 0:
            return [coll]
        for child in coll.children:
            ret_ += recursively_get_children_collections(ret_, child)
        return ret_ 
    ret = []
    for c in armature_.collections:
        ret += recursively_get_children_collections([], c)
    ret += [c for c in armature_.collections]
    return ret