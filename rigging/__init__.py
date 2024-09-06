import bpy
import importlib
from . import ui, operator, property


classes = (
           ui.YfToolbox_Panel_Rigging, 
           operator.YfToolbox_Operator_AddCopyXformConstraintDEFToORG, 
           operator.YfToolbox_Operator_AutoBoneCollections, 
           operator.YfToolbox_Operator_CopyConstraintWithDrivers,
           )


__register, __unregister = bpy.utils.register_classes_factory(classes)

def register():
    __register()
    bpy.utils.register_class(property.YfToolbox_PropertyGroup_Rigging)
    bpy.types.Scene.yf_rigging_prop_grp = bpy.props.PointerProperty(type=property.YfToolbox_PropertyGroup_Rigging)

def unregister():
    __unregister()

