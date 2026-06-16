from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class PanoramaContractTests(unittest.TestCase):
    def test_panorama_routes_are_registered_and_authenticated(self):
        source = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
        route_specs = (
            ("get", "/panorama/tree"),
            ("get", "/panorama/stats"),
            ("get", "/panorama/layers"),
            ("post", "/panorama/layers"),
            ("put", "/panorama/layers/{layer_id}"),
            ("delete", "/panorama/layers/{layer_id}"),
            ("get", "/panorama/nodes"),
            ("post", "/panorama/nodes"),
            ("put", "/panorama/nodes/{node_id}"),
            ("delete", "/panorama/nodes/{node_id}"),
            ("get", "/panorama/tags"),
            ("post", "/panorama/tags"),
            ("put", "/panorama/tags/{tag_id}"),
            ("delete", "/panorama/tags/{tag_id}"),
            ("get", "/panorama/slots"),
            ("post", "/panorama/slots"),
            ("put", "/panorama/slots/{slot_id}"),
            ("delete", "/panorama/slots/{slot_id}"),
        )

        for method, route in route_specs:
            pattern = (
                r"@app\.{}\([\"']{}[\"'][^\n]*\)\s*"
                r"def\s+\w+\((.*?)\):"
            ).format(method, re.escape(route))
            match = re.search(pattern, source, re.S)
            self.assertIsNotNone(match, "{} {} route must be registered".format(method.upper(), route))
            self.assertIn(
                "Depends(get_current_user)",
                match.group(1),
                "{} {} route must require get_current_user".format(method.upper(), route),
            )

    def test_panorama_schemas_exist_in_pydantic_v1_style(self):
        source = (ROOT / "app" / "schemas.py").read_text(encoding="utf-8")
        for name in (
            "PanoramaLayerCreate",
            "PanoramaLayerUpdate",
            "PanoramaNodeCreate",
            "PanoramaNodeUpdate",
            "PanoramaTagCreate",
            "PanoramaTagUpdate",
            "PanoramaSlotCreate",
            "PanoramaSlotUpdate",
            "PanoramaTreeResponse",
            "PanoramaStatsResponse",
        ):
            self.assertRegex(source, r"class\s+{}\(BaseModel\):".format(name))

        self.assertNotIn("model_config", source)
        self.assertNotIn("ConfigDict", source)

    def test_panorama_store_defines_crud_and_read_models(self):
        store_path = ROOT / "app" / "services" / "panorama_store.py"
        self.assertTrue(store_path.exists(), "panorama_store.py must exist")

        source = store_path.read_text(encoding="utf-8")
        for name in (
            "get_panorama_tree",
            "get_panorama_stats",
            "create_layer",
            "update_layer",
            "delete_layer",
            "create_node",
            "update_node",
            "delete_node",
            "create_tag",
            "update_tag",
            "delete_tag",
            "create_slot",
            "update_slot",
            "delete_slot",
        ):
            self.assertRegex(source, r"def\s+{}\(".format(name))

    def test_init_schema_runs_panorama_migration(self):
        source = (ROOT / "app" / "core" / "db.py").read_text(encoding="utf-8")

        self.assertIn("003_panorama.sql", source)
        self.assertIn('_run_migration(cursor, "003_panorama.sql")', source)


if __name__ == "__main__":
    unittest.main()
