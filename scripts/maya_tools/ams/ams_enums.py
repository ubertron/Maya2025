from enum import Enum


class ResourceStatus(Enum):
    exported = 'QLabel {background-color:rgb(216,255,216);color:rgb(40, 40, 40)};'
    missing = 'QLabel {background-color:rgb(255,216,216);color:rgb(40, 40, 40)};'
    needs_export = 'QLabel {background-color:rgb(255,255,216);color:rgb(40, 40, 40)};'
    needs_update = 'QLabel {background-color:rgb(255,216,255);color:rgb(40, 40, 40)};'
    static = 'QLabel {background-color:rgb(216,216,216);color:rgb(40, 40, 40)};'
