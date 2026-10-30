"""View contract regressions; synthetic graphs only, no Oracle artwork."""
import base64
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import urllib.parse
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills/oci-drawio-designer'))
import validate_drawio as validator


BODY = ('<mxCell id="0"/><mxCell id="infra" value="Infrastructure" parent="0" style="locked=1;"/>'
        '<mxCell id="flows" value="Flows" parent="0"/>'
        '<mxCell id="notes" value="Annotations" parent="0" visible="0"/>'
        '<mxCell id="vcn" parent="infra" vertex="1"/>'
        '<mxCell id="subnet" parent="vcn" vertex="1"/>'
        '<UserObject id="app" label="App"><mxCell vertex="1" parent="subnet"/></UserObject>'
        '<object id="db" label="Database"><mxCell vertex="1" parent="subnet"/></object>'
        '<mxCell id="status" parent="infra" vertex="1" value="Proposed synthetic"/>'
        '<mxCell id="sql" parent="flows" edge="1" source="app" target="db"/>'
        '<mxCell id="note" parent="notes" vertex="1"/>')


def declaration():
    overview = dict(id='overview', purpose='Deployment overview', status='proposed',
                    visible_layer_ids=['infra', 'flows'], hidden_layer_ids=['notes'],
                    required_cell_ids=['vcn', 'subnet', 'app', 'db', 'status', 'sql'], omissions=[])
    detail = dict(overview, id='detail', purpose='Deployment details',
                  visible_layer_ids=['infra', 'flows', 'notes'], hidden_layer_ids=[])
    return dict(schema_version=1, pages=[dict(page_name='Deployment',
                layers=[dict(id='infra', name='Infrastructure', locked=True),
                        dict(id='flows', name='Flows', locked=False),
                        dict(id='notes', name='Annotations', locked=False)],
                saved_view_id='overview', views=[overview, detail])])


class LayerViews(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / 'test.drawio'
        self.sidecar = self.path.with_suffix('.views.json')

    def run_graph(self, manifest=None, body=BODY, compressed=False, extra=''):
        model = '<mxGraphModel><root>' + body + '</root></mxGraphModel>'
        if compressed:
            c = zlib.compressobj(wbits=-15)
            model = base64.b64encode(c.compress(urllib.parse.quote(model).encode()) + c.flush()).decode()
        self.path.write_text('<mxfile><diagram name="Deployment">' + model + '</diagram>' + extra + '</mxfile>')
        before = self.path.read_bytes()
        if manifest is not None:
            self.sidecar.write_text(json.dumps(manifest))
        result = validator.check(self.path, self.sidecar if manifest is not None else None)
        self.assertEqual(self.path.read_bytes(), before, 'Validator must not mutate source')
        return result

    def test_nested_wrapped_cross_layer_edges_and_default_states_pass(self):
        result = self.run_graph(declaration(), compressed=True)
        self.assertEqual(result['layer_view_integrity'], 'PASS', result)
        self.assertEqual(result['graph_integrity'], 'PASS')
        self.assertEqual(result['layer_inventory'][0]['layers'], [
            dict(id='infra', name='Infrastructure', locked=True, visible=True),
            dict(id='flows', name='Flows', locked=False, visible=True),
            dict(id='notes', name='Annotations', locked=False, visible=False)])
        for field in ('opening_review', 'visual_review', 'editability_review'):
            self.assertEqual(result[field], 'NOT_VERIFIED')

    def test_single_unnamed_layer_without_sidecar_keeps_legacy_result(self):
        r = self.run_graph(body='<mxCell id="0"/><mxCell id="1" parent="0"/>')
        self.assertEqual(r['graph_integrity'], 'PASS')
        self.assertEqual(r['layer_view_integrity'], 'NOT_VERIFIED')

    def test_contract_errors_are_separate_from_graph_errors(self):
        variants = []
        def variant(change):
            m = declaration(); change(m, m['pages'][0]); variants.append(m)
        variant(lambda m,p: m.update(schema_version=True))
        variant(lambda m,p: m.update(pages=[]))
        variant(lambda m,p: p.update(page_name='Missing'))
        variant(lambda m,p: m['pages'].append(copy.deepcopy(p)))
        variant(lambda m,p: p['layers'][1].update(id='infra'))
        variant(lambda m,p: p['layers'][1].update(name='Infrastructure'))
        variant(lambda m,p: p['layers'][0].update(locked='true'))
        variant(lambda m,p: p['layers'].reverse())
        variant(lambda m,p: p['layers'][0].update(locked=False))
        variant(lambda m,p: p.update(saved_view_id='missing'))
        variant(lambda m,p: p['views'][1].update(id='overview'))
        variant(lambda m,p: p['views'][0].update(purpose=''))
        variant(lambda m,p: p['views'][0].update(required_cell_ids=['missing']))
        variant(lambda m,p: p['views'][0].update(required_cell_ids=[]))
        variant(lambda m,p: p['views'][0].update(hidden_layer_ids=['flows', 'notes']))
        variant(lambda m,p: p['views'][0].update(hidden_layer_ids=[]))
        variant(lambda m,p: p['views'][0].update(visible_layer_ids=['infra','flows','missing']))
        variant(lambda m,p: p['views'][0].update(visible_layer_ids=['infra','infra','flows']))
        variant(lambda m,p: p['views'][0].update(omissions=[dict(model_id='db', reason='')]))
        for m in variants:
            with self.subTest(manifest=m):
                r = self.run_graph(m)
                self.assertEqual(r['layer_view_integrity'], 'FAIL', r)
                self.assertTrue(r['layer_view_errors'])
                self.assertEqual(r['graph_integrity'], 'PASS')
                self.assertEqual(r['errors'], [])

    def test_hidden_or_collapsed_ancestry_cannot_satisfy_required_cells(self):
        for attr in ('visible="0"', 'collapsed="1"'):
            with self.subTest(attr=attr):
                body = BODY.replace('id="subnet"', 'id="subnet" ' + attr)
                self.assertEqual(self.run_graph(declaration(), body)['layer_view_integrity'], 'FAIL')

    def test_hidden_critical_flow_and_hidden_terminals_fail_each_declared_view(self):
        for required in (True, False):
            m = declaration()
            v = m['pages'][0]['views'][1]
            v.update(visible_layer_ids=['flows','notes'], hidden_layer_ids=['infra'])
            if not required:
                v['required_cell_ids'] = ['note']
            r = self.run_graph(m)
            self.assertEqual(r['layer_view_integrity'], 'FAIL')
        m = declaration(); v = m['pages'][0]['views'][1]
        v.update(visible_layer_ids=['infra','notes'], hidden_layer_ids=['flows'])
        self.assertEqual(self.run_graph(m)['layer_view_integrity'], 'FAIL')

    def test_saved_visibility_and_ambiguous_page_names_fail(self):
        body = BODY.replace('id="notes" value="Annotations" parent="0" visible="0"',
                            'id="notes" value="Annotations" parent="0"')
        self.assertEqual(self.run_graph(declaration(), body)['layer_view_integrity'], 'FAIL')
        extra = '<diagram name="Deployment"><mxGraphModel><root><mxCell id="0"/></root></mxGraphModel></diagram>'
        self.assertEqual(self.run_graph(declaration(), extra=extra)['layer_view_integrity'], 'FAIL')

    def test_undeclared_pages_retain_legacy_names(self):
        extra = '<diagram name="Legacy"><mxGraphModel><root><mxCell id="0"/><mxCell id="1" parent="0"/></root></mxGraphModel></diagram>'
        self.assertEqual(self.run_graph(declaration(), extra=extra)['layer_view_integrity'], 'PASS')

    def test_cli_sidecar_failure_emits_json_and_nonzero(self):
        self.run_graph()
        for content in ('{bad', 'null', '[]'):
            self.sidecar.write_text(content)
            r = subprocess.run([sys.executable, '-B', str(validator.__file__), str(self.path),
                                '--views', str(self.sidecar)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 1)
            report = json.loads(r.stdout)
            self.assertEqual(report['layer_view_integrity'], 'FAIL')
            self.assertEqual(report['graph_integrity'], 'PASS')
        self.sidecar.unlink()
        self.assertEqual(validator.check(self.path, self.sidecar)['layer_view_integrity'], 'FAIL')


if __name__ == '__main__':
    unittest.main()
