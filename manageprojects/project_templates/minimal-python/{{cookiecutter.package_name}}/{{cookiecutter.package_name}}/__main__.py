"""
    Allow {{ cookiecutter.package_name }} to be executable
    through `python -m {{ cookiecutter.package_name }}`.
"""


def hello_world():
    print('Hello World from {{ cookiecutter.package_name }}')


if __name__ == "__main__":
    hello_world()
