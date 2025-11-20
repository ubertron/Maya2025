from __future__ import annotations

import sys

from collections import Counter


def count_types_recursive(data: dict | list, key_to_count='type') -> Counter:
    """
    Recursively counts the occurrences of values for a specific key
    in all sub-dictionaries.

    Args:
        data (dict or list): The dictionary or list to search within.
        key_to_count (str): The key to count the values of.

    Returns:
        Counter: A Counter object with the counts of each value found.
    """
    counts = Counter()

    if isinstance(data, dict):
        # If the current item is a dictionary, check for the target key
        if key_to_count in data:
            counts[data[key_to_count]] += 1

        # Recursively process all values in the dictionary
        for value in data.values():
            counts.update(count_types_recursive(value, key_to_count))

    elif isinstance(data, list):
        # If the current item is a list, recursively process each item in the list
        for item in data:
            counts.update(count_types_recursive(item, key_to_count))

    return counts


# Example Usage:
nested_data = {
    'item1': {
        'type': 'fruit',
        'name': 'apple',
        'details': {
            'color': 'red',
            'type': 'organic'
        }
    },
    'item2': {
        'type': 'fruit',
        'name': 'banana',
        'origin': 'Ecuador'
    },
    'item3': {
        'type': 'vegetable',
        'name': 'carrot'
    },
    'item4': [
        {'type': 'fruit', 'name': 'grape'},
        {'type': 'vegetable', 'name': 'broccoli'}
    ]
}


def print_paths():
    for path in sys.path:
        print(path)


if __name__ == '__main__':
    # type_counts = count_types_recursive(nested_data, key_to_count='type')
    # print(type_counts)
    print_paths()
