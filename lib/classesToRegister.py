'''
Copyright (C) 2018 Bricks Brought to Life
http://bblanimation.com/
chris@bblanimation.com

Created by Christopher Gearhart

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

# Addon imports
from ..ui import *
from ..buttons import *
from .preferences import *
from .. import addon_updater_ops


classes = (
    # abs_plastic_materials/addon_updater_ops.py
    addon_updater_ops.OBJECT_OT_addon_updater_install_popup,
    addon_updater_ops.OBJECT_OT_addon_updater_check_now,
    addon_updater_ops.OBJECT_OT_addon_updater_update_now,
    addon_updater_ops.OBJECT_OT_addon_updater_update_target,
    addon_updater_ops.OBJECT_OT_addon_updater_install_manually,
    addon_updater_ops.OBJECT_OT_addon_updater_updated_successful,
    addon_updater_ops.OBJECT_OT_addon_updater_restore_backup,
    addon_updater_ops.OBJECT_OT_addon_updater_ignore,
    addon_updater_ops.OBJECT_OT_addon_updater_end_background,
    # abs_plastic_materials/buttons
    ABS_OT_append_materials,
    # abs_plastic_materials/lib
    ABS_PT_preferences,
    # abs_plastic_materials/ui
    BRICKER_PT_abs_plastic,
)
