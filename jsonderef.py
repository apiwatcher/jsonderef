import copy
import requests

from requests.exceptions import RequestException

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

    def __init__(self, raise_on_not_found=True, not_found=None,
        requests_timeout=10
    ):
        """ Initializes dereferencer.

        :param raise_on_not_found: If true, RefNotFound is raised if referenced
            object is not found.
        :type raise_on_not_found: Boolean
        :param not_found: In case of referenced object is not found and
            raise_on_not_found is False, this value will be used instead of
            referenced object.
        :type raise_on_not_found: Anything
        :param requests_timeout: Timeout set for requests in case of fetching
            remote urls.
        :type requests_timeout: Integer
        """
        self._cache = {}

        self._raise_on_not_found = raise_on_not_found
        self._not_found = not_found
        self._timeout = requests_timeout

    def deref(self, document, max_deref_depth=10):
        """ Returns dereferenced object.

        Original object is left intact, always new copy of the object is
        returned.

        :param max_deref_depth: How many times do the recursive dereference.
        type: Integer or None
        """
        return self._do_deref(document, document, max_deref_depth)

    @staticmethod
    def _parse_ref_string(ref):
        """
        Parses string returning ref object
        """
        ref_object = {}
        if ref.startswith("#"):
            ref_object["type"] = "local"
            ref = ref[1:]
        elif ref.startswith("http"):
            ref_object["type"] = "remote"
            hash_index = ref.rfind("#")
            ref_object["url"] = ref[:hash_index]
            ref = ref[hash_index+1:]
        else:
            raise JsonDerefException(
                "Cannot resolve reference '{0}'".format(ref)
            )

        ref_object["path"] = []
        if ref != "" and not ref.startswith('/'):
            raise JsonDerefException(
                "Path in the reference must start with '/' ({0}).".format(ref)
            )
        path = ref.split("/")
        # Rfc stuff
        for item in path:
            itm = item.replace("~1", "/")
            itm = itm.replace("~0", "~")
            ref_object["path"].append(itm)

        return ref_object

    def _get_url_json(self, url, store=True):
        """
        Returns object stored at url
        """
        doc = self._cache.get(url, None)
        if doc is not None:
            return doc

        try:
            rsp = requests.get(url, timeout=self._timeout)
            if rsp.status_code != 200:
                raise RefNotFound(
                    "Could not get {0}, status code {1}".format(
                        url, rsp.status_code
                    )
                )

            doc = rsp.json()
            self._cache[url] = doc
            return doc

        except ValueError as exc:
            raise JsonDerefException(
                "Document at {0} is not a valid json. "
                "Parser says '{1}'.".format(
                    url, exc.message
                )
            )
        except RequestException as e:
            raise RefNotFound(
                "Could not get {0}, error {1}".format(
                    url, e.message
                )
            )

    def _get_referenced_object(self, cur_root, ref_obj):
        """
        Returns referenced object
        """
        actual_root = None

        if ref_obj["type"] == "local":
            actual_root = cur_root
        elif ref_obj["type"] == "remote":
            try:
                actual_root = self._get_url_json(ref_obj["url"])
            except RefNotFound:
                if self._raise_on_not_found:
                    raise
                else:
                    return {
                        "root": cur_root,
                        "obj": copy.deepcopy(self._not_found)
                    }

        if len(ref_obj["path"]) == 1:
            return {
                "root": actual_root,
                "obj": actual_root
            }
        else:
            cur_obj = actual_root
            try:
                for p in ref_obj["path"][1:]:
                    if isinstance(cur_obj, dict):
                        cur_obj = cur_obj[str(p)]
                    elif isinstance(cur_obj, list):
                        cur_obj = cur_obj[int(p)]

                return {
                    "root": actual_root,
                    "obj": cur_obj
                }
            except (KeyError, IndexError):
                if self._raise_on_not_found:
                    raise RefNotFound(
                        "Referenced object in path #{0}"
                        " has not been found".format(
                            "/".join(ref_obj["path"])
                        )
                    )
                else:
                    return {
                        "root": cur_root,
                        "obj": copy.deepcopy(self._not_found)
                    }


    def _do_deref(self, current_root, current_obj, remaining_depth):
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
                result = self._get_referenced_object(
                    current_root, JsonDeref._parse_ref_string(ref)
                )

                # And do the deref on it again...:)
                return self._do_deref(
                    result["root"], result["obj"], remaining_depth - 1
                )
            else:
                new_obj = {}
                for key in current_obj:
                    new_obj[key] = self._do_deref(
                        current_root, current_obj[key], remaining_depth
                    )
                return new_obj
        # List may containg refs
        elif isinstance(current_obj, list):
            new_list = []
            for item in current_obj:
                new_list.append(
                    self._do_deref(current_root, item, remaining_depth)
                )
            return new_list
        # Anything else can be just returned
        else:
            return copy.deepcopy(current_obj)
