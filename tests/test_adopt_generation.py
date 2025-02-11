import unittest

from app.adopt_generation import build_filters, adopt_generation

'''
Execute python -m unittest tests.test_adopt_generation
'''


class TestAdoptFunction(unittest.TestCase):

    def test_property_wo_operator(self):
        node = {'id': 2, 'name': 'restaurant', 'properties': [{'name': 'outdoor seating'}], 'type': 'nwr'}
        result = build_filters(node)
        expected_output = [
            {
                "and": [
                    {
                        "or": [
                            {"key": "amenity", "operator": "=", "value": "restaurant"},
                            {"key": "amenity", "operator": "=", "value": "food_court"},
                            {"key": "amenity", "operator": "=", "value": "fast_food"}
                        ]
                    },
                    {
                        "or": [
                            {"key": "leisure", "operator": "=", "value": "outdoor_seating"},
                            {"key": "outdoor_seating", "operator": "=", "value": "yes"}
                        ]
                    }
                ]
            }
        ]

        self.assertEqual(result, expected_output)

    def test_brand_entity(self):
        node = {'id': 1, 'name': 'brand:h&m', 'type': 'nwr'}
        result = build_filters(node)
        expected_output = [{'or': [{'key': 'name', 'operator': '~', 'value': 'h&m'},
                                   {'key': 'brand', 'operator': '~', 'value': 'h&m'},
                                   {'key': 'short_name', 'operator': '~', 'value': 'h&m'},
                                   {'key': 'name:en', 'operator': '~', 'value': 'h&m'},
                                   {'key': 'int_name', 'operator': '~', 'value': 'h&m'},
                                   {'key': 'official_name', 'operator': '~', 'value': 'h&m'},
                                   ]}]
        self.assertEqual(result, expected_output)


    def test_adopt_pipeline(self):
        parsed_result = {'area': {'type': 'bbox'}, 'entities': [{'id': 0, 'name': 'supermarket', 'properties': [{'name': 'height', 'operator': '>', 'value': 10}, {'name': 'roof material', 'operator': '=', 'value': 'red'}], 'type': 'nwr'}]}
        result = adopt_generation(parsed_result)
        expected_output = {'area': {'type': 'bbox'}, 'nodes': [{'id': 0, 'type': 'nwr', 'filters': [{'and': [{'or': [{'key': 'shop', 'operator': '=', 'value': 'supermarket'}, {'key': 'building', 'operator': '=', 'value': 'supermarket'}, {'key': 'shop', 'operator': '=', 'value': 'discounter'}, {'key': 'shop', 'operator': '=', 'value': 'wholesale'}]}, {'key': 'height', 'operator': '>', 'value': 10}, {'key': 'roof:material', 'operator': '=', 'value': 'red'}]}], 'name': 'supermarket', 'display_name': 'supermarkets'}]}
        self.assertEqual(result, expected_output)


    def test_color_property(self):
        node = {'id': 2, 'name': 'restaurant', 'properties': [{'name': 'color', 'operator':'=', 'value': 'brown'}], 'type': 'nwr'}
        result = build_filters(node)
        expected_output = [
            {
                "and": [
                    {
                        "or": [
                            {"key": "amenity", "operator": "=", "value": "restaurant"},
                            {"key": "amenity", "operator": "=", "value": "food_court"},
                            {"key": "amenity", "operator": "=", "value": "fast_food"}
                        ]
                    },
                    {
                        "or": [
                            {"key": "colour", "operator": "=", "value": "brown"},
                            {"key": "building:colour", "operator": "=", "value": "brown"},
                            {"key": "roof:colour", "operator": "=", "value": "brown"},
                            {"key": "colour", "operator": "=", "value": "tan"},
                            {"key": "building:colour", "operator": "=", "value": "tan"},
                            {"key": "roof:colour", "operator": "=", "value": "tan"},
                            {"key": "colour", "operator": "=", "value": "#a1634f"},
                            {"key": "building:colour", "operator": "=", "value": "#a1634f"},
                            {"key": "roof:colour", "operator": "=", "value": "#a1634f"},
                            {"key": "colour", "operator": "=", "value": "#85552E"},
                            {"key": "building:colour", "operator": "=", "value": "#85552E"},
                            {"key": "roof:colour", "operator": "=", "value": "#85552E"},
                            {"key": "colour", "operator": "=", "value": "#9c7870"},
                            {"key": "building:colour", "operator": "=", "value": "#9c7870"},
                            {"key": "roof:colour", "operator": "=", "value": "#9c7870"},
                            {"key": "colour", "operator": "=", "value": "#be8988"},
                            {"key": "building:colour", "operator": "=", "value": "#be8988"},
                            {"key": "roof:colour", "operator": "=", "value": "#be8988"},
                            {"key": "colour", "operator": "=", "value": "#c75d4d"},
                            {"key": "building:colour", "operator": "=", "value": "#c75d4d"},
                            {"key": "roof:colour", "operator": "=", "value": "#c75d4d"},
                        ]
                    }
                ]
            }
        ]

        self.assertEqual(result, expected_output)

    def test_cuisine(self):
        node = {'id': 0, 'name': 'restaurant', 'properties': [{'name': 'cuisine', 'operator': '=', 'value': 'italian'}], 'type': 'nwr'}
        result = build_filters(node)
        expected_output = [{'and': [{'or': [{'key': 'amenity', 'operator': '=', 'value': 'restaurant'}, {'key': 'amenity', 'operator': '=', 'value': 'food_court'}, {'key': 'amenity', 'operator': '=', 'value': 'fast_food'}]}, {'key': 'cuisine', 'operator': '=', 'value': 'italian'}]}]
        self.assertEqual(result, expected_output)

if __name__ == '__main__':
    unittest.main()
