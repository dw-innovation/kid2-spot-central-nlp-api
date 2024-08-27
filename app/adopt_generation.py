import inflect
import os
import requests
import sys
from collections.abc import Iterable
from diskcache import Cache
from dotenv import load_dotenv

load_dotenv()
PROJECT_PATH = os.getcwd()
sys.path.append(PROJECT_PATH)

cache = Cache("tmp")
SEARCH_ENDPOINT = os.getenv("SEARCH_ENDPOINT")
PLURAL_ENGINE = inflect.engine()
DEFAULT_DISTANCE = os.getenv("DEFAULT_DISTANCE")

load_dotenv()

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


# @cache.memoize()
def search_osm_tag(entity):
    PARAMS = {"word": entity, "limit": 1, "detail": False}
    r = requests.get(
        url=SEARCH_ENDPOINT, params=PARAMS, verify=False
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
        ent_filters = [
            {
                'or': [
                    {**sub_item, 'value': brand_name if sub_item['value'] == '***example***' else sub_item['value']}
                    for sub_item in item['or']
                ]
            }
            for item in ent_filters
        ]

    additional_att_tag = None

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
                elif any(_ent_prop['key'] in ['brand', 'name'] for _ent_prop in ent_property_imr):
                    new_ent_property_imr = []
                    for item in ent_property_imr:
                        item['operator'] = new_ent_operator
                        item['value'] = new_ent_value
                        new_ent_property_imr.append(item)

                    new_ent_property_imr = {"or": new_ent_property_imr}
                    ent_property_imr = new_ent_property_imr
            else:
                if isinstance(ent_property_imr, list):
                    new_ent_property_imr = {"or": ent_property_imr}
                    ent_property_imr = new_ent_property_imr

            node_flts.append(ent_property_imr)

        processed_filters = [{"and": node_flts}]

    if additional_att_tag:
        processed_filters = [{"and": [processed_filters[0], additional_att_tag]}]

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

    return processed_filters


def adopt_generation(parsed_result):
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

    except (ValueError, IndexError, KeyError, TypeError) as e:
        raise AdoptFuncError(f"Error in Adopt Generation: {e}")
    return parsed_result
