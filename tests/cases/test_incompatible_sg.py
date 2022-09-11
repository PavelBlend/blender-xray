from tests import utils

import bmesh
import bpy
import re


class TestObjectExport_IncompatibleSG(utils.XRayTestCase):

    def test_sharpEdgeAdjacentsHasSameSmoothingGroups(self):
        # Arrange
        bm = utils.create_bmesh((
            (0, 0, 0),
            (-1, -1, 0), (+1, -1, 0), (+1, +1, 0), (-1, +1, 0),
        ), ((0, 1, 2), (0, 2, 3), (0, 3, 4), (0, 4, 1)))
        bm.edges.ensure_lookup_table()
        bm.edges[0].smooth = False
        obj = utils.create_object(bm)

        # Act
        bpy.ops.xray_export.object(
            objects=obj.name, directory=self.outpath(),
            texture_name_from_image_path=False,
            export_motions=False,
        )

        # Assert
        self.assertOutputFiles({
            obj.name + '.object',
        })
        self.assertReportsContains(
            'WARNING',
            re.compile('Maya-SG incompatible: sharp edge adjacents has same smoothing group')
        )
