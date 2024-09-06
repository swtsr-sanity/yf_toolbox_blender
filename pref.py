import bpy
from .rigging import property
from . import __package__ as base_package


class YfToolbox_AddonPreference(bpy.types.AddonPreferences):
    bl_idname = base_package
    bl_options = {'REGISTER'}
    prefs_tabs: bpy.props.EnumProperty(items=(('UI', "General", "General Settings"),
                                    ('RIGGING', "Rigging", "Rigging Settings"),
                                    ('KEYMAPS', "Keymaps", "Keymaps"),
                                    ('SUPPORT', "Support & Donation", "Support")),
                             default='UI')


    prefix_root: bpy.props.StringProperty(name="Root Bone", description="",default='ROOT')
    prefix_def: bpy.props.StringProperty(name="DEF Bone", description="",default='DEF')
    prefix_org: bpy.props.StringProperty(name="DEF Bone", description="",default='ORG')
    prefix_ctl: bpy.props.StringProperty(name="CTL Bone", description="",default='CTL')
    prefix_wgt: bpy.props.StringProperty(name="WGT Bone", description="",default='WGT')
    prefix_mch: bpy.props.StringProperty(name="MCH Bone", description="",default='MCH')
    prefix_ik: bpy.props.StringProperty(name="IK Bone", description="",default='IK')
    prefix_fk: bpy.props.StringProperty(name="FK Bone", description="",default='FK')

    rigging_settings = ["prefix_root", "prefix_def", "prefix_org", "prefix_ctl", "prefix_wgt", "prefix_mch", "prefix_ik", "prefix_fk"]

    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)
        row.prop(self, "prefs_tabs", expand=True)

        if self.prefs_tabs == "RIGGING":
            row = layout.row()
            row.label(text="Bone Naming")
            for setting in self.rigging_settings:
                row = layout.row(align=True)
                row.prop(self, setting)