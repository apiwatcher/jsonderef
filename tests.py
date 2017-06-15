# -*- coding: utf-8 -*-
import unittest
import json
from jsonderef import JsonDeref, RefNotFound

class JsonDerefTests(unittest.TestCase):
    """
    Tests for deref function
    """

    def simple_deref_test(self):
        """
        Trivial derefs should pass
        """
        cases = [
            {
                "in": {"key": "value"},
                "out": {"key": "value"}
            },
            {
                "in": {"key": "value", "ref": {"$ref": "#/key"}},
                "out": {"key": "value", "ref": "value"}
            },
            {
                "in": {"key": "value", "ref": [{"$ref": "#/key"}]},
                "out": {"key": "value", "ref": ["value"]}
            },
            {
                "in": {"key": 1, "ref": {"$ref": "#/key"}},
                "out": {"key": 1, "ref": 1}
            },
            {
                "in": {"key": 1.23, "ref": {"$ref": "#/key"}},
                "out": {"key": 1.23, "ref": 1.23}
            },
            {
                "in": {"key": True, "ref": {"$ref": "#/key"}},
                "out": {"key": True, "ref": True}
            },
            {
                "in": {"key": [], "ref": {"$ref": "#/key"}},
                "out": {"key": [], "ref": []}
            },
            {
                "in": {"key": [1,2], "ref": {"$ref": "#/key"}},
                "out": {"key": [1,2], "ref": [1,2]}
            },
            {
                "in": {"key": {}, "ref": {"$ref": "#/key"}},
                "out": {"key":  {}, "ref":  {}}
            },
            {
                "in": {"key": {"a": 1}, "ref": {"$ref": "#/key"}},
                "out": {"key":  {"a": 1}, "ref":  {"a": 1}}
            },
            {
                "in": {
                    "key": u"Žluťoučký kůň úpěl ďábelské ódy",
                    "ref": {"$ref": "#/key"}
                },
                "out": {
                    "key": u"Žluťoučký kůň úpěl ďábelské ódy",
                    "ref": u"Žluťoučký kůň úpěl ďábelské ódy"
                }
            }
        ]

        for case in cases:
            real_output = JsonDeref(case["in"]).deref()
            self.assertDictEqual(
                real_output, case["out"],
                "Deref of {0} should produce {1} but produces {2}".format(
                    json.dumps(case["in"], indent=2),
                    json.dumps(case["out"], indent=2),
                    json.dumps(real_output, indent=2)
                )
            )

    def errors_test(self):
        """
        Errors should be properly handled
        """
        with self.assertRaises(RefNotFound):
            JsonDeref({"$ref": "#/key"}).deref()

        with self.assertRaises(RefNotFound):
            JsonDeref({"key": [], "ref": {"$ref": "#/key/1"}}).deref()

        with self.assertRaises(RefNotFound):
            JsonDeref({"key": {},  "ref": {"$ref": "#/key/a"}}).deref()

        self.assertEqual(
            JsonDeref({"$ref": "#/key"}, raise_on_not_found=False).deref(),
            None
        )
        self.assertEqual(
            JsonDeref(
                {"key": [], "ref": {"$ref": "#/key/1"}},
                raise_on_not_found=False
            ).deref(),
            {"key": [], "ref": None}
        )
        self.assertEqual(
            JsonDeref(
                {"key": {},  "ref": {"$ref": "#/key/a"}},
                raise_on_not_found=False
            ).deref(),
            {"key": {}, "ref": None}
        )

        self.assertEqual(
            JsonDeref(
                {"$ref": "#/key"},
                raise_on_not_found=False,
                not_found="Not found"
            ).deref(),
            "Not found"
        )

    def recursive_test(self):
        """
        Max depth should be correctly handled
        """
        # Reference the reference - does not nest
        doc = {"a": {"$ref": "#/a"}}

        for i in range(1,100):
            output = JsonDeref(doc).deref(100)
            depth = 0
            while output.get("a",None) is not None:
                output = output["a"]
                depth += 1

            self.assertEqual(depth, 1)

        # Reference the entire object which has a reference inside - nests
        doc = {"a": {"$ref": "#"}}

        for i in range(1,100):
            output = JsonDeref(doc).deref(i)
            depth = 0
            while output.get("a",None) is not None:
                output = output["a"]
                depth += 1

            self.assertEqual(depth, i+1)

    def rfc_test(self):
        """
        Deref should be compliant with rfc 6901
        """
        doc = {
            "foo": ["bar", "baz"],
            "": 0,
            "a/b": 1,
            "c%d": 2,
            "e^f": 3,
            "g|h": 4,
            "i\\j": 5,
            "k\"l": 6,
            " ": 7,
            "m~n": 8
        }

        ref_key_values = [
            ["#/foo", ["bar", "baz"]],
            ["#/foo/0", "bar"],
            ["#/", 0],
            ["#/a~1b", 1],
            ["#/c%d", 2],
            ["#/e^f", 3],
            ["#/g|h", 4],
            ["#/i\\j", 5],
            ["#/k\"l", 6],
            ["#/ ", 7],
            ["#/m~0n", 8],
            [
                "#",
                {
                    "foo": ["bar", "baz"],
                    "": 0,
                    "a/b": 1,
                    "c%d": 2,
                    "e^f": 3,
                    "g|h": 4,
                    "i\\j": 5,
                    "k\"l": 6,
                    " ": 7,
                    "m~n": 8,
                    "ref": {"$ref": "#"}
                }
            ]
        ]

        for m in ref_key_values:
            doc["ref"] = {"$ref": m[0]}
            real_output = JsonDeref(doc).deref(1)
            self.assertEqual(
                real_output["ref"], m[1],
                "Key ref in {0} should be {1} after deref but it is {2}".format(
                    json.dumps(doc, indent=2),
                    json.dumps(m[1], indent=2),
                    json.dumps(real_output["ref"], indent=2)
                )
            )
