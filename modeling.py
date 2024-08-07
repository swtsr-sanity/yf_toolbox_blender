import bpy

    
class YfToolbox_Panel_Modeling(bpy.types.Panel):
    bl_idname = "yf.toolbox_panel_modeling"
    bl_label = "MODEL"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "YF"

    def draw(self, context):
        # You can set the property values that should be used when the user
        # presses the button in the UI.
        layout = self.layout
        scene = context.scene

def register():
    bpy.utils.register_class(YfToolbox_Panel_Modeling)

def unregister():
    bpy.utils.unregister_class(YfToolbox_Panel_Modeling)

