import pytest
from reljsonpointer import (
    RelJsonPointer,
    RelJsonPointerDepthException,
    RelJsonPointerEndOfListException,
    RelJsonPointerIndexTypeException,
    RelJsonPointerInvalidPrefixException,
    RelJsonPointerRootNameException,
    RelNotAbsoluteJsonPointerException,
)
from jsonpointer import EndOfList


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

    def test_hash_without_numeric_prefix(self):
        with pytest.raises(RelJsonPointerInvalidPrefixException):
            RelJsonPointer('#')

    def test_index_without_numeric_prefix(self):
        with pytest.raises(RelJsonPointerInvalidPrefixException):
            RelJsonPointer('-1')


class TestZeroAlone:
    rjp = RelJsonPointer('0')

    def test_root(self):
        doc = {}
        assert id(self.rjp.resolve(doc, '')) == id(doc)

    def test_property(self):
        doc = {'foo': {'bar': 1}}
        assert id(self.rjp.resolve(doc, '/foo')) == id(doc['foo'])

    def test_index(self):
        doc = [{'thing': 'stuff'}]
        assert id(self.rjp.resolve(doc, '/0')) == id(doc[0])

    def test_end_of_list(self):
        assert isinstance(self.rjp.resolve([0, 1, 2], '/-'), EndOfList)

    def test_end_of_list_exception(self):
        with pytest.raises(RelJsonPointerEndOfListException):
            self.rjp.resolve([0, 1, 2], '/-', no_eol=True)

    def test_defaulting(self):
        default = [42]
        assert id(self.rjp.resolve({}, '/foo', default)) == id(default)


class TestHash:
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


class TestIndexManipulation:
    def test_forward(self):
        assert RelJsonPointer('0+1').resolve([88, 42], '/0') == 42

    def test_backwards(self):
        rjp = RelJsonPointer('1-2/a')
        print(f'{rjp._pointer}, {rjp._up_count}, {rjp._over_count}')
        doc = [{'a': 1}, {'b': 2}, {'c': 3}]
        assert rjp.resolve(doc, '/2/c') == 1

    def test_index_root(self):
        with pytest.raises(RelJsonPointerIndexTypeException, match='root'):
            RelJsonPointer('1-2').resolve(
                {'foo': 'bar'},
                '/foo',
            )

    def test_index_object(self):
        with pytest.raises(
            RelJsonPointerIndexTypeException,
            match='non-integer index "whoops"',
        ):
            RelJsonPointer('0+1/foo').resolve(
                {'whoops': {'foo'}},
                '/whoops',
            )

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
