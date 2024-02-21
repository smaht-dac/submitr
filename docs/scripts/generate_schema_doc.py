# UNDER DEVELOPMENT - EXPERIMENTAL

import argparse
from functools import lru_cache
import io
import os
import re
from typing import List, Optional, Tuple
from dcicutils.captured_output import captured_output
from dcicutils.misc_utils import PRINT
from dcicutils.portal_utils import Portal


# Schema properties to ignore (by default) for the view schema usage.
_IGNORE_PROPERTIES = [
    "date_created",
    "last_modified",
    "principals_allowed",
    "submitted_by",
    "schema_version"
]


def main():

    parser = argparse.ArgumentParser(description="Generate Portal schema (rst) documentation.")
    parser.add_argument("schema", type=str, nargs="?",
                        help=f"A schema name or 'schemas' (or no argument) for all. ")
    parser.add_argument("--ini", type=str, required=False, default=None,
                        help=f"Name of the application .ini file.")
    parser.add_argument("--env", "-e", type=str, required=False, default=None,
                        help=f"Environment name (key from ~/.smaht-keys.json).")
    parser.add_argument("--server", "-s", type=str, required=False, default=None,
                        help=f"Environment server name (server from key in ~/.smaht-keys.json).")
    parser.add_argument("--app", type=str, required=False, default=None,
                        help=f"Application name (one of: smaht, cgap, fourfront).")
    parser.add_argument("--all", action="store_true", required=False, default=False,
                        help="Include all properties for schema usage.")
    parser.add_argument("--verbose", action="store_true", required=False, default=False, help="Verbose output.")
    parser.add_argument("--debug", action="store_true", required=False, default=False, help="Debugging output.")
    args = parser.parse_args()

    portal = _create_portal(ini=args.ini, env=args.env or os.environ.get("SMAHT_ENV"),
                            server=args.server, app=args.app, verbose=args.verbose, debug=args.debug)

    if not args.schema or args.schema.lower() in ["schemas", "schema"]:
        schemas = _get_schemas(portal)
        for schema_name in schemas:
            schema = schemas[schema_name]
            _generate_doc(schema, all_properties=args.all)
    elif args.schema:
        schema, schema_name = _get_schema(portal, args.schema)
        if schema and schema_name:
            _generate_doc(schema, all_properties=args.all)
    else:
        _usage()


def _create_portal(ini: str, env: Optional[str] = None,
                   server: Optional[str] = None, app: Optional[str] = None,
                   verbose: bool = False, debug: bool = False) -> Portal:
    portal = None
    with captured_output(not debug):
        portal = Portal(env, server=server, app=app) if env or app else Portal(ini)
    if portal:
        if verbose:
            if portal.env:
                PRINT(f"Portal environment: {portal.env}")
            if portal.keys_file:
                PRINT(f"Portal keys file: {portal.keys_file}")
            if portal.key_id:
                PRINT(f"Portal key prefix: {portal.key_id[0:2]}******")
            if portal.ini_file:
                PRINT(f"Portal ini file: {portal.ini_file}")
            if portal.server:
                PRINT(f"Portal server: {portal.server}")
        return portal


@lru_cache(maxsize=1)
def _get_schemas(portal: Portal) -> Optional[dict]:
    return portal.get_schemas()


def _get_schema(portal: Portal, name: str) -> Tuple[Optional[dict], Optional[str]]:
    if portal and name and (name := name.replace("_", "").replace("-", "").strip().lower()):
        if schemas := _get_schemas(portal):
            for schema_name in schemas:
                if schema_name.replace("_", "").replace("-", "").strip().lower() == name:
                    return schemas[schema_name], schema_name
    return None, None


def _get_parent_schema_name(schema: dict) -> Optional[str]:
    if sub_class_of := schema.get("rdfs:subClassOf"):
        if (parent_schema_name := os.path.basename(sub_class_of).replace(".json", "")) != "Item":
            return parent_schema_name


def _generate_doc(schema: dict, all_properties: bool = False) -> str:
    content = ""
    with io.open("../schema_templates/schema.rst", "r") as f:
        content = f.read()
        if content_required_properties := _generate_doc_required_properties(schema, all_properties):
            content_required_properties = _normalize_spaces(content_required_properties)
            content = content.replace("{required_properties}", content_required_properties)
        if content_identifying_properties := _generate_doc_identifying_properties(schema, all_properties):
            content_identifying_properties = _normalize_spaces(content_identifying_properties)
            content = content.replace("{identifying_properties}", content_identifying_properties)
    return content


def _generate_doc_required_properties(schema: dict, all_properties: bool = False) -> str:
    result = ""
    if not isinstance(schema, dict) or not schema:
        return result
    if not (required_properties := schema.get("required")):
        return result
    properties = []
    for property_name in required_properties:
        if not property_name or not all_properties and property_name in _IGNORE_PROPERTIES:
            continue
        if property_type := (info := schema.get("properties", {}).get(property_name, {})).get("type", ""):
            if property_type == "array" and (array_type := info.get("items", {}).get("type", "")):
                property_type = f"{property_type} or {array_type}"
        properties.append({"name": property_name, "type": property_type})
    result = _generate_doc_simple_properties(properties)
    if isinstance(any_of := schema.get("anyOf"), list):
        if ((any_of == [{"required": ["submission_centers"]}, {"required": ["consortia"]}]) or
            (any_of == [{"required": ["consortia"]}, {"required": ["submission_centers"]}])):  # noqa
            with io.open("../schema_templates/oneormore_property.rst", "r") as f:
                if template_oneormore_property := f.read():
                    result += _generate_doc_simple_properties([
                        {"name": "consortia", "type": "array of string"},
                        {"name": "submission_centers", "type": "array of string"}
                    ])
    return result


def _generate_doc_identifying_properties(schema: dict, all_properties: bool = False) -> str:
    result = ""
    if not isinstance(schema, dict) or not schema:
        return result
    if not (identifying_properties := schema.get("identifyingProperties")):
        return result
    properties = []
    for property_name in identifying_properties:
        if not property_name or not all_properties and property_name in _IGNORE_PROPERTIES:
            continue
        if property_type := (info := schema.get("properties", {}).get(property_name, {})).get("type"):
            if property_type == "array" and (array_type := info.get("items", {}).get("type")):
                property_type = f"{property_type} or {array_type}"
        properties.append({"name": property_name, "type": property_type})
    result = _generate_doc_simple_properties(properties)
    return result


def _generate_doc_simple_properties(properties: List[str]) -> str:
    result = ""
    if not isinstance(properties, list) or not properties:
        return result
    with io.open("../schema_templates/simple_property.rst", "r") as f:
        if not (template_simple_property := f.read()):
            return result
    result = ""
    for property in properties:
        content_simple_property = template_simple_property
        property_name = property["name"]
        property_type = property["type"]
        content_simple_property = content_simple_property.replace("{property_name}", property_name)
        content_simple_property = content_simple_property.replace("{property_type}", property_type)
        result += content_simple_property
    return result


def _replace_respecting_leading_spaces(text: str, value: str, replacement: str, tabsize: int = 4) -> str:
    """
    Searches for the given value substring in the given text string and, if found,
    replaces it with the given replacement string; but making sure to maintain
    and spacing regarding where the replacement string is. TODO more description.
    """
    text = text.expandtabs(tabsize=tabsize)
    if matches := _find_with_leading_characters(text, value, tabsize=tabsize):
        for match in matches:
            position, leading_characters, is_leading_spaces = match
            if is_leading_spaces:
                leading_spaces = " " * leading_characters
                replacement = replacement.replace("\n", f"\n{leading_spaces}")
            else:
                replacement = _normalize_spaces(replacement)
            text = text[0:position] + replacement + text[position + len(value):]
        return text
    return text


def _find_with_leading_characters(text: str, value: str, tabsize: int = 4) -> Optional[List[Tuple[int, int]]]:
    """
    Searches for the given value substring in the given text string and, if found,
    returns a list of 3-tuples where the first value is the index from the beginning
    of the text, the second value is the number of leading characters, and the third
    is True if the leading characters are all spaces, otherwise False; here "leading"
    means from the beginning of the text or from the beginning of a previous newline.
    Returns None if no matches. Expands tabs first.
    """
    pattern = re.compile(r'(?:^|\n)(.*?)' + re.escape(value))
    matches = list(re.finditer(pattern, text))
    result = []
    for match in matches:
        leading_characters = match.group(1)
        value_position = match.start(1) + len(leading_characters)
        result.append((value_position, len(leading_characters), leading_characters.isspace()))
    return result if result else None


def _normalize_spaces(value: str) -> str:
    """
    Returns the given string with multiple consecutive occurrences of whitespace
    converted to a single space, and left and right trimmed of spaces.
    """
    return re.sub(r"\s+", " ", value).strip()


def _usage(message: Optional[str] = None) -> None:
    if message:
        PRINT(f"ERROR: {message}")
    PRINT("USAGE: TODO")
    _exit()


def _exit(message: Optional[str] = None) -> None:
    if message:
        PRINT(f"ERROR: {message}")
    exit(1)


if __name__ == "__main__":
    main()
