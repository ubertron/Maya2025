from typing import Callable


def get_lead_docstring_comment(function: Callable, print_result: bool = False) -> str or None:
    """
    Gets the top line of a function docstring
    :param function:
    :param print_result:
    :return:
    """
    docstring = function.__doc__

    if docstring:
        lead_comment = next((line for line in docstring.split('\n') if line), None)

        if lead_comment:
            lead_comment = lead_comment.lstrip()

            if print_result:
                print(lead_comment)

            return lead_comment


if __name__ == '__main__':
    from core import environment_utils

    get_lead_docstring_comment(function=environment_utils.is_using_maya_python, print_result=True)

