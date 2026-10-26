import unittest

from bugbench import patches

DIFF = """diff --git a/src/a.py b/src/a.py
index 1111111..2222222 100644
--- a/src/a.py
+++ b/src/a.py
@@ -1 +1 @@
-x = 1
+x = 2
diff --git a/tests/test_a.py b/tests/test_a.py
new file mode 100644
index 0000000..3333333
--- /dev/null
+++ b/tests/test_a.py
@@ -0,0 +1 @@
+assert True
diff --git a/old.txt b/old.txt
deleted file mode 100644
index 4444444..0000000
--- a/old.txt
+++ /dev/null
@@ -1 +0,0 @@
-gone
diff --git a/CHANGELOG.md b/CHANGELOG.md
index 5555555..6666666 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -1 +1,2 @@
+- fix
 # Changelog
"""


class PatchesTest(unittest.TestCase):
    def test_parse_paths(self):
        files = patches.parse(DIFF)
        self.assertEqual([f.path for f in files], ["src/a.py", "tests/test_a.py", "old.txt", "CHANGELOG.md"])
        self.assertIsNone(files[1].old_path)
        self.assertIsNone(files[2].new_path)
        self.assertEqual(patches.created_paths(DIFF), ["tests/test_a.py"])

    def test_split(self):
        gold, test = patches.split(DIFF, ["tests/*"], ["CHANGELOG.md"])
        self.assertEqual(patches.touched_paths(gold), ["src/a.py", "old.txt"])
        self.assertEqual(patches.touched_paths(test), ["tests/test_a.py"])

    def test_rejects_garbage(self):
        with self.assertRaises(ValueError):
            patches.parse("not a diff\n")

    def test_empty(self):
        self.assertEqual(patches.parse(""), [])


if __name__ == "__main__":
    unittest.main()
