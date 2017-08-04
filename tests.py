# -*- coding: utf-8 -*-
import unittest
import json
import httpretty

from jsonderef import JsonDeref, RefNotFound, JsonDerefException

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
            real_output = JsonDeref().deref(case["in"])
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
            JsonDeref().deref({"$ref": "#/key"})

        with self.assertRaises(RefNotFound):
            JsonDeref().deref({"key": [], "ref": {"$ref": "#/key/1"}})

        with self.assertRaises(RefNotFound):
            JsonDeref().deref({"key": {},  "ref": {"$ref": "#/key/a"}})

        self.assertEqual(
            JsonDeref(raise_on_not_found=False).deref({"$ref": "#/key"}),
            None
        )
        self.assertEqual(
            JsonDeref(raise_on_not_found=False).deref(
                {"key": [], "ref": {"$ref": "#/key/1"}}
            ),
            {"key": [], "ref": None}
        )
        self.assertEqual(
            JsonDeref(raise_on_not_found=False).deref(
                {"key": {},  "ref": {"$ref": "#/key/a"}}
            ),
            {"key": {}, "ref": None}
        )

        self.assertEqual(
            JsonDeref(raise_on_not_found=False, not_found="Not found").deref(
                {"$ref": "#/key"}
            ),
            "Not found"
        )


    def recursive_test(self):
        """
        Max depth should be correctly handled
        """
        # Reference the reference - does not nest
        doc = {"a": {"$ref": "#/a"}}

        for i in range(1,100):
            output = JsonDeref().deref(doc, 100)
            depth = 0
            while output.get("a",None) is not None:
                output = output["a"]
                depth += 1

            self.assertEqual(depth, 1)

        # Reference the entire object which has a reference inside - nests
        doc = {"a": {"$ref": "#"}}

        for i in range(1,100):
            output = JsonDeref().deref(doc, i)
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
            real_output = JsonDeref().deref(doc, 1)
            self.assertEqual(
                real_output["ref"], m[1],
                "Key ref in {0} should be {1} after deref but it is {2}".format(
                    json.dumps(doc, indent=2),
                    json.dumps(m[1], indent=2),
                    json.dumps(real_output["ref"], indent=2)
                )
            )

    @httpretty.activate
    def remote_url_test(self):
        """
        It should be possible to get ref from remote urls
        """
        remote_doc = {
            "key": "value",
            "object": {
                "key": "value"
            },
            "array": [1,2,3,4,5],
            "self_ref_to_key": {
                "$ref": "#/key"
            },
            "self_ref_recursive": {
                "$ref": "#"
            },
            "self_ref_url": {
                "$ref": "http://200.uri#"
            }
        }

        httpretty.reset()
        httpretty.register_uri(
            httpretty.GET, "http://200.uri", body=json.dumps(remote_doc)
        )

        chain_len = 50
        for i in range(0, chain_len):
            httpretty.register_uri(
                httpretty.GET, "http://{0}.uri".format(i),
                body=json.dumps({
                    "key": {"$ref": "http://{0}.uri#/key".format(i+1)}
                })
            )
        httpretty.register_uri(
            httpretty.GET, "http://{0}.uri".format(chain_len),
            body=json.dumps({
                "key": "value"
            })
        )

        cases = [
            {
                "in": {"key": {"$ref": "http://200.uri#/key"}},
                "out": {"key": "value"},
                "max_depth": 10
            },
            {
                "in": {"key": {"$ref": "http://200.uri#/object"}},
                "out": {"key": {"key": "value"}},
                "max_depth": 10
            },
            {
                "in": {"key": {"$ref": "http://200.uri#/array"}},
                "out": {"key": [1,2,3,4,5]},
                "max_depth": 10
            },
            {
                "in": {"key": {"$ref": "http://200.uri#/self_ref_to_key"}},
                "out": {"key": "value"},
                "max_depth": 10
            },
            {
                # Yeah, this returns "local-like" reference
                "in": {"key": {"$ref": "http://200.uri#/self_ref_to_key"}},
                "out": {"key": {"$ref": "#/key"}},
                "max_depth": 1
            },
            {
                "in": {"$ref": "http://200.uri#"},
                "out": remote_doc,
                "max_depth": 1
            },
            {
                # Chain
                "in": {"key": {"$ref": "http://0.uri#/key"}},
                "out": {"key": "value"},
                "max_depth": chain_len + 1
            }
        ]

        for case in cases:
            real_output = JsonDeref().deref(case["in"], case["max_depth"])
            self.assertDictEqual(
                real_output, case["out"],
                "Deref of {0} should produce {1} but produces {2}".format(
                    json.dumps(case["in"], indent=2),
                    json.dumps(case["out"], indent=2),
                    json.dumps(real_output, indent=2)
                )
            )

    @httpretty.activate
    def remote_url_errors_test(self):
        """
        Remote urls should correclty raise errors
        """
        httpretty.reset()
        httpretty.register_uri(
            httpretty.GET, "http://400.uri", status=400
        )
        with self.assertRaises(RefNotFound):
            JsonDeref().deref(
                {"ref": {"$ref": "http://400.uri#"}}
            )

        res = JsonDeref(raise_on_not_found=False).deref(
            {"ref": {"$ref": "http://400.uri#"}}
        )
        self.assertDictEqual(res, {"ref": None})

        httpretty.register_uri(
            httpretty.GET, "http://200.uri", status=200, body="Not a json"
        )
        with self.assertRaises(JsonDerefException):
            JsonDeref().deref(
                {"ref": {"$ref": "http://200.uri#"}}
            )
        with self.assertRaises(JsonDerefException):
            JsonDeref(raise_on_not_found=False).deref(
                {"ref": {"$ref": "http://200.uri#"}}
            )
