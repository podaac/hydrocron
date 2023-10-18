"""
Hydrocron API module
"""
# !/usr/bin/env python3


def main():
    """
    Main function to run flask app in port 8080
    """
    from hydrocron_api import hydrocron  # noqa: E501 # pylint: disable=import-outside-toplevel
    hydrocron.flask_app.run(port=8080)


if __name__ == '__main__':
    main()
