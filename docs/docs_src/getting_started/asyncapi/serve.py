"""
This file contains `faststream docs` commands.
These commands are referenced in guide file.
These commands are also imported and used in tests under tests/ directory.
"""


gen_json_cmd = """
faststream docs gen basic:app
"""

gen_yaml_cmd = """
faststream docs gen --yaml basic:app
"""

serve_cmd = """
faststream docs serve basic:app
"""

serve_json_cmd = """
faststream docs serve asyncapi.json
"""

serve_yaml_cmd = """
faststream docs serve asyncapi.yaml
"""
