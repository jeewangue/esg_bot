import os
import sys

import streamlit.web.cli as stcli


def resolve_app_path(app_name):
    """
    Resolve the path to the `application` file as an absolute path.
    It assumes that the `application` file is in the same directory as this file.

    Args:
        app_name (str): The name of the application file. E.g. `app.py`

    Returns:
        str: The absolute path to the application file.
    """
    current_file_path = os.path.abspath(__file__)
    resolved_path = os.path.join(os.path.dirname(current_file_path), app_name)
    return resolved_path


def main():
    sys.argv = [
        "streamlit",
        "run",
        resolve_app_path("app.py"),
        "--global.developmentMode=false",
    ]
    sys.exit(stcli.main())
