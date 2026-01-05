#!/bin/bash
# Deployment script for Boxy tool (module-based)

PROJECT_ROOT=~/Dropbox/Technology/Python3/Projects/Maya2025

# Note: For module-based tools where UI_SCRIPT is in __init__.py,
# we need to ensure the launch command can access it from the parent module.
# The launch command creates the tool from boxy_tool, but UI_SCRIPT lives in boxy/__init__.py

$PROJECT_ROOT/.venv/bin/python3 $PROJECT_ROOT/scripts/maya_tools/utilities/maya_tool_bundler/maya_tool_bundler.py \
  $PROJECT_ROOT/scripts/maya_tools/utilities/boxy/boxy_tool.py \
  --output-dir $PROJECT_ROOT/plug-ins \
  --scripts-root $PROJECT_ROOT/scripts \
  --name BoxyTool \
  --icon $PROJECT_ROOT/images/icons/boxy.png \
  --shelf "Robotools" \
  --menu "Robotools" \
  --launch "maya_tools.utilities.boxy.boxy_tool.BoxyTool().show()" \
  --dockable
