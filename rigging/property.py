import bpy

class YfToolbox_PropertyGroup_Rigging(bpy.types.PropertyGroup):
    copy_constraint_use_symmetry: bpy.props.BoolProperty(default=False)
