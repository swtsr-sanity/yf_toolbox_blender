import bpy

def get_active_object() -> bpy.types.Object:
    return bpy.context.active_object


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