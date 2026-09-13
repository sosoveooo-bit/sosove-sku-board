import copy
import hashlib
import unittest
from unittest.mock import patch
from io import BytesIO
from types import SimpleNamespace

from sku_board import backend, cod_prompt_contract as contract, cod_prompt_render


def form_fixture(**changes):
    return contract.normalize_form({
        "product": "便携榨汁杯", "market": "DE", "main": 5, "detail": 5,
        "points": ["随行鲜榨", "USB充电"], "style": "明亮番茄红与奶油白，充电页为桌面场景",
        "discount": "20% OFF", "codText": "Nachnahme", "allowPromo": True,
        **changes,
    })


def references_fixture(content=b"current-image", role="product"):
    return [{"index": 1, "name": "same-name.png", "sha256": hashlib.sha256(content).hexdigest(), "role": role}]


def outline_fixture(form):
    count = form["main"] + form["detail"]
    return {
        "masterPrompt": "PRODUCT-SPECIFIC-MASTER 原文包含20% OFF和自选配色。",
        "hooks": [{"source": point, "variants": [{"type": name, "text": f"Frischer Genuss {i}"} for name in ("pain", "effect", "scene")]} for i, point in enumerate(form["points"])],
        "outline": [{"page": i, "title": f"独立创意{i}", "focus": "USB充电" if i == 1 else "随行鲜榨", "archetype": "product-info" if i == count else "pain-grid" if i == 2 else "comparison" if i == 3 else "产品实景", "sourcePointIndexes": [2] if i == 1 else [1]} for i in range(1, count + 1)],
    }


class CodPromptContractTests(unittest.TestCase):
    def test_exact_counts_and_invalid_counts_are_never_silently_changed(self):
        form = form_fixture()
        self.assertEqual(form["main"] + form["detail"], 10)
        for changes in ({"main": 0}, {"detail": 41}, {"main": "5.5"}, {"size": "bad-size"}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                form_fixture(**changes)

    def test_content_identity_covers_image_bytes_roles_and_all_copy_inputs(self):
        form = form_fixture()
        baseline = contract.fingerprint(form, references_fixture())
        self.assertNotEqual(baseline, contract.fingerprint(form, references_fixture(b"new-same-name-image")))
        self.assertNotEqual(baseline, contract.fingerprint(form, references_fixture(role="detail")))
        self.assertNotEqual(baseline, contract.fingerprint(form_fixture(discount="30% OFF"), references_fixture()))
        self.assertEqual(baseline, contract.fingerprint(form_fixture(model="different-image-model", quality="medium", generationProfile="fast"), references_fixture()))

    def test_exact_compiler_preserves_master_scene_palette_promo_and_page_assignment(self):
        form = form_fixture()
        master = "CURRENT MASTER\nPalette #f26540 #fffaf0; 20% OFF. 特殊排版保留。"
        prompt = "USB充电为本页唯一主题。A unique charging scene with soft light. No juice-preparing action on this page."
        page = {"page": 1, "modelPrompt": prompt, "focus": "USB充电"}
        compiled = contract.compile_execution_prompt(form, master, page, references_fixture())
        self.assertIn(master, compiled)
        self.assertIn(prompt, compiled)
        self.assertIn(form["style"], compiled)
        self.assertIn("20% OFF", compiled)
        self.assertNotIn("No price, discount", compiled)
        self.assertNotIn("随行鲜榨", compiled)
        self.assertEqual(page["focus"], "USB充电")
        self.assertIn("750x1000", compiled)

    def test_outline_enforces_modules_and_source_coverage_without_reordering(self):
        form = form_fixture()
        raw = outline_fixture(form)
        normalized = contract.normalize_outline(raw, form)
        self.assertEqual(normalized["outline"][0]["focus"], "USB充电")
        self.assertEqual(normalized["outline"][-1]["archetype"], "product-info")
        for field in ("outline", "hooks"):
            bad = copy.deepcopy(raw)
            bad[field] = []
            with self.assertRaises(ValueError):
                contract.normalize_outline(bad, form)
        bad = copy.deepcopy(raw)
        bad["outline"][0]["sourcePointIndexes"] = [1]
        with self.assertRaisesRegex(ValueError, "遗漏"):
            contract.normalize_outline(bad, form)

    def test_reference_transport_cannot_remap_canonical_atelier_prompt(self):
        prompt = contract.compile_execution_prompt(form_fixture(), "Special current master", {"page": 1, "modelPrompt": "The primary product must come from reference image 2. Preserve the same saved reference numbering and lighting."}, references_fixture())
        refs = [("first.png", b"a", "image/png"), ("second.png", b"b", "image/png")]
        bound, bound_refs = backend.bind_ai_image_primary_reference(prompt, refs)
        self.assertEqual(bound, prompt)
        self.assertEqual(bound_refs, refs)

    def test_old_page_numbers_and_short_page_payloads_are_rejected(self):
        form = form_fixture()
        outline = contract.normalize_outline(outline_fixture(form), form)["outline"][0]
        with self.assertRaises(ValueError):
            contract.normalize_page({"page": 2, "modelPrompt": "stale"}, outline, form)
        with self.assertRaises(ValueError):
            contract.normalize_page({"page": 1, "modelPrompt": "empty"}, outline, form)


if __name__ == "__main__":
    unittest.main()
