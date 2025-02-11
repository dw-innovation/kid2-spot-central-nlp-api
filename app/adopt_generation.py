import inflect
import os
import requests
import sys
from collections.abc import Iterable
from dotenv import load_dotenv
from functools import lru_cache

load_dotenv()
PROJECT_PATH = os.getcwd()
sys.path.append(PROJECT_PATH)

SEARCH_ENDPOINT = os.getenv("SEARCH_ENDPOINT")
COLOR_BUNDLE_SEARCH = os.getenv("COLOR_BUNDLE_SEARCH")
PLURAL_ENGINE = inflect.engine()
DEFAULT_DISTANCE = os.getenv("DEFAULT_DISTANCE")

def flatten(xs):
    for x in xs:
        if isinstance(x, Iterable) and not isinstance(x, (str, bytes)):
            yield from flatten(x)
        else:
            yield x


def is_nested_list(l):
    try:
        next(x for x in l if isinstance(x, list))

    except StopIteration:
        return False

    return True


class AdoptFuncError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


@lru_cache(maxsize=None)
def search_osm_tag(entity):
    PARAMS = {"word": entity, "limit": 1, "detail": False}
    r = requests.get(
        url=SEARCH_ENDPOINT, params=PARAMS, verify=False
    )  # set verify to False to ignore SSL certificate
    return r.json()

def fetch_color_bundles(color:str):
    PARAMS = {"color": color, "limit": 1, "detail": False}
    r = requests.get(
        url=COLOR_BUNDLE_SEARCH, params=PARAMS, verify=False
    )  # set verify to False to ignore SSL certificate
    return r.json()

def build_filters(node):
    node_name = node["name"]

    osm_results = search_osm_tag(node_name)
    if len(osm_results) == 0:
        return None
    ent_filters = osm_results[0]["imr"]

    if node_name.startswith('brand:'):
        brand_name = node_name.replace('brand:', '')

        for item in ent_filters:
            for sub_item in item['or']:
                if sub_item['value'] == '***example***':
                    sub_item['value'] = brand_name
        ent_filters = [
            {'or': item['or']} for item in ent_filters
        ]

    processed_filters = ent_filters[0] if ent_filters and is_nested_list(ent_filters) else ent_filters

    if "properties" in node:
        node_flts = [processed_filters[0]]

        for node_flt in node["properties"]:
            ent_property = node_flt["name"]
            ent_property_imr = search_osm_tag(ent_property)

            ent_property_imr = ent_property_imr[0]['imr'][0]['or']

            if 'operator' in node_flt:
                new_ent_operator = node_flt['operator']
                if len(new_ent_operator) == 0:
                    new_ent_operator = '='

                new_ent_value = node_flt["value"]
                if len(ent_property_imr) == 1:
                    ent_property_imr = ent_property_imr[0]
                    ent_property_imr["operator"] = new_ent_operator
                    ent_property_imr["value"] = new_ent_value
                elif any(_ent_prop['key'] in ['brand', 'name', 'colour'] for _ent_prop in ent_property_imr):
                    if ent_property_imr and 'colour' in ent_property_imr[0].get('key', ''):
                        new_ent_property_imr = handle_color_filter(ent_property_imr, new_ent_operator, new_ent_value)
                    else:
                        new_ent_property_imr = [
                            {**item, 'operator': new_ent_operator, 'value': new_ent_value} for item in ent_property_imr
                        ]

                    ent_property_imr = {"or": new_ent_property_imr}
            else:
                if isinstance(ent_property_imr, list):
                    new_ent_property_imr = {"or": ent_property_imr}
                    ent_property_imr = new_ent_property_imr

            node_flts.append(ent_property_imr)

        processed_filters = [{"and": node_flts}]

    if not any(key in processed_filters[0] for key in ["and", "or"]):
        processed_filters = [{"and": processed_filters}]

    return processed_filters


def handle_color_filter(ent_property_imr, new_ent_operator, new_ent_value):
    color_values = fetch_color_bundles(new_ent_value)['color_values']
    new_ent_property_imr = []

    for color_value in color_values:
        for item in ent_property_imr:
            new_item = item.copy()
            new_item['operator'] = new_ent_operator
            new_item['value'] = color_value
            new_ent_property_imr.append(new_item)

    return new_ent_property_imr


def adopt_generation(parsed_result):
    try:
        area = parsed_result.get('area', {})
        if area['type'] == 'bbox':
            if area.get('type') == 'bbox':
                area.pop('value', None)

        parsed_result['nodes'] = parsed_result.pop('entities', [])

        processed_nodes = []
        for node in parsed_result['nodes']:
            name = node.get('name')
            if not name:
                print(f'{node} has not the required name field!')
                continue

            display_name = (
                PLURAL_ENGINE.plural_noun(name)
                if not PLURAL_ENGINE.singular_noun(name)
                else name
            )

            display_name = display_name.replace('brand:', '') if display_name.startswith('brand:') else display_name

            node_filters = build_filters(node)

            if node_filters:
                processed_nodes.append({
                    'id': node['id'],
                    'type': 'nwr',
                    'filters': node_filters,
                    'name': node['name'],
                    'display_name': display_name

                })

        parsed_result['nodes'] = processed_nodes

        if 'relations' in parsed_result:
            parsed_result['edges'] = parsed_result.pop('relations')

    except (KeyError, TypeError) as e:
        raise AdoptFuncError(f"Error in Adopt Generation: {e}")

    return parsed_result
