# UNDER DEVELOPMENT - EXPERIMENTAL
# Script to generate readthedocs based documentation for SMaHT Portal schema types
# relevant for (smaht-submitr) metadata submission; as well as pages for supported
# consortia, submission-centers, and file-formats.

import argparse
import copy
from datetime import datetime
from functools import lru_cache
import io
import os
import re
import sys
from typing import Callable, List, Optional, Tuple
from dcicutils.captured_output import captured_output
from dcicutils.misc_utils import camel_case_to_snake_case, PRINT
from dcicutils.portal_utils import Portal

NODATA = True

SMAHT_DAC_EMAIL = "smhelp@hms-dbmi.atlassian.net"

# Schema types/properties to ignore (by default) for the view schema usage.
IGNORE_TYPES = [
    "AccessKey",
    "HiglassViewConfig",
    "IngestionSubmission",
    "MetaWorkflow",
    "MetaWorkflowRun",
    "Page",
    "StaticSection",
    "SubmittedItem",
    "TestingLinkedSchemaField",
    "TestingPostPutPatch",
    "TrackingItem",
    "UserContent",
    "Workflow",
    "WorkflowRun",
]
IGNORE_PROPERTIES = [
    "@id",
    "@type",
    "content",
    "date_created",
    "last_modified",
    "principals_allowed",
    "submitted_by",
    "schema_version",
    "static_content",
    "static_headers"
]

# Relative to the directory containing THIS Python file.
THIS_DIR = f"{os.path.dirname(__file__)}"
TEMPLATES_DIR = f"{THIS_DIR}/../gendoc_templates"
DOCS_DIR = f"{THIS_DIR}/../source"
OUTPUT_DIR = f"{DOCS_DIR}/object_model/types"
OBJECT_MODEL_DOC_FILE = f"{DOCS_DIR}/object_model.rst"
CONSORTIA_DOC_FILE = f"{DOCS_DIR}/object_model/data/consortia.rst"
SUBMISSION_CENTERS_DOC_FILE = f"{DOCS_DIR}/object_model/data/submission_centers.rst"
FILE_FORMATS_DOC_FILE = f"{DOCS_DIR}/object_model/data/file_formats.rst"
REFERENCE_GENOMES_DOC_FILE = f"{DOCS_DIR}/object_model/data/reference_genomes.rst"
# Two copies of the reference data files because so accessible from top level (under REFERENCE)
# and under object_model/data; just for convenience at the top level; would not need to do this
# if we did not care about the URL path - would just put it at top level in that case, which is
# needed otherwise will not appear in left menu, but nice to have the (main/default) reference
# file within object_model/data URL path.
CONSORTIA_TOP_DOC_FILE = f"{DOCS_DIR}/consortia.rst"
SUBMISSION_CENTERS_TOP_DOC_FILE = f"{DOCS_DIR}/submission_centers.rst"
FILE_FORMATS_TOP_DOC_FILE = f"{DOCS_DIR}/file_formats.rst"
REFERENCE_GENOMES_TOP_DOC_FILE = f"{DOCS_DIR}/reference_genomes.rst"
TYPE_HIERARCHY_DOC_FILE = f"{DOCS_DIR}/object_model/type_hierarchy.rst"
SMAHT_BASE_URL = "https://data.smaht.org"


def main():

    parser = argparse.ArgumentParser(description="Generate Portal schema (rst) documentation.")
    parser.add_argument("--ini", type=str, required=False, default=None,
                        help=f"Name of the application .ini file.")
    parser.add_argument("--env", "-e", type=str, required=False, default=None,
                        help=f"Environment name (key from ~/.smaht-keys.json).")
    parser.add_argument("--verbose", action="store_true", required=False, default=False, help="Verbose output.")
    parser.add_argument("--debug", action="store_true", required=False, default=False, help="Debugging output.")
    args = parser.parse_args()

    portal = _create_portal(ini=args.ini, env=args.env or os.environ.get("SMAHT_ENV"),
                            verbose=args.verbose, debug=args.debug)

    if portal.server:
        global SMAHT_BASE_URL
        SMAHT_BASE_URL = portal.server

    schemas = _get_schemas(portal)
    for schema_name in schemas:
        schema = schemas[schema_name]
        schema_doc = _gendoc_schema(schema_name, schema, schemas=schemas, portal=portal)
        _update_schema_file(schema_name, schema_doc)

    _update_object_model_file(schemas, portal)
    _update_type_hierarchy_file(schemas, portal)

    if not NODATA:
        _update_consortia_file(portal)
        _update_submission_centers_file(portal)
        _update_file_formats_file(portal)
        _update_reference_genomes_file(portal)


def _gendoc_schema(schema_name: str, schema: dict, schemas: dict, portal: Portal) -> str:
    content = ""
    if not (content := _get_template("object_model_type")):
        return content
    content_schema_title = f"{'=' * len(schema_name)}\n{schema_name}\n{'=' * len(schema_name)}\n\n"
    content = content.replace("{schema_title}", content_schema_title)
    content = content.replace("{schema_name}", schema_name)
    content = content.replace("{schema_name_camel}", camel_case_to_snake_case(schema_name))
    content = content.replace("{smaht_url}", SMAHT_BASE_URL)

    if schema.get("isAbstract") is True:
        content = content.replace("{schema_abstract}",
                                  "<u><b style='color:darkorange;'>abstract</b></u> (cannot be created directly)")
    if schema_description := schema.get("description"):
        if not schema_description.endswith("."):
            schema_description += "."
        content = content.replace("{schema_description}", f"<br /><u>Description</u>: {schema_description}")

    if parent_schema_name := _get_parent_schema_name(schema):
        content = content.replace("{parent_schema}",
                                  f"Its <b><a href='../type_hierarchy.html' style='color:black;'>parent</a></b> type is:"
                                  f" <a href={camel_case_to_snake_case(parent_schema_name)}.html>"
                                  f"<u>{parent_schema_name}</u></a>.")

    if content_derived_schemas := _gendoc_derived_schemas(schema_name, schemas):
        content = content.replace("{derived_schemas}", f"Its <b><a href='../type_hierarchy.html' style='color:black;'>derived</a></b> types are: {content_derived_schemas}.")

    if content_referencing_schemas := _gendoc_referencing_schemas(schema_name, schemas):
        content = content.replace("{referencing_schemas}",
                                  f"Types <b>referencing</b> this type are: {content_referencing_schemas}.")

    if not NODATA:
        if schema_name == "Consortium":
            content = content.replace("{tip_section}",
                                      "\n.. tip::\n    See consortium values here:"
                                      " `Consortia <../data/consortia.html>`_\n\n")
        elif schema_name == "SubmissionCenter":
            content = content.replace("{tip_section}",
                                      "\n.. tip::\n    See submission center values here:"
                                      " `Submission Centers <../data/submission_centers.html>`_\n\n")
        elif schema_name == "FileFormat":
            content = content.replace("{tip_section}",
                                      "\n.. tip::\n    See file format values here:"
                                      " `File Formats <../data/file_formats.html>`_\n\n")
        elif schema_name == "ReferenceGenome":
            content = content.replace("{tip_section}",
                                      "\n.. tip::\n    See reference genome values here:"
                                      " `Reference Genomes <../data/reference_genomes.html>`_\n\n")
    else:
        content = content.replace(
            "{tip_section}",
            f"\n.. tip::\n\n  .. raw::  html\n\n    <i>See actual {schema_name} data "
            f"<a target='_blank' href='{SMAHT_BASE_URL}/search/?type={schema_name}'><b>here"
            f"<span class='fa fa-external-link' style='left:6pt;position:relative;top:1pt;' /></b></a></i>\n")

    if content_required_properties_section := _gendoc_required_properties_section(schema):
        content = content.replace("{required_properties_section}", content_required_properties_section)

    if content_identifying_properties_section := _gendoc_identifying_properties_section(schema):
        content = content.replace("{identifying_properties_section}", content_identifying_properties_section)

    if content_reference_properties_section := _gendoc_reference_properties_section(schema):
        content = content.replace("{reference_properties_section}", content_reference_properties_section)

    if content_properties_table := _gendoc_properties_table(schema):
        content = content.replace("{properties_table}", content_properties_table)

    return _cleanup_content(content)


def _gendoc_referencing_schemas(schema_name: str, schemas: dict) -> str:
    content = ""
    if schemas and (referencing_schemas := _get_referencing_schemas(schema_name, schemas)):
        for referencing_schema_name in referencing_schemas:
            if content:
                content += ", "
            content += (
                f"<a href='{camel_case_to_snake_case(referencing_schema_name)}.html'>"
                f"<u>{referencing_schema_name}</u></a>")
    return content


def _gendoc_derived_schemas(schema_name: str, schemas: dict) -> str:
    content = ""
    if schemas and (derived_schemas := _get_derived_schemas(schema_name, schemas)):
        for derived_schema_name in derived_schemas:
            if content:
                content += ", "
            content += (
                f"<a href='{camel_case_to_snake_case(derived_schema_name)}.html'><u>{derived_schema_name}</u></a>")
    return content


def _gendoc_required_properties_section(schema: dict) -> str:
    content = ""
    if content_required_properties_table := _gendoc_required_properties_table(schema):
        if not (content := _get_template("required_properties_section")):
            return content
        content_required_properties_table = _normalize_spaces(content_required_properties_table)
        content = content.replace("{required_properties_table}", content_required_properties_table)
    return content


def _gendoc_required_properties_table(schema: dict) -> str:
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
        if (not property_name) or (property_name in IGNORE_PROPERTIES):
            continue
        if not (property := properties[property_name]):
            continue
        if not (property_type := property.get("type")):
            continue
        if not (property_link_to := property.get("linkTo")):
            property_link_to = property.get("items", {}).get("linkTo")
        property_description = None
        if not NODATA:
            if property_link_to == "Consortium":
                property_description = (
                    "<br /><small><i>Click <a href='../data/consortia.html'>here</a> to see values.</i></small>")
            elif property_link_to == "SubmissionCenter":
                property_description = (
                    "<br /><small><i>Click <a href='../data/submission_centers.html'>"
                    "here</a> to see values.</i></small>")
            elif property_link_to == "FileFormat":
                property_description = (
                    "<br /><small><i>Click <a href='../data/file_formats.html'>here</a> to see values.</i></small>")
            elif property_link_to == "ReferenceGenome":
                property_description = (
                    "<br /><small><i>Click <a href='../data/reference_genomes.html'>"
                    "here</a> to see values.</i></small>")
        else:
            if property_link_to in ["Consortium", "SubmissionCenter", "FileFormat", "ReferenceGenome"]:
                property_description = (
                    f"<br /><i>See values "
                    f"<a target='_blank' href='{SMAHT_BASE_URL}/search/?type={property_link_to}'>"
                    f"<b>here</b><span class='fa fa-external-link' style='left:6pt;position:relative;top:1pt;' />"
                    f"</a></i>")
        if property_type == "array":
            if property_items := property.get("items"):
                if property_items.get("enum"):
                    property_type = f"{property_type} of enum"
                elif property_array_type := property_items.get("type"):
                    property_type = f"{property_type} of {property_array_type}"
        simple_properties.append({"name": property_name, "type": property_type,
                                  "link_to": property_link_to, "description": property_description})
    content_simple_property_rows = _gendoc_simple_properties(simple_properties, kind="required")
    content = template_required_properties_table
    content = content.replace("{required_property_rows}", content_simple_property_rows)
    content_oneormore_property_rows = ""
    if isinstance(any_of := schema.get("anyOf"), list):
        # Very special case.
        if ((any_of == [{"required": ["submission_centers"]}, {"required": ["consortia"]}]) or
            (any_of == [{"required": ["consortia"]}, {"required": ["submission_centers"]}])):  # noqa
            if template_oneormore_property_rows := _get_template("oneormore_property_rows"):
                content_oneormore_property_rows = template_oneormore_property_rows
                content_oneormore_property_rows = (
                    content_oneormore_property_rows.replace("{oneormore_properties_list}",
                                                            "<b style='color:darkred;'>consortia</b>, "
                                                            "<b style='color:darkred;'>submission_centers</b>"))
                if not NODATA:
                    content_oneormore_simple_property_rows = _gendoc_simple_properties(
                        [{"name": "consortia", "type": "array of string", "link_to": "Consortium",
                          "description": "<br /><small><i>Click <a href='../data/consortia.html'>here</a>"
                                         " to see values.</i></small>"},
                         {"name": "submission_centers", "type": "array of string", "link_to": "SubmissionCenter",
                          "description": "<br /><small><i>Click <a href='../data/submission_centers.html'>here</a>"
                                         " to see values.</i></small>"}],
                        kind="oneormore-required")
                else:
                    content_oneormore_simple_property_rows = _gendoc_simple_properties(
                        [{"name": "consortia", "type": "array of string", "link_to": "Consortium",
                          "description":
                          f"<br /><i>See values "
                          f"<a target='_blank' href='{SMAHT_BASE_URL}/search/?type=Consortium'>"
                          f"<b>here</b><span class='fa fa-external-link' style='left:6pt;position:relative;top:1pt;' />"
                          f"</a></i>"},
                         {"name": "submission_centers", "type": "array of string", "link_to": "SubmissionCenter",
                          "description":
                          f"<br /><i>See values "
                          f"<a target='_blank' href='{SMAHT_BASE_URL}/search/?type=SubmissionCenter'>"
                          f"<b>here</b><span class='fa fa-external-link' style='left:6pt;position:relative;top:1pt;' />"
                          f"</a></i>"}],
                        kind="oneormore-required")

                content_oneormore_property_rows = (
                    content_oneormore_property_rows.replace("{oneormore_property_rows}",
                                                            content_oneormore_simple_property_rows))
    content = content.replace("{oneormore_property_rows}", content_oneormore_property_rows)
    return content


def _gendoc_identifying_properties_section(schema: dict) -> str:
    content = ""
    if content_identifying_properties_table := _gendoc_identifying_properties_table(schema):
        if not (content := _get_template("identifying_properties_section")):
            return content
        content_identifying_properties_table = _normalize_spaces(content_identifying_properties_table)
        content = content.replace("{identifying_properties_table}", content_identifying_properties_table)
    return content


def _gendoc_identifying_properties_table(schema: dict) -> str:
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
        if (not property_name) or (property_name in IGNORE_PROPERTIES):
            continue
        if not (property := properties[property_name]):
            continue
        if not (property_type := property.get("type")):
            continue
        if property_type == "array":
            if property_items := property.get("items"):
                if property_items.get("enum"):
                    property_type = f"{property_type} of enum"
                elif property_array_type := property_items.get("type"):
                    property_type = f"{property_type} of {property_array_type}"
        simple_properties.append({"name": property_name, "type": property_type})
    content_simple_property_rows = _gendoc_simple_properties(simple_properties, kind="identifying")
    content = template_identifying_properties_table
    content = content.replace("{identifying_property_rows}", content_simple_property_rows)
    return content


def _gendoc_reference_properties_section(schema: dict) -> str:
    content = ""
    if content_reference_properties_table := _gendoc_reference_properties_table(schema):
        if not (content := _get_template("reference_properties_section")):
            return content
        content_reference_properties_table = _normalize_spaces(content_reference_properties_table)
        content = content.replace("{reference_properties_table}", content_reference_properties_table)
    return content


def _gendoc_reference_properties_table(schema: dict) -> str:
    content = ""
    if not isinstance(schema, dict) or not schema:
        return content
    if not (properties := schema.get("properties", [])):
        return content
    if not (template_reference_properties_table := _get_template("reference_properties_table")):
        return content
    required_properties = schema.get("required", [])
    simple_properties = []
    for property_name in properties:
        if (not property_name) or (property_name in IGNORE_PROPERTIES):
            continue
        if not (property := properties[property_name]):
            continue
        if not (property_type := property.get("type")):
            continue
        if not (property_link_to := property.get("linkTo")):
            if not (property_link_to := property.get("items", {}).get("linkTo")):
                continue
        property_description = None
        if not NODATA:
            if property_link_to == "Consortium":
                property_description = (
                    "<br /><small><i>Click <a href='../data/consortia.html'>here</a> to see values.</i></small>")
            elif property_link_to == "SubmissionCenter":
                property_description = (
                    "<br /><small><i>Click <a href='../data/submission_centers.html'>"
                    "here</a> to see values.</i></small>")
            elif property_link_to == "FileFormat":
                property_description = (
                    "<br /><small><i>Click <a href='../data/file_formats.html'>here</a> to see values.</i></small>")
            elif property_link_to == "ReferenceGenome":
                property_description = (
                     "<br /><small><i>Click <a href='../data/reference_genomes.html'>"
                     "here</a> to see values.</i></small>")
        else:
            if property_link_to in ["Consortium", "SubmissionCenter", "FileFormat", "ReferenceGenome"]:
                property_description = (
                    f"<br /><i>See values "
                    f"<a target='_blank' href='{SMAHT_BASE_URL}/search/?type={property_link_to}'>"
                    f"<b>here</b><span class='fa fa-external-link' style='left:6pt;position:relative;top:1pt;' />"
                    f"</a></i>")
        content_property_type = (
            f"<a href={camel_case_to_snake_case(property_link_to)}.html style='font-weight:bold;color:green;'>"
            f"<u>{property_link_to}</u></a><br />{property_type}")
        if property_type == "array":
            if property_items := property.get("items"):
                if property_array_type := property_items.get("type"):
                    content_property_type = f"{content_property_type} of {property_array_type}"
        simple_properties.append({"name": property_name, "type": content_property_type,
                                  "required": property_name in required_properties,
                                  "description": property_description})
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
    for property in sorted(properties, key=lambda item: item.get("name")):
        property_name = property["name"]
        property_type = property["type"]
        property_description = property.get("description")
        if kind == "identifying":
            property_name = f"<span style='color:blue'>{property_name}</span>"
        elif kind == "required" or property.get("required") is True:
            property_name = f"<span style='color:red'>{property_name}</span>"
        elif kind == "oneormore-required":
            property_name = f"<span style='color:darkred'>{property_name}</span>"
        content_simple_property = copy.deepcopy(template_simple_property_row)
        content_simple_property = content_simple_property.replace("{property_name}", property_name)
        if property_link_to := property.get("link_to"):
            property_type = (
                f"<a href='{camel_case_to_snake_case(property_link_to)}.html'><b style='color:green;'>"
                f"<u>{property_link_to}</u></b></a><br />{property_type}")
        content_simple_property = content_simple_property.replace("{property_type}", property_type)
        if property_description:
            content_simple_property = content_simple_property.replace("{property_description}", property_description)
        result += content_simple_property
    return result


def _gendoc_properties_table(schema: dict, _level: int = 0, _parents: List[str] = []) -> str:
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
        if (not property_name) or (property_name in IGNORE_PROPERTIES):
            continue
        if not (property := properties[property_name]):
            continue
        if not (property_type := property.get("type")):
            continue
        content_property_row = template_property_row
        content_property_name = property_name
        content_property_type = property_type
        property_attributes = []
        property_array_enum = None
        property_array_link_to = False
        property_link_to = property.get("linkTo")
        property_link_to_original = property_link_to
        if not property_link_to:
            if property_link_to := (property_items := property.get("items", {})).get("linkTo"):
                property_link_to_original = property_link_to
                content_property_type = (
                    f"<a href={camel_case_to_snake_case(property_link_to)}.html style='font-weight:bold;color:green;'>"
                    f"<u>{property_link_to}</u></a>")
                property_link_to = None
                property_array_link_to = True
                if property_type_array := property_items.get("type") if property_items else None:
                    property_attributes.append(f"array of {property_type_array}")
                else:
                    property_attributes.append(f"array")
        if property_type == "array":
            if property_items := property.get("items"):
                if property_array_enum := property_items.get("enum"):
                    content_property_type = f"<b>{property_type}</b> of <b>enum</b>"
                if property_array_type := property_items.get("type"):
                    if not property_array_link_to and not property_array_enum:
                        content_property_type = f"<b>{property_type}</b> of <b>{property_array_type}</b>"
                    if property_array_type == "object":
                        content_nested_array = _gendoc_properties_table(
                            property_items,
                            _level=_level + 1, _parents=_parents + [property_name])
                # TODO
                # Note that minLength/maxLength (I think) refers to the length of the string;
                # the minItems/maxItems refers to the length of the array;
                # it does not appear that minLength/maxLength is every used outside of arrays.
                if (min_items := property.get("minItems")) is not None:
                    property_attributes.append(f"min items: {min_items}")
                if (max_items := property.get("maxItems")) is not None:
                    property_attributes.append(f"max items: {max_items}")
                if (min_length := property_items.get("minLength")) is not None:
                    property_attributes.append(
                        f"min{' string' if property_array_type == 'string' else ''} length: {min_length}")
                if (max_length := property_items.get("maxLength")) is not None:
                    property_attributes.append(
                        f"max{' string' if property_array_type == 'string' else ''} length: {max_length}")
                if property_items.get("permission") == "restricted_fields":
                    property_attributes.append("restricted")
            if property.get("uniqueItems"):
                property_attributes.append("unique")
            if property.get("permission") == "restricted_fields":
                property_attributes.append("restricted")
        elif property_type == "object":
            content_nested_object = _gendoc_properties_table(
                property,
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
        enum = None
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
                f"<a href={camel_case_to_snake_case(property_link_to)}.html style='font-weight:bold;color:green;'>"
                f"<u>{property_link_to}</u></a>")
            property_attributes.append(f"{property_type}")
        elif (enum := property.get("enum", [])) or property_array_enum:
            if not property_array_enum:
                content_property_type = f"<b>enum</b> of <b>{content_property_type}</b>"
            content_property_name = (
                f"<u>{content_property_name}</u>"
                f"<span style='font-weight:normal;font-family:arial;color:#222222;'>")
            for enum_value in sorted(enum if not property_array_enum else property_array_enum):
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
            content_property_type_array = ""
            for type in property_type:
                if content_property_type_array:
                    content_property_type_array += " or<br />"
                content_property_type_array += f"<b>{type}</b>"
            content_property_type = content_property_type_array
        elif property_type != "array" and not enum:
            content_property_type = f"<b>{content_property_type}</b>"
        if default:
            if isinstance(default, bool):
                default = str(default).lower()
            property_attributes.append(f"default: {default}")
        if (minimum := property.get("minimum")) is not None:
            property_attributes.append(f"min value: {minimum}")
        if (maximum := property.get("maximum")) is not None:
            property_attributes.append(f"max value: {maximum}")
        if (min_length := property.get("minLength")) is not None:
            property_attributes.append(f"min length: {min_length}")
        if (max_length := property.get("maxLength")) is not None:
            property_attributes.append(f"max length: {max_length}")
        if property.get("uniqueKey") is True:
            property_attributes.append(f"unique")
        if property_attributes:
            content_property_type = f"<u>{content_property_type}</u><br />"
            for property_attribute in property_attributes:
                content_property_type += f"•&nbsp;{property_attribute}<br />"
        if pattern := (property.get("pattern") or property.get("items", {}).get("pattern")):
            if property_name in required_properties:
                color = "darkred"
            elif property_name in identifying_properties:
                color = "darkblue"
            else:
                color = "inherit"
            property_description += (
                f"<br />Must adhere to (regex) <span style='color:{color};'><u>pattern</u>:&nbsp;"
                f"<small style='font-family:monospace;'><b>{pattern}</b></small></span>")
        if _parents:
            content_parents = "<span style='font-weight:normal;'>"
            for index, parent in enumerate(_parents):
                if index > 0:
                    content_parents += f" <b>.</b> "
                content_parents += f"{parent}"
            content_parents += "</span>"
            content_property_name = f"{content_parents} <b>.</b> {content_property_name}"
        if not NODATA:
            if property_link_to_original == "Consortium":
                property_description += (
                    "<br /><small><i>Click <a href='../data/consortia.html'>here</a> to see values.</i></small>")
            elif property_link_to_original == "SubmissionCenter":
                property_description += (
                    "<br /><small><i>Click <a href='../data/submission_centers.html'>"
                    "here</a> to see values.</i></small>")
            elif property_link_to_original == "FileFormat":
                if property_description:
                    property_description += "<br />"
                property_description += (
                    "<small><i>Click <a href='../data/file_formats.html'>here</a> to see values.</i></small>")
            elif property_link_to_original == "ReferenceGenome":
                if property_description:
                    property_description += "<br />"
                property_description += (
                    "<small><i>Click <a href='../data/reference_genomes.html'>here</a> to see values.</i></small>")
        else:
            if property_link_to_original in ["Consortium", "SubmissionCenter", "FileFormat", "ReferenceGenome"]:
                if property_description:
                    property_description += "<br />"
                property_description += (
                    f"<i>See values "
                    f"<a target='_blank' href='{SMAHT_BASE_URL}/search/?type={property_link_to_original}'>"
                    f"<b>here</b><span class='fa fa-external-link' style='left:6pt;position:relative;top:1pt;' />"
                    f"</a></i>")
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
    return _normalize_spaces(content)


def _update_consortia_file(portal: Portal) -> None:
    if not (template_consortia_page := _get_template("consortia_page")):
        return
    if not (content_consortia_table := _gendoc_consortia_table(portal)):
        return
    content_consortia_page = template_consortia_page
    content_consortia_page = content_consortia_page.replace("{consortia_table}", content_consortia_table)
    with io.open(CONSORTIA_DOC_FILE, "w") as f:
        f.writelines(content_consortia_page)
    with io.open(CONSORTIA_TOP_DOC_FILE, "w") as f:
        content_consortia_page = content_consortia_page.replace("../types/", "object_model/types/")
        f.writelines(content_consortia_page)


def _gendoc_consortia_table(portal: Portal) -> str:
    content = ""
    if not (template_consortia_table := _get_template("consortia_table")):
        return content
    if not (template_consortia_row := _get_template("consortia_row")):
        return content
    if not (consortia := portal.get_metadata("/consortia")):
        return content
    consortia = sorted(consortia.get("@graph", []), key=lambda key: key.get("identifier"))
    content_consortia_rows = ""
    for consortium in consortia:
        if ((consortium_name := consortium.get("identifier")) and
            (consortium_uuid := consortium.get("uuid"))):  # noqa
            if consortium_description := consortium.get("title", ""):
                if not consortium_description.endswith("."):
                    consortium_description += "."
            content_consortia_row = template_consortia_row
            content_consortia_row = content_consortia_row.replace("{consortium_name}", consortium_name)
            content_consortia_row = content_consortia_row.replace("{consortium_uuid}", consortium_uuid)
            content_consortia_row = content_consortia_row.replace("{consortium_description}",
                                                                  consortium_description or "-")
            content_consortia_row = content_consortia_row.replace("{consortium_url}",
                                                                  f"{portal.server}/{consortium_uuid}")
            content_consortia_rows += content_consortia_row
    consortia_url = f"{SMAHT_BASE_URL}/search/?type=Consortium"
    content = template_consortia_table
    content = content.replace("{consortia_rows}", content_consortia_rows)
    content = content.replace("{consortia_url}", consortia_url)
    return _normalize_spaces(content)


def _update_submission_centers_file(portal: Portal) -> None:
    if not (template_submission_centers_page := _get_template("submission_centers_page")):
        return
    if not (content_submission_centers_table := _gendoc_submission_centers_table(portal)):
        return
    content_submission_centers_page = template_submission_centers_page
    content_submission_centers_page = (
        content_submission_centers_page.replace("{submission_centers_table}",
                                                content_submission_centers_table))
    with io.open(SUBMISSION_CENTERS_DOC_FILE, "w") as f:
        f.writelines(content_submission_centers_page)
    with io.open(SUBMISSION_CENTERS_TOP_DOC_FILE, "w") as f:
        content_submission_centers_page = content_submission_centers_page.replace("../types/", "object_model/types/")
        f.writelines(content_submission_centers_page)


def _gendoc_submission_centers_table(portal: Portal) -> str:
    content = ""
    if not (template_submission_centers_table := _get_template("submission_centers_table")):
        return content
    if not (template_submission_centers_row := _get_template("submission_centers_row")):
        return content
    if not (submission_centers := portal.get_metadata("/submission-centers?limit=1000")):
        return content
    submission_centers = sorted(submission_centers.get("@graph", []), key=lambda key: key.get("title"))
    content_submission_centers_rows = ""
    for submission_center in submission_centers:
        if ((submission_center_name := submission_center.get("identifier")) and
            (submission_center_uuid := submission_center.get("uuid"))):  # noqa
            submission_center_code = submission_center.get("code", "")
            submission_center_title = submission_center.get("title", "")
            if submission_center_description := submission_center.get("description", ""):
                if not submission_center_description.endswith("."):
                    submission_center_description += "."
            if isinstance(submission_center_leader := submission_center.get("leader", ""), dict):
                if submission_center_leader_name := submission_center_leader.get("display_title", ""):
                    if submission_center_leader_url := submission_center_leader.get("@id", ""):
                        submission_center_leader_url = f"{portal.server}/{submission_center_leader_url}"
                else:
                    submission_center_leader = None
            if submission_center_leader:
                if submission_center_description:
                    submission_center_description += "<br />"
                if submission_center_leader_url:
                    submission_center_description += (
                        f"<u>Leader</u>: <a target='_blank' href='{submission_center_leader_url}'>"
                        f"<b>{submission_center_leader_name}</b></a>")
                else:
                    submission_center_description += f"<u>Leader</u>: <b>{submission_center_leader}</b>"
            elif submission_center_name == "smaht_dac":
                if submission_center_description:
                    submission_center_description += "<br />"
                submission_center_description += f"<u>Contact</u>: <b>{SMAHT_DAC_EMAIL}</b>"
            content_submission_centers_row = template_submission_centers_row
            content_submission_centers_row = (
                content_submission_centers_row.replace("{submission_center_name}", submission_center_name))
            content_submission_centers_row = (
                content_submission_centers_row.replace("{submission_center_title}", submission_center_title))
            content_submission_centers_row = (
                content_submission_centers_row.replace("{submission_center_uuid}", submission_center_uuid))
            content_submission_centers_row = (
                content_submission_centers_row.replace("{submission_center_code}", submission_center_code))
            content_submission_centers_row = (
                content_submission_centers_row.replace("{submission_center_description}",
                                                       submission_center_description or "-"))
            content_submission_centers_row = (
                content_submission_centers_row.replace("{submission_center_url}",
                                                       f"{portal.server}/{submission_center_uuid}"))
            content_submission_centers_rows += content_submission_centers_row
    submission_centers_url = f"{SMAHT_BASE_URL}/search/?type=SubmissionCenter"
    content = template_submission_centers_table
    content = content.replace("{submission_centers_rows}", content_submission_centers_rows)
    content = content.replace("{submission_centers_url}", submission_centers_url)
    return _normalize_spaces(content)


def _update_file_formats_file(portal: Portal) -> None:
    if not (template_file_formats_page := _get_template("file_formats_page")):
        return
    if not (content_file_formats_table := _gendoc_file_formats_table(portal)):
        return
    content_file_formats_aligned_reads_table = _gendoc_file_formats_table(portal, "AlignedReads")
    content_file_formats_unaligned_reads_table = _gendoc_file_formats_table(portal, "UnalignedReads")
    content_file_formats_variant_calls_table = _gendoc_file_formats_table(portal, "VariantCalls")
    content_file_formats_page = template_file_formats_page
    content_file_formats_page = content_file_formats_page.replace("{file_formats_all}",
                                                                  content_file_formats_table)
    content_file_formats_page = content_file_formats_page.replace("{file_formats_aligned_reads}",
                                                                  content_file_formats_aligned_reads_table)
    content_file_formats_page = content_file_formats_page.replace("{file_formats_unaligned_reads}",
                                                                  content_file_formats_unaligned_reads_table)
    content_file_formats_page = content_file_formats_page.replace("{file_formats_variant_calls}",
                                                                  content_file_formats_variant_calls_table)
    with io.open(FILE_FORMATS_DOC_FILE, "w") as f:
        f.write(content_file_formats_page)
    with io.open(FILE_FORMATS_TOP_DOC_FILE, "w") as f:
        content_file_formats_page = content_file_formats_page.replace("../types/", "object_model/types/")
        f.write(content_file_formats_page)


def _gendoc_file_formats_table(portal: Portal, valid_item_type: Optional[str] = None) -> str:
    content = ""
    if not (template_file_formats_table := _get_template("file_formats_table")):
        return content
    if not (template_file_formats_row := _get_template("file_formats_row")):
        return content
    file_formats = None
    try:
        if not (file_formats := portal.get_metadata("/file-formats?limit=1000")):
            return content
    except Exception:
        return content
    file_formats = sorted(file_formats.get("@graph", []), key=lambda key: key.get("identifier"))
    content_file_formats_rows = ""
    for file_format in file_formats:
        file_format_valid_item_types = file_format.get("valid_item_types")
        if valid_item_type and ((not file_format_valid_item_types) or
                                (valid_item_type not in file_format_valid_item_types)):
            continue
        if ((file_format_name := file_format.get("identifier")) and
            (file_format_uuid := file_format.get("uuid"))):  # noqa
            if file_format_description := file_format.get("description", ""):
                if not file_format_description.endswith("."):
                    file_format_description += "."
            if file_format_file_extension := file_format.get("standard_file_extension"):
                if file_format_description:
                    file_format_description += "<br />"
                file_format_description += f"<u>File Extension</u>: <b>.{file_format_file_extension}</b>"
            if file_format_valid_item_types := file_format.get("valid_item_types"):
                if file_format_description:
                    file_format_description += "<br />"
                file_format_description += f"<u>Valid Types</u>: "
                for index, file_format_valid_item_type in enumerate(sorted(file_format_valid_item_types)):
                    if index > 0:
                        file_format_description += ", "
                    file_format_description += (
                        f"<a href='../types/{camel_case_to_snake_case(file_format_valid_item_type)}.html'>"
                        f"{file_format_valid_item_type}</b>")
            content_file_formats_row = template_file_formats_row
            content_file_formats_row = content_file_formats_row.replace("{file_format_name}", file_format_name)
            content_file_formats_row = content_file_formats_row.replace("{file_format_uuid}", file_format_uuid)
            content_file_formats_row = content_file_formats_row.replace("{file_format_description}",
                                                                        file_format_description or "-")
            content_file_formats_row = (
                content_file_formats_row.replace("{file_format_url}", f"{portal.server}/{file_format_uuid}"))
            content_file_formats_rows += content_file_formats_row
    file_formats_url = f"{SMAHT_BASE_URL}/search/?type=FileFormat"
    if valid_item_type:
        file_formats_url += f"&valid_item_types={valid_item_type}"
    content = template_file_formats_table
    content = content.replace("{file_formats_url}", file_formats_url)
    content = content.replace("{file_formats_rows}", content_file_formats_rows)
    return _normalize_spaces(content)


def _update_reference_genomes_file(portal: Portal) -> None:
    if not (template_reference_genomes_page := _get_template("reference_genomes_page")):
        return
    if not (content_reference_genomes_table := _gendoc_reference_genomes_table(portal)):
        return
    content_reference_genomes_page = template_reference_genomes_page
    content_reference_genomes_page = content_reference_genomes_page.replace("{reference_genomes}",
                                                                            content_reference_genomes_table)
    with io.open(REFERENCE_GENOMES_DOC_FILE, "w") as f:
        f.write(content_reference_genomes_page)
    with io.open(REFERENCE_GENOMES_TOP_DOC_FILE, "w") as f:
        content_reference_genomes_page = content_reference_genomes_page.replace("../types/", "object_model/types/")
        f.write(content_reference_genomes_page)


def _gendoc_reference_genomes_table(portal: Portal, valid_item_type: Optional[str] = None) -> str:
    content = ""
    if not (template_reference_genomes_table := _get_template("reference_genomes_table")):
        return content
    if not (template_reference_genomes_row := _get_template("reference_genomes_row")):
        return content
    reference_genomes = None
    try:
        if not (reference_genomes := portal.get_metadata("/reference-genomes?limit=1000")):
            return content
    except Exception:
        return content
    reference_genomes = sorted(reference_genomes.get("@graph", []), key=lambda key: key.get("identifier"))
    content_reference_genomes_rows = ""
    for reference_genome in reference_genomes:
        if ((reference_genome_name := reference_genome.get("identifier")) and
            (reference_genome_uuid := reference_genome.get("uuid"))):  # noqa
            reference_genome_description = reference_genome.get("title")
            content_reference_genomes_row = template_reference_genomes_row
            content_reference_genomes_row = content_reference_genomes_row.replace("{reference_genome_name}",
                                                                                  reference_genome_name)
            content_reference_genomes_row = content_reference_genomes_row.replace("{reference_genome_uuid}",
                                                                                  reference_genome_uuid)
            content_reference_genomes_row = content_reference_genomes_row.replace("{reference_genome_description}",
                                                                                  reference_genome_description or "-")
            content_reference_genomes_row = (
                content_reference_genomes_row.replace("{reference_genome_url}",
                                                      f"{portal.server}/{reference_genome_uuid}"))
            content_reference_genomes_rows += content_reference_genomes_row
    reference_genomes_url = f"{SMAHT_BASE_URL}/search/?type=ReferenceGenome"
    content = template_reference_genomes_table
    content = content.replace("{reference_genomes_rows}", content_reference_genomes_rows)
    content = content.replace("{reference_genomes_url}", reference_genomes_url)
    return _normalize_spaces(content)


def _update_schema_file(schema_name: str, schema_doc_content: str) -> None:
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    output_file = f"{os.path.join(OUTPUT_DIR, camel_case_to_snake_case(schema_name))}.rst"
    with io.open(output_file, "w") as f:
        f.write(schema_doc_content)


def _update_object_model_file(schemas: dict, portal: Portal) -> None:
    if not (template_object_model_page := _get_template("object_model_page")):
        return
    nschemas = len(schemas) - 1
    content_schema_types = ""
    content_schema_types_left = ""
    content_schema_types_middle = ""
    content_schema_types_right = ""
    ncolumns = 3
    nschemas_one_part = nschemas // ncolumns
    nschemas_one_part_remainder = nschemas % ncolumns
    nschemas_distribution = [nschemas_one_part + (1 if n < nschemas_one_part_remainder else 0) for n in range(ncolumns)]
    nschemas_left, nschemas_middle, nschemas_right = nschemas_distribution
    for index, schema_name in enumerate(schemas):
        schema = schemas[schema_name]
        is_schema_abstract = schema.get("isAbstract") is True
        content_schema_types += (
            f"{(' ' * 3) if index > 0 else ''}object_model/types/{camel_case_to_snake_case(schema_name)}\n")
        content_schema_type = (
                f"<li><a href='object_model/types/{camel_case_to_snake_case(schema_name)}.html'>"
                f"{schema_name}</a>{' <small><b>(A)</b></small>' if is_schema_abstract else ''}</li>")
        if index < nschemas_left:
            content_schema_types_left += content_schema_type
        elif index < (nschemas_left + nschemas_right + 1):
            content_schema_types_middle += content_schema_type
        else:
            content_schema_types_right += content_schema_type
    content_object_model_page = template_object_model_page
    content_object_model_page = content_object_model_page.replace("{schema_types}", content_schema_types)
    content_object_model_page = content_object_model_page.replace("{schema_types_left}", content_schema_types_left)
    content_object_model_page = content_object_model_page.replace("{schema_types_middle}", content_schema_types_middle)
    content_object_model_page = content_object_model_page.replace("{schema_types_right}", content_schema_types_right)
    content_object_model_page = content_object_model_page.replace("{smaht_url}", SMAHT_BASE_URL)
    content_object_model_page = content_object_model_page.replace("{smaht_domain}",
                                                                  SMAHT_BASE_URL.replace("https://", ""))
    content_object_model_page = content_object_model_page.replace("{generated_datetime}",
                                                                  _get_current_datetime_string())
    try:
        content_object_model_page = content_object_model_page.replace("{smaht_portal_version}",
                                                                      portal.get_health().json().get("project_version"))
    except Exception:
        pass
    with io.open(OBJECT_MODEL_DOC_FILE, "w") as f:
        f.write(content_object_model_page)


def _update_type_hierarchy_file(schemas: dict, portal: Portal) -> None:
    if not (template_type_hierarchy_page := _get_template("type_hierarchy_page")):
        return
    if not (type_hierarchy := _gendoc_schemas_tree(schemas)):
        return
    content_type_hierarchy_page = template_type_hierarchy_page
    content_type_hierarchy_page = content_type_hierarchy_page.replace("{type_hierarchy}", type_hierarchy)
    with io.open(TYPE_HIERARCHY_DOC_FILE, "w") as f:
        f.write(content_type_hierarchy_page)


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
    schemas = portal.get_schemas()
    return {schema_name: schemas[schema_name] for schema_name in sorted(schemas) if schema_name not in IGNORE_TYPES}


def _get_schema(portal: Portal, name: str) -> Tuple[Optional[dict], Optional[str]]:
    if portal and name and (name := name.replace("_", "").replace("-", "").strip().lower()):
        if schemas := _get_schemas(portal):
            for schema_name in schemas:
                if schema_name.replace("_", "").replace("-", "").strip().lower() == name:
                    return schemas[schema_name], schema_name
    return None, None


def _get_parent_schema_name(schema: dict) -> Optional[str]:
    if (isinstance(schema, dict) and
        (parent_schema_name := schema.get("rdfs:subClassOf")) and
        (parent_schema_name := parent_schema_name.replace("/profiles/", "").replace(".json", "")) and
        (parent_schema_name != "Item")):  # noqa
        return parent_schema_name
    return None


def _get_referencing_schemas(schema_name: str, schemas: dict) -> List[str]:
    result = []
    for this_schema_name in schemas:
        if this_schema_name == schema_name:
            continue
        schema = schemas[this_schema_name]
        if properties := schema.get("properties"):
            for property_name in properties:
                if (not property_name) or (property_name in IGNORE_PROPERTIES):
                    continue
                property = properties[property_name]
                if property.get("linkTo") == schema_name:
                    result.append(this_schema_name)
                elif property.get("items", {}).get("linkTo") == schema_name:
                    result.append(this_schema_name)
    return sorted(list(set(result)))


def _get_derived_schemas(schema_name: str, schemas: dict) -> List[str]:
    result = []
    for this_schema_name in schemas:
        if this_schema_name == schema_name:
            continue
        if _get_parent_schema_name(schemas[this_schema_name]) == schema_name:
            result.append(this_schema_name)
    return result


def _get_schema_version(schema: dict) -> str:
    if version := schema.get("properties", {}).get("schema_version", {}).get("default", ""):
        if "." not in version:
            version = f"{version}.0"
        version = f"v{version}"
    return version


def _gendoc_schemas_tree(schemas: dict) -> str:
    root_name = "Types"
    def children_of(name: str):  # noqa
        nonlocal schemas
        children = []
        if not (name is None or isinstance(name, str)):
            return children
        if name == root_name:
            name = None
        for schema_name in (schemas if isinstance(schemas, dict) else {}):
            if _get_parent_schema_name(schemas[schema_name]) == name:
                children.append(schema_name)
        return sorted(children)
    def name_of(name: str) -> None:  # noqa
        nonlocal root_name, schemas
        abstract = (schemas[name].get("isAbstract") is True) if schemas.get(name) else False
        return (f"<a href='types/{camel_case_to_snake_case(name)}.html'>{name}</a>"
                f"{' <small><b>(A)</b></small>' if abstract else ''}"
                if name != root_name else f"<a href='../object_model.html#types'><b>{name}</b></a>")
    content = ""
    def collect_content(value: str) -> None:  # noqa
        nonlocal content
        content += f"{' ' * 8}{value}\n"
    _print_tree(root_name=root_name, children_of=children_of, name_of=name_of, print=collect_content)
    return content


def _print_tree(root_name: Optional[str],
                children_of: Callable,
                has_children: Optional[Callable] = None,
                name_of: Optional[Callable] = None,
                print: Callable = print) -> None:
    """
    Recursively prints as a tree structure the given root name and any of its
    children (again, recursively) as specified by the given children_of callable;
    the has_children may be specified, for efficiency, though if not specified
    it will use the children_of function to determine this; the name_of callable
    may be specified to modify the name before printing;

    :param directory: Directory name whose tree structure to print.
    """
    first = "└─ "
    space = "    "
    branch = "│   "
    tee = "├── "
    last = "└── "

    if not callable(children_of):
        return
    if not callable(has_children):
        has_children = lambda name: children_of(name) is not None  # noqa

    # This function adapted from stackoverflow.
    # Ref: https://stackoverflow.com/questions/9727673/list-directory-tree-structure-in-python
    def tree_generator(name: str, prefix: str = ""):
        contents = children_of(name)
        pointers = [tee] * (len(contents) - 1) + [last]
        for pointer, path in zip(pointers, contents):
            yield prefix + pointer + (name_of(path) if callable(name_of) else path)
            if has_children(path):
                extension = branch if pointer == tee else space
                yield from tree_generator(path, prefix=prefix+extension)
    print(first + ((name_of(root_name) if callable(name_of) else root_name) or "root"))
    for line in tree_generator(root_name, prefix="   "):
        print(line)


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
    return datetime.now().astimezone(tzlocal).strftime(f"%Y-%m-%d %-I:%M %p %Z")
    return datetime.now().astimezone(tzlocal).strftime(f"%A, %B %-d, %Y %-I:%M %p %Z")


def _usage(message: Optional[str] = None) -> None:
    if message:
        PRINT(f"ERROR: {message}")
    PRINT("USAGE: TODO")
    _exit()


def _exit(message: Optional[str] = None) -> None:
    if message:
        PRINT(f"ERROR: {message}")
    sys.exit(1)


if __name__ == "__main__":
    main()
