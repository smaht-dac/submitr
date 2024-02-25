# UNDER DEVELOPMENT - EXPERIMENTAL

import argparse
import copy
from datetime import datetime
from functools import lru_cache
import io
import os
import re
from typing import List, Optional, Tuple
from dcicutils.captured_output import captured_output
from dcicutils.misc_utils import PRINT
from dcicutils.portal_utils import Portal


# Schema types/properties to ignore (by default) for the view schema usage.
_IGNORE_TYPES = [
    "AccessKey",
    "IngestionSubmission",
    "MetaWorkflow",
    "MetaWorkflowRun",
    "Page",
    "StaticSection",
    "TestingLinkedSchemaField",
    "TestingPostPutPatch",
    "TrackingItem",
    "Workflow",
    "WorkflowRun",
]
_IGNORE_PROPERTIES = [
    "@id",
    "@type",
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
            if schema_name in _IGNORE_TYPES:
                continue
            schema = schemas[schema_name]
            schema_doc = _gendoc(schema_name, schema, include_all=args.all, schemas=schemas, portal=portal)
            _write_doc(schema_name, schema_doc)
    elif args.schema:
        schema, schema_name = _get_schema(portal, args.schema)
        if schema and schema_name:
            schema_doc = _gendoc(schema_name, schema, include_all=args.all)
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


def _get_referencing_schemas(schema_name: str, schemas: dict) -> List[str]:
    result = []
    for this_schema_name in schemas:
        if this_schema_name == schema_name or this_schema_name in _IGNORE_TYPES:
            continue
        schema = schemas[this_schema_name]
        if properties := schema.get("properties"):
            for property_name in properties:
                if property_name in _IGNORE_PROPERTIES:
                    continue
                property = properties[property_name]
                if property.get("linkTo") == schema_name:
                    result.append(this_schema_name)
    return sorted(list(set(result)))


def _get_derived_schemas(schema_name: str, schemas: dict) -> List[str]:
    result = []
    for this_schema_name in schemas:
        if this_schema_name == schema_name or this_schema_name in _IGNORE_TYPES:
            continue
        if _get_parent_schema_name(schemas[this_schema_name]) == schema_name:
            result.append(this_schema_name)
    return result


def _gendoc(schema_name: str, schema: dict, include_all: bool = False,
            schemas: Optional[dict] = None, portal: Portal = None) -> str:
    content = ""
    if not (content := _get_template("schema")):
        return content
    content_schema_title = f"{'=' * len(schema_name)}\n{schema_name}\n{'=' * len(schema_name)}\n\n"
    content = content.replace("{schema_title}", content_schema_title)
    content = content.replace("{schema_name}", schema_name)
    if schema.get("isAbstract") is True:
        content = content.replace("{schema_abstract}", "<u>abstract</u>")
    if schema_description := schema.get("description"):
        if not schema_description.endswith("."):
            schema_description += "."
        content = content.replace("{schema_description}", f"<br /><u>Description</u>: {schema_description}")

    if parent_schema_name := _get_parent_schema_name(schema):
        content = content.replace("{parent_schema}",
                                  f"Its <b>parent</b> type is: "
                                  f"<a href={parent_schema_name}.html>"
                                  f"<u>{parent_schema_name}</u></a>.")

    if schemas and (content_derived_schemas := _gendoc_derived_schemas(schema_name, schemas)):
        content_derived_schemas = f"Its <b>derived</b> types are: {content_derived_schemas}."
        content = content.replace("{derived_schemas}", content_derived_schemas)

    if schemas and (content_referencing_schemas := _gendoc_referencing_schemas(schema_name, schemas)):
        content_referencing_schemas = f"Types <b>referencing</b> this type are: {content_referencing_schemas}."
        content = content.replace("{referencing_schemas}", content_referencing_schemas)

    if content_required_properties_section := _gendoc_required_properties_section(schema, include_all):
        content = content.replace("{required_properties_section}", content_required_properties_section)

    if content_identifying_properties_section := _gendoc_identifying_properties_section(schema, include_all):
        content = content.replace("{identifying_properties_section}", content_identifying_properties_section)

    if content_reference_properties_section := _gendoc_reference_properties_section(schema, include_all):
        content = content.replace("{reference_properties_section}", content_reference_properties_section)

    if content_properties_table := _gendoc_properties_table(schema, include_all):
        content_properties_table = _normalize_spaces(content_properties_table)
        content = content.replace("{properties_table}", content_properties_table)

    content = content.replace("{generated_datetime}", _get_current_datetime_string())
    if portal:
        content = content.replace("{generated_server}", portal.server)
    return _cleanup_content(content)


def _gendoc_referencing_schemas(schema_name: str, schemas: dict) -> str:
    content = ""
    if schemas and (referencing_schemas := _get_referencing_schemas(schema_name, schemas)):
        for referencing_schema in referencing_schemas:
            if content:
                content += ", "
            content += f"<a href='{referencing_schema}.html'><u>{referencing_schema}</u></a>"
    return content


def _gendoc_derived_schemas(schema_name: str, schemas: dict) -> str:
    content = ""
    if schemas and (derived_schemas := _get_derived_schemas(schema_name, schemas)):
        for derived_schema in derived_schemas:
            if content:
                content += ", "
            content += f"<a href='{derived_schema}.html'><u>{derived_schema}</u></a>"
    return content


def _gendoc_required_properties_section(schema: dict, include_all: bool = False) -> str:
    content = ""
    if content_required_properties_table := _gendoc_required_properties_table(schema, include_all):
        if not (content := _get_template("required_properties_section")):
            return content
        content_required_properties_table = _normalize_spaces(content_required_properties_table)
        content = content.replace("{required_properties_table}", content_required_properties_table)
    return content


def _gendoc_required_properties_table(schema: dict, include_all: bool = False) -> str:
    content = ""
    if not isinstance(schema, dict) or not schema:
        return content
    if not (properties := schema.get("properties", [])):
        return content
    if not (required_properties := schema.get("required")):
        return content
    if not (template_required_properties_table := _get_template("required_properties_table")):
        return content
    simple_properties = []
    for property_name in sorted(list(set(required_properties))):
        if not property_name or not include_all and property_name in _IGNORE_PROPERTIES:
            continue
        if not (property := properties[property_name]):
            continue
        if not (property_type := property.get("type")):
            continue
        if property_type == "array":
            if property_items := property.get("items"):
                if property_array_type := property_items.get("type"):
                    property_type = f"{property_type} of {property_array_type}"
        simple_properties.append({"name": property_name, "type": property_type})
    content_simple_property_rows = _gendoc_simple_properties(simple_properties, kind="required")
    content = template_required_properties_table
    content = content.replace("{required_property_rows}", content_simple_property_rows)
    content_oneormore_property_row = ""
    if isinstance(any_of := schema.get("anyOf"), list):
        # Very special case.
        if ((any_of == [{"required": ["submission_centers"]}, {"required": ["consortia"]}]) or
            (any_of == [{"required": ["consortia"]}, {"required": ["submission_centers"]}])):  # noqa
            if template_oneormore_property_row := _get_template("oneormore_property_row"):
                content_oneormore_property_row = template_oneormore_property_row
                content_oneormore_property_row = (
                    content_oneormore_property_row.replace("{oneormore_properties_list}",
                                                           "<b>consortia</b>, <b>submission_centers</b>"))
    content = content.replace("{oneormore_property_row}", content_oneormore_property_row)
    return content


def _gendoc_identifying_properties_section(schema: dict, include_all: bool = False) -> str:
    content = ""
    if content_identifying_properties_table := _gendoc_identifying_properties_table(schema, include_all):
        if not (content := _get_template("identifying_properties_section")):
            return content
        content_identifying_properties_table = _normalize_spaces(content_identifying_properties_table)
        content = content.replace("{identifying_properties_table}", content_identifying_properties_table)
    return content


def _gendoc_identifying_properties_table(schema: dict, include_all: bool = False) -> str:
    content = ""
    if not isinstance(schema, dict) or not schema:
        return content
    if not (properties := schema.get("properties", [])):
        return content
    if not (identifying_properties := sorted(list(set(schema.get("identifyingProperties", []))))):
        return content
    if not (template_identifying_properties_table := _get_template("identifying_properties_table")):
        return content
    simple_properties = []
    for property_name in identifying_properties:
        if not property_name or not include_all and property_name in _IGNORE_PROPERTIES:
            continue
        if not (property := properties[property_name]):
            continue
        if not (property_type := property.get("type")):
            continue
        if property_type == "array":
            if property_items := property.get("items"):
                if property_array_type := property_items.get("type"):
                    property_type = f"{property_type} of {property_array_type}"
        simple_properties.append({"name": property_name, "type": property_type})
    content_simple_property_rows = _gendoc_simple_properties(simple_properties, kind="identifying")
    content = template_identifying_properties_table
    content = content.replace("{identifying_property_rows}", content_simple_property_rows)
    return content


def _gendoc_reference_properties_section(schema: dict, include_all: bool = False) -> str:
    content = ""
    if content_reference_properties_table := _gendoc_reference_properties_table(schema, include_all):
        if not (content := _get_template("reference_properties_section")):
            return content
        content_reference_properties_table = _normalize_spaces(content_reference_properties_table)
        content = content.replace("{reference_properties_table}", content_reference_properties_table)
    return content


def _gendoc_reference_properties_table(schema: dict, include_all: bool = False) -> str:
    content = ""
    if not isinstance(schema, dict) or not schema:
        return content
    if not (properties := schema.get("properties", [])):
        return content
    if not (reference_properties := [property_name for property_name in properties
                                     if properties[property_name].get("linkTo")]):
        return content
    if not (template_reference_properties_table := _get_template("reference_properties_table")):
        return content
    simple_properties = []
    for property_name in reference_properties:
        if not property_name or not include_all and property_name in _IGNORE_PROPERTIES:
            continue
        if not (property := properties[property_name]):
            continue
        if not (property_type := property.get("type")):
            continue
        if not (property_link_to := property.get("linkTo")):
            continue
        property_type = (
            f"<a href={property_link_to}.html style='font-weight:bold;color:green;'>"
            f"{property_link_to}</a><br /><span style='color:green;'>{property_type}</span>")
        if property_type == "array":
            if property_items := property.get("items"):
                if property_array_type := property_items.get("type"):
                    property_type = f"{property_type} of {property_array_type}"
        simple_properties.append({"name": property_name, "type": property_type})
    if not (content_simple_property_rows := _gendoc_simple_properties(simple_properties)):
        return content
    content = template_reference_properties_table
    content = content.replace("{reference_property_rows}", content_simple_property_rows)
    return content


def _gendoc_simple_properties(properties: List[str], kind: Optional[str] = None) -> str:
    result = ""
    if not isinstance(properties, list) or not properties:
        return result
    if not (template_simple_property_row := _get_template("simple_property_row")):
        return result
    result = ""
    for property in properties:
        property_name = property["name"]
        property_type = property["type"]
        if kind == "required":
            property_name = f"<span style='color:red'>{property_name}</span>"
        elif kind == "identifying":
            property_name = f"<span style='color:blue'>{property_name}</span>"
        content_simple_property = copy.deepcopy(template_simple_property_row)
        content_simple_property = content_simple_property.replace("{property_name}", property_name)
        content_simple_property = content_simple_property.replace("{property_type}", property_type)
        result += content_simple_property
    return result


def _gendoc_properties_table(schema: dict, include_all: bool = False,
                             _level: int = 0, _parents: List[str] = []) -> str:
    content = ""
    if not isinstance(schema, dict) or not schema:
        return content
    if not (properties := schema.get("properties")):
        return content
    if _level == 0:
        if not (template_properties_table := _get_template("properties_table")):
            return content
    if not (template_property_row := _get_template("property_row")):
        return content
    if _parents:
        template_property_row = template_property_row.replace("{property_row_indent}", "padding-left:20pt")
    else:
        template_property_row = template_property_row.replace("{property_row_indent}", "")
    required_properties = schema.get("required", [])
    identifying_properties = schema.get("identifyingProperties", [])
    content_property_rows = ""
    for property_name in {key: properties[key] for key in sorted(properties)}:
        content_nested_object = ""
        content_nested_array = ""
        if not property_name or not include_all and property_name in _IGNORE_PROPERTIES:
            continue
        if not (property := properties[property_name]):
            continue
        if not (property_type := property.get("type")):
            continue
        content_property_row = template_property_row
        content_property_name = property_name
        content_property_type = property_type
        property_attributes = []
        property_link_to = property.get("linkTo")
        if property_type == "array":
            if property_items := property.get("items"):
                if property_array_type := property_items.get("type"):
                    content_property_type = f"<b>{property_type}</b> of <b>{property_array_type}</b>"
                    if property_array_type == "object":
                        content_nested_array = _gendoc_properties_table(
                            property_items, include_all=include_all,
                            _level=_level + 1, _parents=_parents + [property_name])
                if max_length := property_items.get("maxLength"):
                    property_attributes.append(f"max items: {max_length}")
            if property.get("uniqueItems"):
                property_attributes.append("unique")
        elif property_type == "object":
            content_nested_object = _gendoc_properties_table(
                property, include_all=include_all,
                _level=_level + 1, _parents=_parents + [property_name])
        if property_description := property.get("description", "").strip():
            if not property_description.endswith("."):
                property_description += "."
        if property_internal_comment := property.get("internal_comment", "").strip():
            property_internal_comment = "[" + property_internal_comment + "]"
            if property_description:
                property_description += " " + property_internal_comment
        if not property_description and property_name == "uuid":
            property_description = "Unique ID by which this object is identified."
        if property_name in required_properties:
            content_property_name = f"<span style='color:red'>{property_name}</span>"
        elif property_name in identifying_properties:
            content_property_name = f"<span style='color:blue'>{property_name}</span>"
        default = property.get("default")
        if (format := property.get("format")) and (format != property_name):
            property_attributes.append(f"format: {format}")
        if property.get("calculatedProperty"):
            property_attributes.append(f"calculated")
        if isinstance(any_of := property.get("anyOf"), list):
            if ((any_of == [{"format": "date"}, {"format": "date-time"}]) or
                (any_of == [{"format": "date-time"}, {"format": "date"}])):  # noqa
                # Very special case.
                property_attributes.append(f"format: date | date-time")
        if property_link_to:
            content_property_type = (
                f"<a href={property_link_to}.html style='font-weight:bold;color:green;'>"
                f"{property_link_to}</a><br /><span style='color:green;'>{content_property_type}</span>")
        elif enum := property.get("enum", []):
            content_property_type = f"<b>enum</b> of {content_property_type}"
            content_property_name = (
                f"<u>{content_property_name}</u>"
                f"<span style='font-weight:normal;font-family:arial;color:#222222;'>")
            for enum_value in enum:
                if isinstance(enum_value, str) and len(enum_value) > 60:
                    content_property_name += f"<br />&nbsp;•&nbsp;{enum_value[0:32]}"
                    content_property_name += (
                        f"<br />&nbsp;&nbsp;&nbsp;{enum_value[32:]}"
                        f"{'&nbsp;←&nbsp;<small><b>default</b></small>' if enum_value == default else ''}")
                else:
                    content_property_name += (
                        f"<br />&nbsp;•&nbsp;{enum_value}"
                        f"{'&nbsp;←&nbsp;<small><b>default</b></small>' if enum_value == default else ''}")
            content_property_name += f"</span>"
        elif isinstance(property_type, list):
            property_types_string = ""
            for type in property_type:
                if property_types_string:
                    property_types_string += " or<br />"
                property_types_string += f"<b>{type}</b>"
            content_property_type = property_types_string
        elif not property_type == "array":
            content_property_type = f"<b>{content_property_type}</b>"
            if default is not None:
                if isinstance(default, bool):
                    default = str(default).lower()
                content_property_type += f"<span style='font-weight:normal'><br />•&nbsp;default: {default}</span>"
        if property_attributes:
            content_property_type = f"<u>{content_property_type}</u><br />"
            for property_attribute in property_attributes:
                content_property_type += f"•&nbsp;{property_attribute}<br />"
        if pattern := property.get("pattern"):
            if property_name in required_properties:
                color = "red"
            elif property_name in identifying_properties:
                color = "blue"
            else:
                color = "inherit"
            property_description += (
                f"<br />Must adhere to (regex) <span style='color:{color};'><b>pattern</b>:&nbsp;"
                f"<small style='font-family:monospace;'>{pattern}</small></span>")
        if _parents:
            content_parents = "<span style='font-weight:normal;'>"
            for index, parent in enumerate(_parents):
                if index > 0:
                    content_parents += f" <b>.</b> "
                content_parents += f"{parent}"
            content_parents += "</span>"
            content_property_name = f"{content_parents} <b>.</b> {content_property_name}"
        content_property_row = content_property_row.replace("{property_name}", content_property_name)
        content_property_row = content_property_row.replace("{property_type}", content_property_type)
        content_property_row = content_property_row.replace("{property_description}", property_description or "-")
        content_property_rows += content_property_row
        if content_nested_object:
            content_property_rows += content_nested_object
        elif content_nested_array:
            content_property_rows += content_nested_array
    if _level == 0:
        content = template_properties_table
        content = content.replace("{property_rows}", content_property_rows)
    else:
        content = content_property_rows
    return content


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
        for schema_name in {key: schemas[key] for key in sorted(schemas)}:
            if schema_name in _IGNORE_TYPES:
                continue
            f.write(f"  schemas/{schema_name}\n")


@lru_cache(maxsize=32)
def _get_template(name: str) -> str:
    template_file = f"{TEMPLATES_DIR}/{name}.html"
    with io.open(template_file, "r") as f:
        return f.read()


def _cleanup_content(content: str) -> str:
    return re.sub(r"\{\w+\}", "", content)


def _normalize_spaces(value: str) -> str:
    """
    Returns the given string with multiple consecutive occurrences of whitespace
    converted to a single space, and left and right trimmed of spaces.
    """
    return re.sub(r"\s+", " ", value).strip()


def _get_current_datetime_string():
    tzlocal = datetime.now().astimezone().tzinfo
    return datetime.now().astimezone(tzlocal).strftime(f"%A, %B %-d, %Y | %-I:%M %p %Z")


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