from enum import Enum


class ItemStatus(Enum):
    exported = 'QLabel {background-color:rgb(216,255,216);color:rgb(40, 40, 40)};'
    missing = 'QLabel {background-color:rgb(255,216,216);color:rgb(40, 40, 40)};'
    export = 'QLabel {background-color:rgb(255,255,216);color:rgb(40, 40, 40)};'
    update = 'QLabel {background-color:rgb(255,216,255);color:rgb(40, 40, 40)};'
    static = 'QLabel {background-color:rgb(216,216,216);color:rgb(40, 40, 40)};'
