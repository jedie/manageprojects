"""
    Allow manageprojects CLI to be executable through `python -m manageprojects`.
"""
from manageprojects.cli import cli

if __name__ == "__main__":
    cli()
