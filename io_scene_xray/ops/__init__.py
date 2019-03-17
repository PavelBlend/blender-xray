
import bpy

from . import joint_limits


class BaseOperator(bpy.types.Operator):
    report_catcher = None

    def __getattribute__(self, item):
        if (item == 'report') and (self.report_catcher is not None):
            return self.report_catcher
        return super().__getattribute__(item)
