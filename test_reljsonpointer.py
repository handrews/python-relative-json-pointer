import pytest
from reljsonpointer import (
    RelJsonPointer,
    RelJsonPointerDepthException,
    RelJsonPointerRootNameException,
    RelJsonPointerRootManipulationException,
    RelJsonPointerEndOfListException,
    RelJsonPointerIndexTypeException,
    RelJsonPointerInvalidPrefixException,
    RelJsonPointerDoesNotExistException,
    RelNotAbsoluteJsonPointerException,
)
from jsonpointer import JsonPointer, EndOfList


class TestConstructor:
    def _check(self, rjp, up, over, pointer, use_last):
        assert rjp._up_count == up
        assert rjp._over_count == over
        assert str(rjp._pointer) == pointer
        assert rjp._use_name_of_last == use_last

    def test_up_only(self):
        rjp = RelJsonPointer('2')
        self._check(rjp, 2, 0, '', False)

    def test_use_last(self):
        rjp = RelJsonPointer('0#')
        self._check(rjp, 0, 0, '', True)

    def test_with_pointer(self):
        rjp = RelJsonPointer('100/foo/bar')
        self._check(rjp, 100, 0, '/foo/bar', False)

    def test_with_index_forward_with_pointer(self):
        rjp = RelJsonPointer('5+9/things/-/stuff')
        self._check(rjp, 5, 9, '/things/-/stuff', False)

    def test_with_index_backward_no_pointer(self):
        rjp = RelJsonPointer('2-100')
        self._check(rjp, 2, -100, '', False)

    def test_with_index_and_use_last(self):
        # See https://github.com/json-schema-org/json-schema-spec/issues/1175
        # for questions as to whether this is part of the spec or not.
        rjp = RelJsonPointer('3+1#')
        self._check(rjp, 3, 1, '', True)

    def test_absolute(self):
        with pytest.raises(RelNotAbsoluteJsonPointerException):
            RelJsonPointer('/foo')

    def test_non_integer_prefix(self):
        with pytest.raises(RelJsonPointerInvalidPrefixException):
            RelJsonPointer('abc/def')

    def test_malformed_index_operator(self):
        with pytest.raises(RelJsonPointerInvalidPrefixException):
            RelJsonPointer('0*1/foo')

    def test_hash_without_numeric_prefix(self):
        with pytest.raises(RelJsonPointerInvalidPrefixException):
            RelJsonPointer('#')

    def test_index_without_numeric_prefix(self):
        with pytest.raises(RelJsonPointerInvalidPrefixException):
            RelJsonPointer('-1')


class TestToAbsolute:
    def test_root(self):
        assert RelJsonPointer('0').to_absolute(JsonPointer('')) == \
            (JsonPointer(''), False)

    def test_up(self):
        assert RelJsonPointer('1').to_absolute('/foo/0') == \
            (JsonPointer('/foo'), False)

    def test_forwards(self):
        assert RelJsonPointer('0+2').to_absolute('/10') == \
            (JsonPointer('/12'), False)

    def test_negative_index(self):
        assert RelJsonPointer('1-3').to_absolute('/1/bar') == \
            (JsonPointer('/-2'), False)

    def test_hash(self):
        assert RelJsonPointer('0#').to_absolute('/') == \
            (JsonPointer('/'), True)

    def test_manipulation_and_hash(self):
        # See https://github.com/json-schema-org/json-schema-spec/issues/1175
        # for questions as to whether this is part of the spec or not.
        assert RelJsonPointer('0-1#').to_absolute('/1') == \
            (JsonPointer('/0'), True)

    def test_manipulation_root(self):
        with pytest.raises(RelJsonPointerRootManipulationException):
            RelJsonPointer('1-2').to_absolute('/foo')

    def test_manipulation_object(self):
        with pytest.raises(RelJsonPointerIndexTypeException):
            RelJsonPointer('0+1/foo').to_absolute('/whoops')


class TestResolve:
    rjp = RelJsonPointer('0')

    def test_property(self):
        doc = {'foo': {'bar': 1}}
        assert id(self.rjp.resolve(doc, JsonPointer('/foo'))) == id(doc['foo'])

    def test_index(self):
        doc = [{'thing': 'stuff'}]
        assert id(self.rjp.resolve(doc, JsonPointer('/0'))) == id(doc[0])

    def test_end_of_list(self):
        assert isinstance(self.rjp.resolve([0, 1, 2], '/-'), EndOfList)

    def test_end_of_list_exception(self):
        with pytest.raises(RelJsonPointerEndOfListException):
            self.rjp.resolve([0, 1, 2], '/-', no_eol=True)

    def test_defaulting(self):
        default = [42]
        assert id(self.rjp.resolve({}, '/foo', default)) == id(default)


class TestResolveWithHash:
    rjp = RelJsonPointer('1#')

    def test_depth(self):
        with pytest.raises(RelJsonPointerDepthException):
            self.rjp.resolve({}, '')

    def test_property(self):
        doc = {'foo': [0]}
        assert self.rjp.resolve(doc, '/foo/0') == 'foo'

    def test_index(self):
        doc = [{'foo': 'bar'}]
        assert self.rjp.resolve(doc, '/0/foo') == 0

    def test_array_length(self):
        doc = [{'a': 0}, {'a': 1}]
        assert self.rjp.resolve(doc, '/-/a') == len(doc)

    def test_no_root_hash(self):
        with pytest.raises(RelJsonPointerRootNameException):
            RelJsonPointer('0#').resolve({}, '')

    def test_no_index(self):
        with pytest.raises(RelJsonPointerDoesNotExistException):
            RelJsonPointer('0#').resolve(['foo', 'bar'], '/2')

    def test_no_property(self):
        with pytest.raises(RelJsonPointerDoesNotExistException):
            RelJsonPointer('0#').resolve({'foo': 1, 'bar': 2}, '/baz')

    def test_index_with_use_last(self):
        # See https://github.com/json-schema-org/json-schema-spec/issues/1175
        # for questions as to whether this is part of the spec or not.
        rjp = RelJsonPointer('0+1#')
        assert rjp.resolve(['a', 'b'], '/0') == 1

    def test_index_with_use_last_out_of_bounds(self):
        # See https://github.com/json-schema-org/json-schema-spec/issues/1175
        # for questions as to whether this is part of the spec or not.
        rjp = RelJsonPointer('0+1#')
        with pytest.raises(Exception):
            rjp.resolve(['a', 'b'], '/1')
