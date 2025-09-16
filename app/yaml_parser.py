import yaml

SCHEMA = {
    'type': 'object',
    'properties': {
        'area': {
            'type': 'object',
            'properties': {
                'name': {'type': 'string'},
                'type': {'type': 'string'},
            },
            'required': ['name', 'type']
        }
    },
    'required': ['area']
}


def validate_and_fix_yaml(yaml_text):
    """
    Attempts to safely parse a YAML string, and recursively correct common formatting
    issues if parsing fails.

    This is primarily used for model-generated YAML that may contain small errors
    such as:
      - invalid tokens (e.g. `</s>`)
      - missing quotes around values
      - malformed lists or dicts
      - improperly indented or split keys like 'id'

    Args:
        yaml_text (str): The raw YAML string output to be parsed and validated.

    Returns:
        dict: Parsed and corrected YAML content as a Python dictionary.

    Notes:
        - If parsing fails due to common known issues, the function attempts to correct
          them and recursively calls itself.
        - If parsing fails irrecoverably, the function may return `None` or raise an error,
          depending on the failure point.

    Examples:
        >>> validate_and_fix_yaml("area:\n  name: Bonn\n  type: city")
        {'area': {'name': 'Bonn', 'type': 'city'}}
    """
    yaml_text = yaml_text.replace('</s>', '')
    try:
        result = yaml.safe_load(yaml_text)
        # validate(instance=result, schema=SCHEMA)
        return result
    except yaml.parser.ParserError as e:
        print(f"fixing error: {e}")
        line_num = e.problem_mark.line
        # column_num = e.problem_mark.column
        lines = yaml_text.split('\n')

        misformatted_line = lines[line_num]
        if "entities" or "relations" in lines[line_num]:
            corrected_line = misformatted_line.strip()
            yaml_text = yaml_text.replace(misformatted_line, corrected_line)
            return validate_and_fix_yaml(yaml_text)
    except yaml.composer.ComposerError as e:
        print(f"fixing error: {e}")
        line_num = e.problem_mark.line
        # column_num = e.problem_mark.column
        lines = yaml_text.split('\n')

        if "value" in lines[line_num]:
            tag = lines[line_num].split(":")
            tag_value = tag[1].strip()
            fixed_tag_value = "\"" + tag_value + "\""
            yaml_text = yaml_text.replace(tag_value, fixed_tag_value)
            return validate_and_fix_yaml(yaml_text)

    except yaml.scanner.ScannerError as e:
        print(f"fixing error: {e}")
        line_num = e.problem_mark.line

        # column_num = e.problem_mark.column
        lines = yaml_text.split('\n')

        misformatted_line = lines[line_num]
        if "value" and "id" in lines[line_num]:
            corrected_line = misformatted_line.replace("id:", "\n id:")
            yaml_text = yaml_text.replace(misformatted_line, corrected_line)
            return validate_and_fix_yaml(yaml_text)



