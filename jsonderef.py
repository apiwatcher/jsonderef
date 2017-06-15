import copy


class JsonDerefException(Exception):
    """
    Generic exception
    """
    pass

class RefNotFound(JsonDerefException):
    """
    Raised if reference is not found
    """
    pass


class JsonDeref(object):

    def __init__(self, document, raise_on_not_found=True, not_found=None):
        """ Initializes dereferencer.

        :param document: Document to be processed.
        :type document: Anything which can be serilized as json :)
        :param raise_on_not_found: If true, RefNotFound is raised if referenced
            object is not found.
        :type raise_on_not_found: Boolean
        :param not_found: In case of referenced object is not found and
            raise_on_not_found is False, this value will be used instead of
            referenced object.
        :type raise_on_not_found: Anything
        """
        self.doc = document
        self.raise_on_not_found = raise_on_not_found
        self.not_found = not_found

    def deref(self, max_deref_depth=10):
        """ Returns dereferenced object.

        Original object is left intact, always new copy of the object is
        returned.

        :param max_deref_depth: How many times do the recursive dereference.
        type: Integer or None
        """
        return self._do_deref(self.doc, max_deref_depth)

    @staticmethod
    def _parse_ref_string(ref):
        """
        Parses string returning ref object
        """
        ref_object = {}
        if ref.startswith("#"):
            ref_object["type"] = "local"
            ref = ref[1:]
        else:
            raise JsonDerefException(
                "Only local references are supported for now."
            )

        ref_object["path"] = []
        path = ref.split("/")
        # Rfc stuff
        for item in path:
            itm = item.replace("~1", "/")
            itm = itm.replace("~0", "~")
            ref_object["path"].append(itm)

        return ref_object

    def _get_referenced_object(self, ref_obj):
        """
        Returns referenced object
        """
        if ref_obj["type"] == "local":
            if len(ref_obj["path"]) == 1:
                return copy.deepcopy(self.doc)
            else:
                try:
                    cur_obj = self.doc
                    for p in ref_obj["path"][1:]:
                        if isinstance(cur_obj, dict):
                            cur_obj = cur_obj[str(p)]
                        elif isinstance(cur_obj, list):
                            cur_obj = cur_obj[int(p)]

                    return copy.deepcopy(cur_obj)
                except (KeyError, IndexError):
                    if self.raise_on_not_found:
                        raise RefNotFound(
                            "Referenced object in path #{0}"
                            " has not been found".format(
                                "/".join(ref_obj["path"])
                            )
                        )
                    else:
                        return copy.deepcopy(self.not_found)
        else:
            if self.raise_on_not_found:
                raise JsonDerefException(
                    "Only local references are supported for now."
                )
            else:
                return copy.deepcopy(self.not_found)

    def _do_deref(self, current_obj, remaining_depth):
        """
        Does the recursive job
        """
        # No remaining level of dereferencing -just return whatever we have
        if remaining_depth == 0:
            return copy.deepcopy(current_obj)

        # dictionary is either ref or it's keys may contain refs
        if isinstance(current_obj, dict):
            ref = current_obj.get("$ref", None)
            # Ok, this object is reference
            if ref is not None:
                # Get the object reference is pointing to
                new_obj = self._get_referenced_object(
                    JsonDeref._parse_ref_string(ref)
                )

                # And do the deref on it again...:)
                return self._do_deref(new_obj, remaining_depth - 1)
            else:
                new_obj = {}
                for key in current_obj:
                    new_obj[key] = self._do_deref(
                        current_obj[key], remaining_depth
                    )
                return new_obj
        # List may containg refs
        elif isinstance(current_obj, list):
            new_list = []
            for item in current_obj:
                new_list.append(self._do_deref(item, remaining_depth))
            return new_list
        # Anything else can be just returned
        else:
            return copy.deepcopy(current_obj)
