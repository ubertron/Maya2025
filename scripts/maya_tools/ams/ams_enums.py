from enum import Enum


class StatusStyle(Enum):
    exported = 'QLabel {background-color:rgb(216,255,216);color:rgb(40, 40, 40)};'
    needs_export = 'QLabel {background-color:rgb(255,216,216);color:rgb(40, 40, 40)};'
