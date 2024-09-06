import bpy
from . import ui
    
classes = (ui.YfToolbox_Panel_Modeling, )
register, unregister = bpy.utils.register_classes_factory(classes)

