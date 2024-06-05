from __future__ import annotations
from typing import Optional, Type


class RCloneStoreRegistry:

    _registered_cloud_stores = {}
    _required_prefix_suffix = "://"

    @staticmethod
    def register(cls):
        if RCloneStoreRegistry._is_derived_from_rclone_store_class(cls):
            if not RCloneStoreRegistry._is_properly_defined_rclone_store_class_derivative(cls):
                print(f"CODE ERROR: Malformed RCloneStore class register attempt: {cls.__module__}.{cls.__name__}")
                return cls
            if (existing_cls := RCloneStoreRegistry.lookup(cls.prefix)) is not None:
                print(f"CODE ERROR: Duplicate RCloneStore class register attempt:"
                      f" {cls.__module__}.{cls.__name__} |"
                      f" {existing_cls.__module__}.{existing_cls.__name__} | {cls.prefix}")
                return cls
            # Above sanity check ensures cls.prefix ends with RCloneStoreRegistry._required_prefix_suffix.
            key = cls.prefix[0:cls.prefix.find(RCloneStoreRegistry._required_prefix_suffix)]
            RCloneStoreRegistry._registered_cloud_stores[key] = cls
        return cls

    @staticmethod
    def lookup(path: str) -> Optional[Type]:
        if isinstance(path, str) and (path := path.lstrip()):
            if prefix_suffix_index := path.find(RCloneStoreRegistry._required_prefix_suffix):
                if key := path[0:prefix_suffix_index]:
                    return RCloneStoreRegistry._registered_cloud_stores.get(key)
        return None

    @staticmethod
    def _is_derived_from_rclone_store_class(cls) -> bool:
        # We don't want to import RCloneStore here because we want it to import us,
        # we need to do this sanity checking by name.
        for base in cls.__bases__:
            if base.__name__ == "RCloneStore" and base.__module__ == "submitr.rclone.rclone_store":
                return True
        return False

    @staticmethod
    def _is_properly_defined_rclone_store_class_derivative(cls) -> bool:
        if (callable(getattr(cls, "from_args")) and
            hasattr(cls, "proper_name") and isinstance and (value := cls.proper_name, str) and value and
            hasattr(cls, "proper_name_title") and isinstance(value := cls.proper_name_title, str) and value and
            hasattr(cls, "proper_name_label") and isinstance(value := cls.proper_name_label, str) and value and
            hasattr(cls, "prefix") and isinstance(value := cls.prefix, str) and
            value.endswith(RCloneStoreRegistry._required_prefix_suffix) and
            len(value) > len(RCloneStoreRegistry._required_prefix_suffix)):  # noqa
            return True
        return False
