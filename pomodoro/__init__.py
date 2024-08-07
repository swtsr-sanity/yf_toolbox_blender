import importlib


import bpy
from . import pomodoro_base, todo_base
from .util_funcs import *

from bpy.app.handlers import persistent

import sys

bl_info = {
    "name": "Yf's Easy Pomodoro",
    "blender": (2, 80, 0),
    "category": "3D View",
    "version": (1, 0, 0),
    "description": "A Pomodoro Timer in Blender.",
    "location": "View 3D > Tool > Pomodoro",
    "category": "3D View",
    "doc_url": "https://github.com/yufan-zhang1006/yf_ez_pomodoro_blender",
}

DEBUG = True

def menu_draw(self, context):
    layout = self.layout
    scene = context.scene
    props = scene.yf_pomodoro_props
    c = layout.column()
    r = c.row(align=True)
    b = r.box()
    b.label(
        icon_value=custom_icons["tomato" if not props.is_blinking else "invisible"].icon_id,
        text=str(seconds_to_time_string(props.cur_time))
        )
    r.popover("yf.pomodoro_header_popover")

@persistent
def on_file_read(dummy):
    bpy.ops.yf.reset_op()

def register():
    if DEBUG:
        try:
            importlib.reload(pomodoro_base)
            importlib.reload(todo_base)
            importlib.reload(util_funcs)
        except:
            pass

    bpy.app.handlers.load_post.append(on_file_read)
    pomodoro_base.register()
    todo_base.register()

    bpy.types.VIEW3D_MT_editor_menus.append(menu_draw)


def unregister():
    bpy.app.handlers.load_post.remove(on_file_read)
    pomodoro_base.unregister()
    todo_base.unregister()

    bpy.types.VIEW3D_MT_editor_menus.remove(menu_draw)
