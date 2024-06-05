from __future__ import annotations
from typing import Optional, Type


class RCloneStoreRegistry:

    _registered_cloud_stores = []

    @staticmethod
    def register(cls):
        if RCloneStoreRegistry._is_derived_from_rclone_store_class(cls):
            if not RCloneStoreRegistry._is_properly_defined_rclone_store_class_derivative(cls):
                print(f"CODE ERROR: Malformed RCloneStore class register attempt: {cls.__module__}.{cls.__name__}")
            elif (existing_cls := RCloneStoreRegistry.lookup(cls.prefix)) is not None:
                print(f"CODE ERROR: Duplicate RCloneStore class register attempt:"
                      f" {cls.__module__}.{cls.__name__} |"
                      f" {existing_cls.__module__}.{existing_cls.__name__} | {cls.prefix}")
            else:
                RCloneStoreRegistry._registered_cloud_stores.append(cls)
        return cls

    @staticmethod
    def lookup(path: str) -> Optional[Type]:
        if isinstance(path, str) and (path := path.strip().lower()):
            for cloud_store_class in RCloneStoreRegistry._registered_cloud_stores:
                if path.startswith(cloud_store_class.prefix.lower()):
                    return cloud_store_class
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
        if (hasattr(cls, "prefix") and isinstance(value := cls.prefix, str) and value and
            hasattr(cls, "proper_name") and isinstance and (value := cls.proper_name, str) and value and
            hasattr(cls, "proper_name_title") and isinstance(value := cls.proper_name_title, str) and value and
            hasattr(cls, "proper_name_label") and isinstance(value := cls.proper_name_label, str) and value and
            callable(getattr(cls, "from_args"))):  # noqa
            return True
        return False
