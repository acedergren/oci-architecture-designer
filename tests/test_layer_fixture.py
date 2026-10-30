"""Exercise fixed layered fixtures with synthetic XML, without source artwork."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as E
import zipfile

import integration_official as fixture
from test_validators import presentation_parts, write_package, P, A


MODEL = dict(nodes=[dict(id='app'), dict(id='db')], flows=[dict(id='sql')])
GRAPH = ('<mxfile><diagram name="Architecture"><mxGraphModel><root>'
         '<mxCell id="0"/><mxCell id="1" parent="0"/>'
         '<mxCell id="title" parent="1" vertex="1" value="Synthetic example"/>'
         '<mxCell id="vcn" parent="1" vertex="1"/>'
         '<mxCell id="app" parent="vcn" vertex="1" value="App"/>'
         '<mxCell id="db" parent="vcn" vertex="1" value="DB"/>'
         '<mxCell id="sql" edge="1" source="app" target="db" parent="vcn"/>'
         '<mxCell id="assumptions" parent="1" vertex="1" value="Optional note"/>'
         '</root></mxGraphModel></diagram></mxfile>')


class LayerFixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'architecture.drawio'

    def test_drawio_preserves_ancestry_critical_flows_and_scoped_edit(self):
        self.path.write_text(GRAPH)
        fixture.layer_drawio(self.path, MODEL)
        sidecar = self.path.with_suffix('.views.json')
        self.assertEqual(fixture.validate_drawio.check(self.path, sidecar)['layer_view_integrity'], 'PASS')
        root = E.parse(self.path).getroot()
        self.assertEqual(root.find('.//mxCell[@id="app"]').get('parent'), 'vcn')
        self.assertEqual(root.find('.//mxCell[@id="sql"]').get('parent'), 'layer-flows')
        self.assertEqual(root.find('.//mxCell[@id="title"]').get('value'), 'Proposed synthetic — routes/security not deployed')
        for cell in root.findall('.//mxCell'):
            if cell.get('value'):
                self.assertIn('fontFamily=Oracle Sans;', cell.get('style'))
        edited = self.path.with_name('edited.drawio')
        root.find('.//mxCell[@id="assumptions"]').set('value', 'Updated note')
        edited.write_bytes(E.tostring(root))
        fixture.assert_drawio_preserved(self.path, edited, {'assumptions'})
        root.find('.//mxCell[@id="app"]').set('parent', 'layer-flows')
        edited.write_bytes(E.tostring(root))
        with self.assertRaises(AssertionError):
            fixture.assert_drawio_preserved(self.path, edited, {'assumptions'})
        root.find('.//root').remove(root.find('.//mxCell[@id="db"]'))
        edited.write_bytes(E.tostring(root))
        with self.assertRaises(AssertionError):
            fixture.assert_drawio_preserved(self.path, edited, {'assumptions'})

    def test_pptx_view_slides_are_native_and_reference_is_unchanged(self):
        path = self.path.with_suffix('.pptx')
        shape = (f'<p:sp><p:nvSpPr><p:cNvPr id="2" name="title"/></p:nvSpPr>'
                 f'<p:txBody><a:p><a:r><a:rPr><a:latin typeface="Calibri"/></a:rPr>'
                 f'<a:t>Synthetic OCI architecture</a:t></a:r></a:p></p:txBody></p:sp>')
        parts = presentation_parts(shape)
        for k in list(parts):
            parts[k.replace('slide1.xml','slide24.xml')] = parts.pop(k).replace('slide1.xml','slide24.xml')
        parts['ppt/slides/slide25.xml'] = parts['ppt/slides/slide24.xml']
        write_package(path, parts)
        untouched = parts['ppt/slides/slide25.xml'].encode()
        fixture.layer_pptx(path)
        with zipfile.ZipFile(path) as z:
            self.assertEqual(z.read('ppt/slides/slide25.xml'), untouched)
            self.assertIn('ppt/slides/slide26.xml', z.namelist())
            for part in ('ppt/slides/slide24.xml','ppt/slides/slide26.xml'):
                root = E.fromstring(z.read(part))
                self.assertTrue(root.findall('.//{' + P + '}sp'))
                self.assertEqual(root.find('.//{' + A + '}latin').get('typeface'), 'Oracle Sans')
        report = fixture.validate_pptx.check(path)
        self.assertEqual(report['file_integrity'], 'PASS', report)
        self.assertEqual(report['slide_order'][:2], ['ppt/slides/slide24.xml', 'ppt/slides/slide26.xml'])

    def test_pptx_scoped_annotation_check_rejects_protected_changes_on_same_slide(self):
        original = self.path.with_suffix('.pptx')
        edited = original.with_name('edited.pptx')
        shapes = ('<p:grpSp><p:nvGrpSpPr><p:cNvPr id="2" name="compute"/></p:nvGrpSpPr>'
                  '<p:grpSpPr><a:xfrm><a:off x="100" y="200"/></a:xfrm></p:grpSpPr></p:grpSp>'
                  '<p:sp><p:nvSpPr><p:cNvPr id="3" name="annotation"/></p:nvSpPr>'
                  '<p:txBody><a:p><a:r><a:t>Note</a:t></a:r></a:p></p:txBody></p:sp>'
                  '<p:cxnSp><p:nvCxnSpPr><p:cNvPr id="4" name="flow"/>'
                  '<p:cNvCxnSpPr><a:stCxn id="2" idx="0"/></p:cNvCxnSpPr></p:nvCxnSpPr></p:cxnSp>')
        parts = presentation_parts(shapes); part = 'ppt/slides/slide1.xml'
        write_package(original, parts)
        updated = dict(parts)
        updated[part] = updated[part].replace('>Note<', '>Revised note<')
        write_package(edited, updated)
        fixture.assert_pptx_preserved(original, edited, {(part, 'annotation')})
        for damage in ('geometry', 'group', 'connector'):
            tree = E.fromstring(updated[part])
            if damage == 'geometry':
                tree.find('.//{' + A + '}off').set('x','999')
            elif damage == 'group':
                parent = tree.find('.//{' + P + '}spTree')
                parent.remove(parent.find('{' + P + '}grpSp'))
            else:
                tree.find('.//{' + A + '}stCxn').set('id','3')
            damaged = dict(updated); damaged[part] = E.tostring(tree)
            write_package(edited, damaged)
            with self.subTest(damage=damage), self.assertRaises(AssertionError):
                fixture.assert_pptx_preserved(original, edited, {(part, 'annotation')})


if __name__ == '__main__':
    unittest.main()
