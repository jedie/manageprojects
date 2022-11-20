"""
    Allow manageprojects to be executable
    through `python -m manageprojects`.
"""


from manageprojects.cli import cli_app


def main():
    cli_app.main()


if __name__ == '__main__':
    main()
