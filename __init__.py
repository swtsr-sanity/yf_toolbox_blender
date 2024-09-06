import bpy
import importlib
from . import pref
from . import modeling, pomodoro, timelapse
from . import rigging

bl_info = {
    "name": "Yf's Toolbox",
    "blender": (2, 80, 0),
    "category": "3D View",
    "version": (1, 0, 0),
    "description": "Does nothing fancy, really.",
    "location": "View 3D > Tool > YF",
    "category": "3D View",
    "doc_url": "https://github.com/swtsr-sanity/yf_toolbox_blender",
}

from types import ModuleType


from importlib import reload  # Python 3.4+


def register():
    
    reload(rigging)
    reload(rigging.ui)
    reload(rigging.operator)
    reload(rigging.property)
    reload(pref)

    bpy.utils.register_class(pref.YfToolbox_AddonPreference)
    rigging.register()

    



def unregister():
    rigging.unregister()
    bpy.utils.unregister_class(pref.YfToolbox_AddonPreference)

if __name__ == "__main__":
    register()