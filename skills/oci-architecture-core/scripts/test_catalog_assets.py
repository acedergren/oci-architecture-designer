import tempfile
import unittest
from pathlib import Path
from catalog_assets import drawio_index


class ImportedGroups(unittest.TestCase):
    def test_wrapper_and_implicit_group_labels_are_indexed(self):
        xml = '''<mxfile><diagram name="Icons"><mxGraphModel><root>
        <mxCell id="0"/><mxCell id="1" parent="0"/>
        <UserObject id="official" label=""><mxCell parent="1" vertex="1" style="vsdxID=1;"/></UserObject>
        <mxCell id="label1" parent="official" value="Oracle Base"/>
        <mxCell id="label2" parent="official" value="Database"/>
        </root></mxGraphModel></diagram></mxfile>'''
        with tempfile.TemporaryDirectory() as d:
            p = Path(d, 'fixture.drawio'); p.write_text(xml)
            entries = drawio_index(p)
        self.assertEqual(entries, [{'page':'Icons', 'cell_id':'official', 'label':'Oracle Base Database', 'cell_count':3}])


if __name__ == '__main__':
    unittest.main()
