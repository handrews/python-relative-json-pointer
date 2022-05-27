# python-relative-json-pointer
Relative JSON Pointer implementation in Python

_**WARNING:** This project is in the earliest stages of development, although
I am reasonably sure that it works.  I intend to polish it and publish it
properly during Summer 2022, particularly if I can get the following
issues resolved in a new draft release:_

* [#1235](https://github.com/json-schema-org/json-schema-spec/issues/1235) _or_ [#1236](https://github.com/json-schema-org/json-schema-spec/issues/1236), which are two proposals to allow using Relative JSON Pointer's `#` opeator on JSON Pointers that use the `-` special index operator.  Technically, #1235 would be needed in order for the way this library works to be considered correct, as it is implemented by resolving against a base pointer and applying the resulting RFC 9601 JSON Pointer rather than directly operating on an instance.  This is useful as parent traversals are difficult in most in-memory representations of JSON (although see jschon's [RelativeJSONPointer](https://jschon.readthedocs.io/en/latest/reference/jsonpointer.html#jschon.jsonpointer.RelativeJSONPointer) and [JSON](https://jschon.readthedocs.io/en/latest/reference/json.html#jschon.json.JSON) classes for an implementation using a parent-aware data structure).

* [#1175](https://github.com/json-schema-org/json-schema-spec/issues/1175), which clarifies that index manipulation and `#` _can_ be used together, even though we forgot to put it in the ABNF.

And possibly [anything else tagged with "rel json pointer"](https://github.com/json-schema-org/json-schema-spec/issues?q=is%3Aissue+is%3Aopen+label%3A%22rel+json+pointer%22).

_**Please do** feel free to file issues if you notice a problem or have a need for
it to be on PyPI sooner._
