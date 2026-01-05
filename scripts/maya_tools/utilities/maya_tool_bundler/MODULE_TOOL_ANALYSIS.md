# Module-Based Tool Deployment

## Boxy Tool Structure

```
boxy/
├── __init__.py          # Contains: UI_SCRIPT = "from maya_tools.utilities.boxy import boxy_tool; boxy_tool.BoxyTool().restore()"
├── boxy.py              # Backend logic
└── boxy_tool.py         # UI (BoxyTool class inherits from GenericWidget)
```

## How the Bundler Handles This:

### 1. Dependency Analysis
Starting from `boxy_tool.py`, the bundler will:
- Find the import: `from maya_tools.utilities.boxy import boxy`
- Resolve this to `boxy.py` in the same directory
- Find the import in `boxy_tool.py` (if any references to `__init__.py`)
- Copy all three files maintaining the directory structure

### 2. Launch Command Transformation
Given: `--launch "maya_tools.utilities.boxy.boxy_tool.BoxyTool().show()"`

With `--dockable` flag:
- Extracts module: `maya_tools.utilities.boxy.boxy_tool`
- Replaces `.show()` with `.show_workspace_control()`
- Adds `ui_script` parameter using the module's UI_SCRIPT

### 3. Generated Plugin Code
```python
def doIt(self, args):
    """Execute the command."""
    try:
        _setup_plugin_path()
        import maya_tools.utilities.boxy.boxy_tool
        maya_tools.utilities.boxy.boxy_tool.BoxyTool().show_workspace_control(
            ui_script=maya_tools.utilities.boxy.boxy_tool.UI_SCRIPT
        )
    except Exception as e:
        cmds.error(f"BoxyTool error: {e}")
```

### 4. Directory Structure After Bundling
```
plug-ins/BoxyTool/
├── BoxyTool.py                    # Plugin file
├── scripts/
│   └── maya_tools/
│       └── utilities/
│           └── boxy/
│               ├── __init__.py    # Contains UI_SCRIPT
│               ├── boxy.py
│               └── boxy_tool.py
├── icons/
│   └── boxy.png
└── README.md
```

## Key Points:

1. **UI_SCRIPT Location**: For module-based tools, the UI_SCRIPT is in `__init__.py`, but the bundler accesses it as:
   ```python
   maya_tools.utilities.boxy.boxy_tool.UI_SCRIPT
   ```
   
   Wait - this is WRONG! The UI_SCRIPT is in `__init__.py`, so it should be:
   ```python
   maya_tools.utilities.boxy.UI_SCRIPT
   ```

2. **Import Path**: The module path in the launch command should match where UI_SCRIPT lives.

## ISSUE IDENTIFIED:
The current bundler logic extracts the module path from the launch command by removing everything after the last `.` before the method call. This works for single-file tools but may not work correctly for module-based tools where UI_SCRIPT is in `__init__.py`.

For `maya_tools.utilities.boxy.boxy_tool.BoxyTool().show()`:
- Current extraction: `maya_tools.utilities.boxy.boxy_tool`
- UI_SCRIPT location: `maya_tools.utilities.boxy.UI_SCRIPT` (in __init__.py)

The bundler needs to handle both cases!
