import bpy
from . import property

class YfToolbox_Panel_Rigging(bpy.types.Panel):
    bl_idname = "yf.toolbox_rigging_panel"
    bl_label = "Rigging"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "YF"

    def draw(self, context):
        # You can set the property values that should be used when the user
        # presses the button in the UI.
        layout = self.layout
        scene = context.scene
        row = layout.row()

        row.operator("yf.toolbox_rigging_op_def_to_org",
                         text="Bind DEF to ORG",
                         icon="DECORATE_LINKED")
        row = layout.row()
        row.operator("yf.toolbox_rigging_op_auto_bone_collections",
                         text="Auto B-Collections",
                         icon="BRUSH_DATA")
        
        row = layout.row()
        row.prop(scene.yf_rigging_prop_grp, "copy_constraint_use_symmetry", text="Use Symmetry?")
        row = layout.row()
        row.operator("yf.toolbox_rigging_op_copy_constraints_with_drivers",
                         text="Copy Constraints w/ Drivers",
                         icon="BRUSH_DATA")
        row = layout.row()
        
        return 