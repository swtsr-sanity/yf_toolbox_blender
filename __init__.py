import bpy
import importlib
from . import rigging, modeling, pomodoro, timelapse, yf_lib

DEBUG = True

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



def register():
    if DEBUG:
        try:
                importlib.reload(rigging)
                importlib.reload(yf_lib)
        except:
            pass
    
    rigging.register()
    modeling.register()
    pomodoro.register()
    timelapse.register()

def unregister():
    rigging.unregister()
    modeling.unregister()
    pomodoro.unregister()
    timelapse.unregister()

if __name__ == "__main__":
    register()