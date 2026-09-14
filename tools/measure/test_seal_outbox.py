"""Tests for the seal, including the exact failure that broke comparator 0.1.0."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seal_outbox as seal  # noqa: E402


def repository():
    root = tempfile.mkdtemp()
    run = lambda *args: subprocess.run(["git", "-C", root, *args], capture_output=True, check=True)
    run("init", "-q")
    run("config", "user.name", "Daniel Wahnich")
    run("config", "user.email", "cogitoergosum143@gmail.com")
    with open(os.path.join(root, "kept.json"), "w", encoding="utf-8") as handle:
        handle.write('{"version": "1"}\n')
    run("add", "-A")
    run("commit", "-q", "-m", "one")
    head = subprocess.run(["git", "-C", root, "rev-parse", "HEAD"],
                          capture_output=True, text=True, check=True).stdout.strip()
    return root, head


class Seal(unittest.TestCase):
    def setUp(self):
        self.root, self.head = repository()
        self.outbox = tempfile.mkdtemp()

    def write(self, name, text):
        with open(os.path.join(self.outbox, name), "w", encoding="utf-8") as handle:
            handle.write(text)

    def test_a_committed_payload_is_verified_against_its_blob(self):
        self.write("kept.json", '{"version": "1"}\n')
        result = seal.seal(self.outbox, self.root, self.head, {"kept.json": "kept.json"})
        self.assertEqual(result["committed"], 1)
        self.assertEqual(result["generated"], 0)
        with open(os.path.join(self.outbox, "MANIFEST.json"), encoding="utf-8") as handle:
            manifest = json.load(handle)
        self.assertEqual(manifest["files"][0]["origin"], "committed")
        self.assertEqual(manifest["files"][0]["verified_against"], f"{self.head}:kept.json")

    def test_the_comparator_failure_is_refused_rather_than_sealed(self):
        """A generated status shipped under a committed path with different bytes."""
        self.write("kept.json", '{"version": "2"}\n')
        with self.assertRaises(seal.SealError) as caught:
            seal.seal(self.outbox, self.root, self.head, {"kept.json": "kept.json"})
        self.assertIn("bytes differ", str(caught.exception))
        self.assertFalse(os.path.exists(os.path.join(self.outbox, "MANIFEST.json")))

    def test_a_declared_path_absent_from_the_commit_is_refused(self):
        self.write("kept.json", '{"version": "1"}\n')
        with self.assertRaises(seal.SealError) as caught:
            seal.seal(self.outbox, self.root, self.head, {"kept.json": "nowhere.json"})
        self.assertIn("is not in", str(caught.exception))
        self.assertFalse(os.path.exists(os.path.join(self.outbox, "MANIFEST.json")))

    def test_a_generated_payload_is_never_described_as_committed(self):
        self.write("kept.json", '{"version": "1"}\n')
        self.write("status.json", '{"generated": true}\n')
        result = seal.seal(self.outbox, self.root, self.head, {"kept.json": "kept.json"})
        self.assertEqual(result["committed"], 1)
        self.assertEqual(result["generated"], 1)
        with open(os.path.join(self.outbox, "MANIFEST.json"), encoding="utf-8") as handle:
            manifest = json.load(handle)
        generated = [f for f in manifest["files"] if f["outbox_file"] == "status.json"][0]
        self.assertEqual(generated["origin"], "generated")
        self.assertIsNone(generated["repository_path"])

    def test_the_manifest_digest_is_the_manifest_bytes(self):
        self.write("kept.json", '{"version": "1"}\n')
        result = seal.seal(self.outbox, self.root, self.head, {"kept.json": "kept.json"})
        with open(os.path.join(self.outbox, "MANIFEST.json"), "rb") as handle:
            self.assertEqual(seal.digest_bytes(handle.read()), result["manifest_sha256"])
        with open(os.path.join(self.outbox, "MANIFEST.sha256"), encoding="utf-8") as handle:
            self.assertTrue(handle.read().startswith(result["manifest_sha256"]))

    def test_no_sentence_speaks_for_every_payload_at_once(self):
        self.write("kept.json", '{"version": "1"}\n')
        self.write("status.json", '{"generated": true}\n')
        seal.seal(self.outbox, self.root, self.head, {"kept.json": "kept.json"})
        with open(os.path.join(self.outbox, "MANIFEST.json"), encoding="utf-8") as handle:
            manifest = json.load(handle)
        self.assertIn("No statement here covers all payloads at once",
                      manifest["origin_policy"])
        for entry in manifest["files"]:
            self.assertIn("origin", entry)


class TransportBoundary(unittest.TestCase):
    """A publisher cannot verify its own transport, and the seal refuses to say it did."""

    def setUp(self):
        self.root, self.head = repository()
        self.outbox = tempfile.mkdtemp()
        with open(os.path.join(self.outbox, "kept.json"), "w", encoding="utf-8") as handle:
            handle.write('{"version": "1"}\n')

    def test_every_manifest_carries_the_asserted_unverified_state(self):
        seal.seal(self.outbox, self.root, self.head, {"kept.json": "kept.json"})
        with open(os.path.join(self.outbox, "MANIFEST.json"), encoding="utf-8") as handle:
            manifest = json.load(handle)
        self.assertEqual(manifest["transport_verification_state"], "asserted_unverified")
        self.assertIn("publisher", manifest["transport_boundary"])

    def test_the_comparator_0_2_0_wording_is_refused(self):
        """The exact field that shipped in comparator-0.2.0's sealed manifest."""
        header = {"publication": {
            "independent_transport_verification":
                "a fresh clone of the pushed ref returned the same tree"}}
        with self.assertRaises(seal.SealError) as caught:
            seal.seal(self.outbox, self.root, self.head, {"kept.json": "kept.json"}, header)
        self.assertIn("publisher readback", str(caught.exception))
        self.assertFalse(os.path.exists(os.path.join(self.outbox, "MANIFEST.json")))

    def test_the_claim_is_refused_in_a_value_as_well_as_a_key(self):
        header = {"note": "this clone is an independent transport verification of the push"}
        with self.assertRaises(seal.SealError):
            seal.seal(self.outbox, self.root, self.head, {"kept.json": "kept.json"}, header)

    def test_an_honest_publisher_readback_header_is_accepted(self):
        header = {"publication": {"publisher_readback": "a fresh clone returned the same tree"}}
        result = seal.seal(self.outbox, self.root, self.head, {"kept.json": "kept.json"}, header)
        self.assertEqual(result["committed"], 1)


if __name__ == "__main__":
    unittest.main()
