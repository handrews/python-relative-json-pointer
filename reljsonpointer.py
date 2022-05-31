# -*- coding: utf-8 -*-

__author__ = 'Henry Andrews <andrews_henry@yahoo.com>'
__version__ = '0.1'
__website__ = 'https://github.com/handrews/python-relative-json-pointer'
__license__ = 'MIT'

"""Implementation of the draft Relative JSON Pointer Specification"""

import re
from collections.abc import Sequence
from itertools import chain
from jsonpointer import JsonPointer, JsonPointerException, EndOfList, unescape

_PREFIX = re.compile(r'^(?P<up>\d+)(?P<over>[-+]\d+)$')

_DEFAULT = object()


class RelJsonPointerException(Exception):
    pass


class RelJsonPointerDepthException(RelJsonPointerException):
    def __init__(self, up_count, depth):
        super().__init__(
            f'Cannot go up {up_count} from starting point of depth {depth}'
        )


class RelJsonPointerRootNameException(RelJsonPointerException):
    def __init__(self):
        super().__init__(
            "Cannot return name or index of the document root"
        )


class RelJsonPointerRootManipulationException(RelJsonPointerException):
    def __init__(self):
        super().__init__(
            "Cannot manipulate the index of the document root"
        )


class RelJsonPointerIndexTypeException(RelJsonPointerException):
    def __init__(self, over_count, last):
        super().__init__(
            f'Cannot add {over_count} to a non-integer index "{last}"'
        )


class RelJsonPointerEndOfListException(RelJsonPointerException):
    def __init__(self, full):
        super().__init__(
            'Cannot resolve pointer with "-" index except to ' +
            f'access the length of an array with "#": "{full}"'
        )


class RelNotAbsoluteJsonPointerException(RelJsonPointerException):
    def __init__(self, pointer):
        super().__init__(
            f'Cannot use non-relative JSON pointer {pointer} as relative ' +
            'JSON pointer, which must start with a non-negative integer.'
        )


class RelJsonPointerInvalidPrefixException(RelJsonPointerException):
    def __init__(self, prefix):
        super().__init__(
            f'Relative JSON Pointer prefix "{prefix}" must start with a ' +
            'non-negative integer, optionally followed by "-" or "+" and ' +
            'another non-negative integer.'
        )


class RelJsonPointerDoesNotExistException(RelJsonPointerException):
    def __init__(self, full):
        super().__init__(
            f'Resolved JSON Pointer "{full}" points to a non-existant' +
            'instance location.'
        )


class RelJsonPointer:
    def __init__(self, relpointer):
        self._use_name_of_last = False
        self._over_count = 0
        self._up_count = 0
        self._pointer = None

        relparts = [unescape(p) for p in relpointer.split('/')]
        prefix = relparts[0]
        if prefix == '':
            raise RelNotAbsoluteJsonPointerException(relpointer)

        if len(relparts) == 1:
            if prefix.endswith('#'):
                self._use_name_of_last = True
                prefix = prefix[:-1]
            self._pointer = JsonPointer('')
        else:
            self._pointer = JsonPointer.from_parts(relparts[1:])

        if len(prefix) == 0 or not prefix[0].isdigit():
            raise RelJsonPointerInvalidPrefixException(prefix)

        try:
            self._up_count = int(prefix)
        except ValueError:
            m = _PREFIX.search(prefix)
            if m is None:
                raise RelJsonPointerInvalidPrefixException(prefix)
            self._up_count = int(m.group('up'))
            self._over_count = int(m.group('over'))

    def to_absolute(self, base):
        if isinstance(base, str):
            base = JsonPointer(base)

        parts = base.get_parts()
        new_length = len(parts) - self._up_count

        if new_length < 0:
            raise RelJsonPointerDepthException(self._up_count, len(parts))

        if self._use_name_of_last and new_length < 1:
            raise RelJsonPointerRootNameException()

        parts = parts[:new_length]

        if self._over_count:
            try:
                index = int(parts[-1])
                parts[-1] = str(index + self._over_count)
            except ValueError:
                raise RelJsonPointerIndexTypeException(
                    self._over_count,
                    parts[-1],
                )
            except IndexError:
                # Not enough parts, we tried to modify the index of root.
                raise RelJsonPointerRootManipulationException()

        full = JsonPointer.from_parts(
            chain(parts[:new_length], self._pointer.get_parts())
        )
        return full, self._use_name_of_last

    def resolve(self, doc, base, default=_DEFAULT, no_eol=False):
        full, use_name_of_last = self.to_absolute(base)
        if use_name_of_last:
            try:
                sub_doc, last = full.to_last(doc)
                is_list = isinstance(sub_doc, Sequence)
                if is_list and last == '-':
                    return len(sub_doc)

                # Make sure there is really a value, don't care what it is.
                full.walk(sub_doc, last)

                # We won't get a TypeError on this int() because
                # JsonPointer.walk() would have raised an exception already.
                return int(last) if is_list else last
            except JsonPointerException:
                raise RelJsonPointerDoesNotExistException(full)

        elif default == _DEFAULT:
            # Because of how JsonPointer implements checking for
            # a default (which we copied here), we need to omit
            # the parameter when we forward the call.
            result = full.resolve(doc)
        else:
            result = full.resolve(doc, default)

        if no_eol and isinstance(result, EndOfList):
            raise RelJsonPointerEndOfListException(full)

        return result
