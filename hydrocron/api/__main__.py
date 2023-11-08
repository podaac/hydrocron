"""
Hydrocron API module
"""
# !/usr/bin/env python3


def main():
    """
    Main function to run flask app in port 8080
    """
    from hydrocron.api import hydrocron  # pylint: disable=C0415
    hydrocron.flask_app.run(port=8080)


if __name__ == '__main__':
    main()
