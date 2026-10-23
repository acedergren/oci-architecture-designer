import base64
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import urllib.parse
import zipfile
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'skills/oci-drawio-designer'), str(ROOT / 'skills/oci-powerpoint-designer')]
import validate_drawio

P = 'http://schemas.openxmlformats.org/presentationml/2006/main'
A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PKG = 'http://schemas.openxmlformats.org/package/2006/relationships'


def presentation_parts(shapes='', slide_ids=None):
    return {
        '[Content_Types].xml': '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>'
            '<Override PartName="/ppt/slides/slide1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/></Types>',
        '_rels/.rels': f'<Relationships xmlns="{PKG}"><Relationship Id="r1" Type="{R}/officeDocument" Target="ppt/presentation.xml"/></Relationships>',
        'ppt/presentation.xml': f'<p:presentation xmlns:p="{P}" xmlns:r="{R}"><p:sldIdLst>' + (
            slide_ids if slide_ids is not None else '<p:sldId id="256" r:id="r1"/>') + '</p:sldIdLst></p:presentation>',
        'ppt/_rels/presentation.xml.rels': f'<Relationships xmlns="{PKG}"><Relationship Id="r1" Type="{R}/slide" Target="slides/slide1.xml"/></Relationships>',
        'ppt/slides/slide1.xml': f'<p:sld xmlns:p="{P}" xmlns:a="{A}"><p:cSld><p:spTree>{shapes}</p:spTree></p:cSld></p:sld>',
    }


def write_package(path, parts):
    with zipfile.ZipFile(path, 'w') as archive:
        for name, data in parts.items():
            archive.writestr(name, data)


class Drawio(unittest.TestCase):
    def check(self, body, compressed=False):
        xml = '<mxGraphModel><root><mxCell id="0"/><mxCell id="1" parent="0"/>' + body + '</root></mxGraphModel>'
        if compressed:
            compressor = zlib.compressobj(wbits=-15)
            xml = base64.b64encode(compressor.compress(urllib.parse.quote(xml).encode()) + compressor.flush()).decode()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'fixture.drawio'
            path.write_text('<mxfile><diagram name="Test">' + xml + '</diagram></mxfile>')
            return validate_drawio.check(path)

    def test_wrapped_compressed_graph_has_separate_unverified_reviews(self):
        result = self.check('<UserObject id="a" label="A"><mxCell parent="1" vertex="1"/></UserObject>'
                            '<mxCell id="b" parent="1" vertex="1"/><mxCell id="e" edge="1" source="a" target="b" parent="1"/>', True)
        self.assertEqual(result['graph_integrity'], 'PASS')
        self.assertEqual(result['visual_review'], 'NOT_VERIFIED')
        self.assertEqual(result['opening_review'], 'NOT_VERIFIED')

    def test_bad_ids_cycles_dangling_and_unattached_edges_fail(self):
        bodies = ['<mxCell id="a"/><mxCell id="a"/>', '<mxCell id="a" parent="b"/><mxCell id="b" parent="a"/>',
                  '<mxCell id="a" parent="missing"/>', '<mxCell id="e" edge="1" source="1"/>',
                  '<mxCell id="e" edge="1" source="1" target="missing"/>']
        for body in bodies:
            with self.subTest(body=body):
                self.assertEqual(self.check(body)['graph_integrity'], 'FAIL')


class Pptx(unittest.TestCase):
    def run_check(self, parts):
        import validate_pptx
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'fixture.pptx'
            write_package(path, parts)
            return validate_pptx.check(path)

    def test_valid_internal_targets_external_links_and_separate_review_status(self):
        parts = presentation_parts('<p:sp><p:nvSpPr><p:cNvPr id="2"/></p:nvSpPr></p:sp>')
        parts['ppt/slides/_rels/slide1.xml.rels'] = f'<Relationships xmlns="{PKG}"><Relationship Id="web" Type="{R}/hyperlink" Target="https://example.org" TargetMode="External"/></Relationships>'
        result = self.run_check(parts)
        self.assertEqual(result['file_integrity'], 'PASS')
        self.assertEqual(result['slide_order'], ['ppt/slides/slide1.xml'])
        self.assertEqual(len(result['external_relationships']), 1)
        self.assertEqual(result['visual_review'], 'NOT_VERIFIED')
        self.assertEqual(result['opening_review'], 'NOT_VERIFIED')

    def test_missing_relation_target_wrong_slide_order_duplicate_shape_and_connector_fail(self):
        variants = []
        missing = presentation_parts(); del missing['ppt/slides/slide1.xml']; variants.append(missing)
        variants.append(presentation_parts(slide_ids='<p:sldId id="256" r:id="missing"/>'))
        variants.append(presentation_parts('<p:sp><p:nvSpPr><p:cNvPr id="2"/></p:nvSpPr></p:sp>' * 2))
        variants.append(presentation_parts('<p:cxnSp><p:nvCxnSpPr><p:cNvPr id="3"/><p:cNvCxnSpPr><a:stCxn id="404" idx="0"/></p:cNvCxnSpPr></p:nvCxnSpPr></p:cxnSp>'))
        malformed = presentation_parts(); malformed['ppt/slides/slide1.xml'] = '<broken'; variants.append(malformed)
        for parts in variants:
            with self.subTest(parts=parts.keys()):
                self.assertEqual(self.run_check(parts)['file_integrity'], 'FAIL')

    def test_cli_outputs_json_and_nonzero_for_corrupt_zip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'corrupt.pptx'; path.write_bytes(b'corrupt')
            result = subprocess.run([sys.executable, str(ROOT / 'skills/oci-powerpoint-designer/validate_pptx.py'), str(path)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(json.loads(result.stdout)['file_integrity'], 'FAIL')

    def test_undeclared_markup_compatibility_prefix_fails(self):
        parts = presentation_parts()
        parts['ppt/slides/slide1.xml'] = parts['ppt/slides/slide1.xml'].replace(
            '</p:spTree>', '<mc:AlternateContent xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006">'
            '<mc:Choice Requires="p14"/><mc:Fallback/></mc:AlternateContent></p:spTree>')
        self.assertEqual(self.run_check(parts)['file_integrity'], 'FAIL')

    def test_invalid_opc_roots_missing_content_type_and_wrong_entrypoint_fail(self):
        variants = []
        for name in ['[Content_Types].xml', '_rels/.rels']:
            parts = presentation_parts(); parts[name] = '<wrong/>'; variants.append(parts)
        parts = presentation_parts(); parts['media.untyped'] = b'content'; variants.append(parts)
        parts = presentation_parts(); parts['_rels/.rels'] = parts['_rels/.rels'].replace('/officeDocument', '/notOfficeDocument'); variants.append(parts)
        parts = presentation_parts(); parts['[Content_Types].xml'] = parts['[Content_Types].xml'].replace(
            'application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml', 'application/xml'); variants.append(parts)
        for parts in variants:
            with self.subTest():
                self.assertEqual(self.run_check(parts)['file_integrity'], 'FAIL')


if __name__ == '__main__':
    unittest.main()
