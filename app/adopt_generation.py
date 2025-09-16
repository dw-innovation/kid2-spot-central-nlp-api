import inflect
import os
import requests
import sys
from collections.abc import Iterable
from dotenv import load_dotenv

load_dotenv()
PROJECT_PATH = os.getcwd()
sys.path.append(PROJECT_PATH)

SEARCH_ENDPOINT = os.getenv("SEARCH_ENDPOINT")
COLOR_BUNDLE_SEARCH = os.getenv("COLOR_BUNDLE_SEARCH")
PLURAL_ENGINE = inflect.engine()
DEFAULT_DISTANCE = os.getenv("DEFAULT_DISTANCE")

load_dotenv()

def flatten(xs):
    """
    Recursively flatten a nested iterable into a flat generator.

    Args:
        xs (Iterable): Possibly nested iterable (lists/tuples/sets, etc.).

    Yields:
        Any: Each non-iterable element from the nested structure, preserving order.

    Notes:
        - Strings and bytes are treated as scalars (not iterated character-by-character).
    """
    for x in xs:
        if isinstance(x, Iterable) and not isinstance(x, (str, bytes)):
            yield from flatten(x)
        else:
            yield x


def is_nested_list(l):
    """
    Check whether a list contains at least one nested list.

    Args:
        l (list): The list to inspect.

    Returns:
        bool: True if any element is a list, otherwise False.

    Raises:
        TypeError: If `l` is not iterable (rare in this usage).
    """
    try:
        next(x for x in l if isinstance(x, list))

    except StopIteration:
        return False

    return True


class AdoptFuncError(Exception):
    """
    Custom exception for errors raised during the adopt-generation pipeline.

    Attributes:
        message (str): Human-readable description of the error cause.
    """
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


def search_osm_tag(entity):
    """
    Query the OSM tag search service for an entity name and return IMR hints.

    Args:
        entity (str): Tag or concept to look up (e.g., 'restaurant', 'door color').

    Returns:
        dict | list: Parsed JSON response from the search endpoint.

    Notes:
        - Uses the `SEARCH_ENDPOINT` URL from environment variables.
        - SSL verification is disabled (verify=False).
    """
    PARAMS = {"word": entity, "limit": 1, "detail": False}
    r = requests.get(
        url=SEARCH_ENDPOINT, params=PARAMS, verify=False
    )  # set verify to False to ignore SSL certificate
    return r.json()

def fetch_color_bundles(color:str):
    """
    Fetch a color bundle (synonyms/hex variants) for a given color name.

    Args:
        color (str): Base color string (e.g., 'brown', 'green').

    Returns:
        dict: Parsed JSON containing `color_values` and related metadata.

    Notes:
        - Uses `COLOR_BUNDLE_SEARCH` from environment variables.
        - SSL verification is disabled (verify=False).
    """
    PARAMS = {"color": color, "limit": 1, "detail": False}
    r = requests.get(
        url=COLOR_BUNDLE_SEARCH, params=PARAMS, verify=False
    )  # set verify to False to ignore SSL certificate
    return r.json()

def build_filters(node):
    """
    Build IMR-compatible filter blocks for a single parsed node.

    Workflow:
        1) Look up base filters for the node's name via `search_osm_tag`.
        2) Special-case brand entities (name starts with 'brand:') to inject
           the actual brand value in place of placeholders.
        3) If node has `properties`, look up property IMR blocks and merge them:
           - Respect explicit operators and values from the node properties.
           - Expand color properties via `fetch_color_bundles`.
           - Normalize into {"and": [...]} and {"or": [...]} structures.

    Args:
        node (dict): Parsed node with fields like:
            {
              "id": int,
              "name": str,
              "type": "nwr" | "cluster",
              "properties": [
                {"name": str, "operator": str, "value": Any}, ...
              ]
            }

    Returns:
        list[dict] | None: A list of filter dicts (e.g., [{"and": [...]}, ...]).
                           Returns None if no OSM results found.

    Raises:
        ValueError: When the property IMR block does not contain 'or' or 'and'.
    """
    node_name = node["name"]
    osm_results = search_osm_tag(node_name)
    if len(osm_results) == 0:
        return None
    ent_filters = osm_results[0]["imr"]

    if node_name.startswith('brand:'):
        brand_name = node_name.replace('brand:', '')
        ent_filters = [
            {
                'or': [
                    {**sub_item, 'value': brand_name if sub_item['value'] == '***example***' else sub_item['value']}
                    for sub_item in item['or']
                ]
            }
            for item in ent_filters
        ]

    processed_filters = []
    if len(ent_filters) > 0:
        if is_nested_list(ent_filters):
            processed_filters.extend(ent_filters[0])
        else:
            processed_filters.extend(ent_filters)

    if "properties" in node:
        node_flts = []

        node_flts.append(processed_filters[0])

        for node_flt in node["properties"]:
            ent_property = node_flt["name"]
            ent_property_imr = search_osm_tag(ent_property)
            imr_block = ent_property_imr[0]['imr'][0]
            if 'or' in imr_block:
                ent_property_imr = imr_block['or']
            elif 'and' in imr_block:
                ent_property_imr = imr_block['and']
            else:
                raise ValueError(f"Neither 'or' nor 'and' found in IMR block: {imr_block}")

            if 'operator' in node_flt:
                new_ent_operator = node_flt['operator']
                if len(new_ent_operator) == 0:
                    new_ent_operator = '='

                new_ent_value = node_flt["value"]
                if len(ent_property_imr) == 1:
                    ent_property_imr = ent_property_imr[0]
                    ent_property_imr["operator"] = new_ent_operator
                    ent_property_imr["value"] = new_ent_value
                elif any(_ent_prop['value'] in ['***example***'] for _ent_prop in ent_property_imr) or any(_ent_prop['value'] in ['***numeric***'] for _ent_prop in ent_property_imr):
                    new_ent_property_imr = []

                    if 'colour' in ent_property_imr[0]['key'] or 'color' in ent_property_imr[0]['key']:
                        color_values = fetch_color_bundles(new_ent_value)['color_values']
                        for color_value in color_values:
                            for item in ent_property_imr:
                                new_item = item.copy()
                                new_item['operator'] = new_ent_operator
                                new_item['value'] = color_value
                                new_ent_property_imr.append(new_item)
                    else:
                        for item in ent_property_imr:
                            item['operator'] = new_ent_operator
                            item['value'] = new_ent_value
                            new_ent_property_imr.append(item)

                    new_ent_property_imr = {"or": new_ent_property_imr}
                    ent_property_imr = new_ent_property_imr
                else:
                    new_ent_property_imr = {"or": ent_property_imr}
                    ent_property_imr = new_ent_property_imr
            else:
                if isinstance(ent_property_imr, list):
                    new_ent_property_imr = {"or": ent_property_imr}
                    ent_property_imr = new_ent_property_imr

            node_flts.append(ent_property_imr)

        processed_filters = [{"and": node_flts}]

    and_or_in_filters = False
    for processed_filter in processed_filters:
        if "and" in processed_filter:
            and_or_in_filters = True
            continue
        if "or" in processed_filter:
            and_or_in_filters = True
            continue

    if not and_or_in_filters:
        processed_filters = [{"and": processed_filters}]

    print("===processed_filters===")
    print(processed_filters)

    return processed_filters


def adopt_generation(parsed_result):
    """
    Convert a parsed IMR-like structure into the final graph shape used downstream.

    Transformations:
        - Normalize `area` (drop 'value' for bbox).
        - Rename top-level 'entities' to 'nodes', and enrich each node with:
            * filters built by `build_filters`
            * pluralized `display_name` (unless already plural or brand-prefixed)
            * node type: 'nwr' or 'cluster' if `minpoints` is provided
        - Convert 'relations' to 'edges', normalizing type 'dist' -> 'distance'.

    Args:
        parsed_result (dict): Parsed YAML/JSON structure containing at least:
            {
              "area": {"type": "bbox" | "...", ...},
              "entities": [ { "id": int, "name": str, "type": "nwr", ... }, ... ],
              "relations": [ ... ]  # optional
            }

    Returns:
        dict: The transformed result with 'nodes' and optional 'edges'.

    Raises:
        AdoptFuncError: Wraps ValueError/IndexError/KeyError/TypeError with context.
    """
    try:
        area = parsed_result['area']
        if area['type'] == 'bbox':
            if 'value' in area:
                del area['value']

        parsed_result['nodes'] = parsed_result.pop('entities')

        processed_nodes = []
        for node in parsed_result['nodes']:
            if 'name' not in node:
                print(f'{node} has not the required name field!')
                continue
            if not PLURAL_ENGINE.singular_noun(node['name']):
                display_name = PLURAL_ENGINE.plural_noun(node["name"])
            else:
                display_name = node['name']

            if display_name.startswith('brand:'):
                display_name = display_name.replace('brand:', '')

            node_filters = build_filters(node)

            if node_filters:
                if 'minpoints' in node:
                    processed_nodes.append({
                        'id': node['id'],
                        'type': 'cluster',
                        'maxDistance': node['maxdistance'],
                        'minPoints': node['minpoints'],
                        'filters': node_filters,
                        'name': node['name'],
                        'display_name': display_name

                    })
                else:
                    processed_nodes.append({
                        'id': node['id'],
                        'type': 'nwr',
                        'filters': node_filters,
                        'name': node['name'],
                        'display_name': display_name

                    })

        parsed_result['nodes'] = processed_nodes

        if 'relations' in parsed_result:
            rels = parsed_result.pop('relations')
            for rel in rels:
                if rel.get('type') == 'dist':
                    rel['type'] = 'distance'
            parsed_result['edges'] = rels

    except (ValueError, IndexError, KeyError, TypeError) as e:
        raise AdoptFuncError(f"Error in Adopt Generation: {e}")
    return parsed_result