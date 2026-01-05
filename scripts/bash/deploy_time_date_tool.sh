#!/bin/bash
# Example deployment script for dockable time_date_tool

PROJECT_ROOT=~/Dropbox/Technology/Python3/Projects/Maya2025

$PROJECT_ROOT/.venv/bin/python3 $PROJECT_ROOT/scripts/maya_tools/utilities/maya_tool_bundler/maya_tool_bundler.py \
  $PROJECT_ROOT/scripts/maya_tools/utilities/time_date_tool.py \
  --output-dir $PROJECT_ROOT/plug-ins \
  --scripts-root $PROJECT_ROOT/scripts \
  --name TimeDateTool \
  --icon $PROJECT_ROOT/images/icons/time.png \
  --shelf "Robotools" \
  --menu "Robotools" \
  --launch "maya_tools.utilities.time_date_tool.TimeDateTool().show()" \
  --dockable