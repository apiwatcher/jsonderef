jsonderef
==========

A json dereferencing tool for python.

Currently only local references are supported but file and remote references
are comming soon.

Json pointers evaluation is compliant with rfc 6901
(https://tools.ietf.org/html/rfc6901).

Installation
=============

Best way is to use *pip*.

.. code-block:: shell

  pip install jsonderef


Usage
======

.. code-block:: python

  from jsonderef import JsonDeref

  document = {
    "key": "value",
    "ref": {"$ref": "#/key"},
    "array_ref": [ {"$ref": "#/key"}],
    "nested_ref": { "nest": {"$ref": "#/nested_ref"}}
  }
  dereferencer = JsonDeref(document)

  print dereferencer.deref(max_deref_depth=5)
