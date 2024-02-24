# UNDER DEVELOPMENT - EXPERIMENTAL

import argparse
import copy
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

# Relative to the directory containing THIS Python file.
THIS_DIR = f"{os.path.dirname(__file__)}"
TEMPLATES_DIR = f"{THIS_DIR}/../schema_templates"
DOCS_DIR = f"{THIS_DIR}/../source"
OUTPUT_DIR = f"{DOCS_DIR}/schemas"
INDEX_DOC_FILE = f"{DOCS_DIR}/schema_types.rst"


def main():

    parser = argparse.ArgumentParser(description="Generate Portal schema (rst) documentation.")
    parser.add_argument("schema", type=str, nargs="?",
                        help=f"A schema name or 'schemas' (or no argument) for all. ")
    parser.add_argument("--ini", type=str, required=False, default=None,
                        help=f"Name of the application .ini file.")
    parser.add_argument("--env", "-e", type=str, required=False, default=None,
                        help=f"Environment name (key from ~/.smaht-keys.json).")
    parser.add_argument("--all", action="store_true", required=False, default=False,
                        help="Include all properties for schema usage.")
    parser.add_argument("--update-index", action="store_true", required=False,
                        default=False, help="Update the index.rst file.")
    parser.add_argument("--verbose", action="store_true", required=False, default=False, help="Verbose output.")
    parser.add_argument("--debug", action="store_true", required=False, default=False, help="Debugging output.")
    args = parser.parse_args()

    portal = _create_portal(ini=args.ini, env=args.env or os.environ.get("SMAHT_ENV"),
                            verbose=args.verbose, debug=args.debug)

    if not args.schema or args.schema.lower() in ["schemas", "schema"]:
        schemas = _get_schemas(portal)
        for schema_name in schemas:
            schema = schemas[schema_name]
            schema_doc = _generate_doc(schema_name, schema, include_all=args.all)
            _write_doc(schema_name, schema_doc)
    elif args.schema:
        schema, schema_name = _get_schema(portal, args.schema)
        if schema and schema_name:
            schema_doc = _generate_doc(schema_name, schema, include_all=args.all)
            _write_doc(schema_name, schema_doc)
    else:
        _usage()

    if args.update_index:
        _update_index_doc(_get_schemas(portal))


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


def _generate_doc(schema_name: str, schema: dict, include_all: bool = False) -> str:
    content = ""
    if content := _get_template("schema"):
        content = content.replace("{schema_name}", schema_name)

        if content_all_properties := _generate_doc_all_properties(schema, include_all):
            content_all_properties = _normalize_spaces(content_all_properties)
            content = content.replace("{all_properties}", content_all_properties)

        if content_required_properties := _generate_doc_required_properties(schema, include_all):
            content_required_properties = _normalize_spaces(content_required_properties)
            content = content.replace("{required_properties_list}", content_required_properties)
        if content_identifying_properties := _generate_doc_identifying_properties(schema, include_all):
            content_identifying_properties = _normalize_spaces(content_identifying_properties)
            content = content.replace("{identifying_properties_list}", content_identifying_properties)
    return content


def _generate_doc_all_properties(schema: dict, include_all: bool = False) -> str:
    result = ""
    if not isinstance(schema, dict) or not schema:
        return result
    if not (all_properties := schema.get("properties")):
        return result
    properties = []
    for property_name in all_properties:
        if not property_name or not include_all and property_name in _IGNORE_PROPERTIES:
            continue
        if not (property := all_properties[property_name]):
            continue
        if not (property_type := all_properties.get("type")):
            continue
        properties.append({"name": property_name, "type": property_type})
    result = _generate_doc_simple_properties(properties)
    return result


def _generate_doc_required_properties(schema: dict, include_all: bool = False) -> str:
    result = ""
    if not isinstance(schema, dict) or not schema:
        return result
    if not (required_properties := schema.get("required")):
        return result
    properties = []
    for property_name in required_properties:
        if not property_name or not include_all and property_name in _IGNORE_PROPERTIES:
            continue
        if property_type := (info := schema.get("properties", {}).get(property_name, {})).get("type", ""):
            if property_type == "array" and (array_type := info.get("items", {}).get("type", "")):
                property_type = f"{property_type} or {array_type}"
        properties.append({"name": property_name, "type": property_type})
    result = _generate_doc_simple_properties(properties)
    if isinstance(any_of := schema.get("anyOf"), list):
        if ((any_of == [{"required": ["submission_centers"]}, {"required": ["consortia"]}]) or
            (any_of == [{"required": ["consortia"]}, {"required": ["submission_centers"]}])):  # noqa
            if template_oneormore_property_row := _get_template("oneormore_property_row"):
                result += _generate_doc_simple_properties([
                    {"name": "consortia", "type": "array of string"},
                    {"name": "submission_centers", "type": "array of string"}
                ])
    return result


def _generate_doc_identifying_properties(schema: dict, include_all: bool = False) -> str:
    result = ""
    if not isinstance(schema, dict) or not schema:
        return result
    if not (identifying_properties := schema.get("identifyingProperties")):
        return result
    properties = []
    for property_name in identifying_properties:
        if not property_name or not include_all and property_name in _IGNORE_PROPERTIES:
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
    if not (template_simple_property_row := _get_template("simple_property_row")):
        return result
    result = ""
    for property in properties:
        property_name = property["name"]
        property_type = property["type"]
        content_simple_property = copy.deepcopy(template_simple_property_row)
        content_simple_property = content_simple_property.replace("{property_name}", property_name)
        content_simple_property = content_simple_property.replace("{property_type}", property_type)
        result += content_simple_property
    return result


def _write_doc(schema_name: str, schema_doc_content: str) -> None:
    output_file = f"{os.path.join(OUTPUT_DIR, schema_name)}.rst"
    with io.open(output_file, "w") as f:
        f.write(schema_doc_content)


def _update_index_doc(schemas: dict) -> None:
    magic_string = ".. DO NOT TOUCH THIS LINE: USED BY generate_schema_doc SCRIPT!"
    with io.open(INDEX_DOC_FILE, "r") as f:
        lines = f.readlines()
    for index, line in enumerate(lines):
        if line.strip() == magic_string:
            lines = lines[:index+1]
            break
    with io.open(INDEX_DOC_FILE, "w") as f:
        f.writelines(lines)
        f.write(f"\n")
        f.write(".. toctree::\n")
        f.write("  :caption: Types  🔍\n")
        f.write("  :maxdepth: 1\n\n")
        for schema_name in schemas:
            f.write(f"  schemas/{schema_name}\n")


@lru_cache(maxsize=32)
def _get_template(name: str) -> str:
    template_file = f"{TEMPLATES_DIR}/{name}.rst"
    with io.open(template_file, "r") as f:
        return f.read()


def _replace_respecting_leading_spaces(text: str, value: str, replacement: str, tabsize: int = 4) -> str:
    """
    Searches for the given value substring in the given text string and, if found,
    replaces it with the given replacement string; but making sure to maintain
    and spacing regarding where the replacement string is. Meaning that if the
    value to to be replaced in the text is the first non-space value on a line,
    i.e. following a newline, the replacement value will be preceded by by that
    many spaces before doing the replacement, including any of the lines in the
    replacement string, i.e. each newline in the replacement string will be
    followed by that many spaces when doing the replacement. If the value to
    be replaced is not the first non-space value on the line, the the replacement
    value will be normlized with respect to spaces before doing the replacement
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
