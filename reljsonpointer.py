import re
from collections.abc import Sequence
from itertools import chain
from jsonpointer import JsonPointer, JsonPointerException, unescape

INDEX_MANIP = re.compile(r'^(?P<up>\d+)(?P<over>[-+]\d+)$')


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


class RelJsonPointerIndexTypeException(RelJsonPointerException):
    def __init__(self, over_count, last):
        super().__init__(
            f'Cannot add {over_count} to a non-integer index {last}'
        )


class RelJsonPointerIndexException(RelJsonPointerException):
    def __init__(self, over_count, initial_index, length):
        super().__init__(
            f'Cannot go over {over_count} from {initial_index} ' +
            f'in list of length {length}'
        )


class RelJsonPointerEndOfListException(RelJsonPointerException):
    def __init__(self, full):
        super().__init__(
            'Cannot resolve pointer with "-" index except to ' +
            f'access the length of an array with "#": "{full}"'
        )


class RelNotAbsoluteJsonPointerException:
    def __init__(self, pointer):
        super().__init__(
            f'Cannot use non-relative JSON pointer {pointer} as relative ' +
            'JSON pointer, which must start with a non-negative integer.'
        )


class RelJsonPointerInvalidPrefixException:
    def __init__(self, prefix):
        super().__init__(
            f'Relative JSON Pointer prefix "{prefix}" must start with a ' +
            'non-negative integer, optionally followed by "-" or "+" and ' +
            'another non-negative integer.'
        )


class RelJsonPointer:
    def __init__(self, relpointer, strict=True):
        self._use_name_of_last = False
        self._over_count = 0
        self._up_count = 0
        self._pointer = None

        relparts = [unescape(p) for p in relpointer.split('/')]
        prefix = relparts[0]
        if prefix == '':
            if strict:
                raise RelNotAbsoluteJsonPointerException(relpointer)
            self._pointer = JsonPointer.from_parts(relparts)
            return

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
            m = INDEX_MANIP.search(prefix)
            if m is None:
                raise RelJsonPointerInvalidPrefixException(prefix)
            self._up_count = int(m.group('up'))
            self._over_count = int(m.group('over'))

    def resolve(self, doc, base):
        if isinstance(base, str):
            base = JsonPointer(base)

        parts = base.get_parts()
        new_length = len(parts) - self._up_count

        if new_length < 0:
            raise RelJsonPointerDepthException(self._up_count, len(parts))

        if self._use_name_of_last and new_length < 1:
            raise RelJsonPointerRootNameException()

        if self._over_count:
            try:
                index = int(parts[-1])
                parts[-1] = str(index + self._over_count)
            except TypeError:
                raise RelJsonPointerIndexTypeException(
                    self._over_count, parts[-1]
                )

        full = JsonPointer.from_parts(
            chain(parts[:new_length], self._pointer.get_parts())
        )

        if self._use_name_of_last:
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
            except JsonPointerException as jpe:
                if 'jsonpointer.EndOfList' in str(jpe):
                    raise RelJsonPointerEndOfListException(full)

        try:
            return full.resolve(doc)
        except JsonPointerException as jpe:
            if 'jsonpointer.EndOfList' in str(jpe):
                raise RelJsonPointerEndOfListException(full)
            raise
