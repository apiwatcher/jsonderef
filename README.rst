jsonderef
==========

A json dereferencing library for python.

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
  dereferencer = JsonDeref()

  print dereferencer.deref(document, max_deref_depth=5)

Tests
======

Clone the repo, install dependencies and run nose.

.. code-block:: shell

  virtualenv env
  . env/bin/activate

  pip install -r requirements.txt

  nosetests tests.py
