"""
Maya Tool Bundler
Analyzes a PySide Maya tool, finds dependencies, and creates a portable plugin package.
"""

import os
import sys
import ast
import shutil
import json
from pathlib import Path
from typing import Set, List, Dict

# Bundler version
BUNDLER_VERSION = "1.2.6"


class DependencyAnalyzer:
    """Analyzes Python files to find all import dependencies."""

    def __init__(self, root_file: str, exclude_stdlib: bool = True, search_paths: List[Path] = None):
        self.root_file = Path(root_file).resolve()
        self.root_dir = self.root_file.parent
        self.exclude_stdlib = exclude_stdlib
        self.dependencies: Set[Path] = set()
        self.stdlib_modules = self._get_stdlib_modules()

        # Additional search paths for resolving imports
        self.search_paths = [self.root_dir]
        if search_paths:
            self.search_paths.extend([Path(p) for p in search_paths])

        # Try to find project root by looking for common markers
        self._find_project_root()

    def _get_stdlib_modules(self) -> Set[str]:
        """Get standard library module names."""
        return set(sys.stdlib_module_names) if hasattr(sys, 'stdlib_module_names') else set()

    def _find_project_root(self) -> None:
        """Try to find the project root directory by looking for common markers."""
        current = self.root_dir

        # Look up the directory tree for project markers
        for _ in range(10):  # Limit search depth
            # Check for common project markers
            if any((current / marker).exists() for marker in ['.git', '.venv', 'scripts', 'src']):
                self.search_paths.insert(0, current)
                # Also add common subdirectories
                for subdir in ['scripts', 'src', 'lib']:
                    subdir_path = current / subdir
                    if subdir_path.exists():
                        self.search_paths.append(subdir_path)
                break

            parent = current.parent
            if parent == current:  # Reached root
                break
            current = parent

    def _is_local_import(self, module_name: str) -> bool:
        """Check if import is a local module (not stdlib or maya/PySide)."""
        if not module_name:
            return False

        base = module_name.split('.')[0]

        # Exclude Maya and PySide modules (available in Maya)
        if base in ['maya', 'PySide2', 'PySide6', 'shiboken2', 'shiboken6']:
            return False

        # Exclude stdlib
        if self.exclude_stdlib and base in self.stdlib_modules:
            return False

        return True

    def _resolve_import_path(self, module_name: str, current_file: Path) -> Path:
        """Resolve a module name to a file path."""
        parts = module_name.split('.')

        # Try all search paths
        for search_path in self.search_paths:
            for i in range(len(parts), 0, -1):
                path_parts = parts[:i]
                potential_file = search_path / '/'.join(path_parts)

                if potential_file.with_suffix('.py').exists():
                    return potential_file.with_suffix('.py')
                if (potential_file / '__init__.py').exists():
                    return potential_file / '__init__.py'

        return None

    def _analyze_file(self, file_path: Path, visited: Set[Path]) -> None:
        """Recursively analyze a Python file for imports."""
        if file_path in visited or not file_path.exists():
            return

        visited.add(file_path)
        self.dependencies.add(file_path)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=str(file_path))
        except Exception as e:
            print(f"Warning: Could not parse {file_path}: {e}")
            return

        for node in ast.walk(tree):
            module_names = []

            if isinstance(node, ast.Import):
                module_names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module_names = [node.module]
                # Handle relative imports
                if node.level > 0:
                    parent = file_path.parent
                    for _ in range(node.level - 1):
                        parent = parent.parent
                    if node.module:
                        rel_path = parent / node.module.replace('.', '/')
                    else:
                        rel_path = parent

                    if rel_path.with_suffix('.py').exists():
                        self._analyze_file(rel_path.with_suffix('.py'), visited)
                    elif (rel_path / '__init__.py').exists():
                        self._analyze_file(rel_path / '__init__.py', visited)

            for module_name in module_names:
                if self._is_local_import(module_name):
                    dep_path = self._resolve_import_path(module_name, file_path)
                    if dep_path:
                        self._analyze_file(dep_path, visited)

    def analyze(self) -> Set[Path]:
        """Analyze the root file and return all dependencies."""
        visited = set()
        self._analyze_file(self.root_file, visited)
        return self.dependencies


class MayaToolBundler:
    """Bundles a Maya tool with all dependencies into a portable plugin."""

    def __init__(self, root_file: Path, output_dir: Path, plugin_name: str = None,
                 launch_command: str = None, scripts_root: Path = None, dockable: bool = False):
        self.root_file = root_file.resolve()
        self.output_dir = output_dir.resolve()
        self.plugin_name = plugin_name or self.root_file.stem
        self.plugin_dir = self.output_dir / self.plugin_name
        self.launch_command = launch_command
        self.scripts_root = scripts_root
        self.dockable = dockable

    def _get_timestamp(self) -> str:
        """Get current timestamp for plugin generation."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def bundle(self, icon_path: str = None, menu_parent: str = None,
               shelf_name: str = None) -> Dict[str, str]:
        """Bundle the tool and create all necessary files.

        Args:
            icon_path: Path to icon file
            menu_parent: Parent menu name to add tool to (e.g., "MayaWindow|mainRigMenu")
            shelf_name: Shelf name to add button to (e.g., "Custom")
        """
        print(f"Analyzing dependencies for {self.root_file}...")

        # Clean up existing plugin directory if it exists
        if self.plugin_dir.exists():
            print(f"Removing existing plugin directory: {self.plugin_dir}")
            shutil.rmtree(self.plugin_dir)

        # Set up search paths
        search_paths = []
        if self.scripts_root:
            search_paths.append(self.scripts_root.resolve())

        analyzer = DependencyAnalyzer(str(self.root_file), search_paths=search_paths)
        dependencies = analyzer.analyze()

        print(f"Found {len(dependencies)} files to copy")

        # Create output directory structure
        self.plugin_dir.mkdir(parents=True, exist_ok=True)
        source_dir = self.plugin_dir / 'scripts'
        source_dir.mkdir(exist_ok=True)

        # Copy all dependencies maintaining structure
        # Use scripts_root as base if provided, otherwise find common base
        if self.scripts_root:
            common_base = self.scripts_root.resolve()
        else:
            root_dir = self.root_file.parent
            common_base = None
            for dep in dependencies:
                for search_path in analyzer.search_paths:
                    try:
                        dep.relative_to(search_path)
                        if common_base is None or len(str(search_path)) > len(str(common_base)):
                            common_base = search_path
                        break
                    except ValueError:
                        continue

            if common_base is None:
                common_base = root_dir

        print(f"Using base path: {common_base}")

        for dep in dependencies:
            try:
                rel_path = dep.relative_to(common_base)
            except ValueError:
                # If not relative to common base, use filename only
                rel_path = dep.name

            dest = source_dir / rel_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(dep, dest)
            print(f"Copied: {rel_path}")

        # Copy icon if provided
        icon_filename = None
        if icon_path:
            icon_path_obj = Path(icon_path)

            # Validate icon exists
            if not icon_path_obj.exists():
                raise FileNotFoundError(f"Icon file not found: {icon_path}")

            # Validate icon file extension
            valid_extensions = {'.png', '.svg', '.jpg', '.jpeg', '.bmp', '.xpm', '.ico'}
            if icon_path_obj.suffix.lower() not in valid_extensions:
                raise ValueError(f"Invalid icon format: {icon_path_obj.suffix}. Must be one of: {', '.join(valid_extensions)}")

            # Copy icon
            icon_dest = self.plugin_dir / 'icons' / icon_path_obj.name
            icon_dest.parent.mkdir(exist_ok=True)
            shutil.copy2(icon_path_obj, icon_dest)
            icon_filename = icon_path_obj.name
            print(f"Copied icon: {icon_path}")

        # Create plugin file
        plugin_file = self._create_plugin_file(menu_parent, shelf_name, icon_filename)

        # Create launch scripts
        result = {'plugin_dir': str(self.plugin_dir), 'plugin_file': plugin_file}

        if shelf_name:
            shelf_script = self._create_shelf_script(shelf_name, icon_filename)
            result['shelf_script'] = shelf_script

        if menu_parent:
            menu_script = self._create_menu_script(menu_parent)
            result['menu_script'] = menu_script

        # Create README
        readme_path = self._create_readme(icon_filename, menu_parent, shelf_name)
        result['readme'] = readme_path

        print(f"\n✓ Plugin bundled successfully!")
        print(f"  Plugin file: {self.output_dir / f'{self.plugin_name}.py'}")
        print(f"  Support files: {self.plugin_dir}")

        return result

    def _create_plugin_file(self, menu_parent: str = None, shelf_name: str = None, icon_filename: str = None) -> str:
        """Create the Maya plugin .py file."""
        # Create plugin file in parent directory (output_dir) instead of plugin_dir
        # This makes it visible to Maya's Plugin Manager at the top level
        plugin_file = self.output_dir / f'{self.plugin_name}.py'

        main_module = self.root_file.stem

        # Determine launch command
        if self.launch_command:
            # Extract module path from launch command for import
            # e.g., "maya_tools.utilities.time_date_tool.TimeDateTool().show()"
            # -> import maya_tools.utilities.time_date_tool
            import_match = self.launch_command.split('(')[0].rsplit('.', 1)[0]

            if self.dockable:
                # For dockable widgets, modify the command to use show_workspace_control
                # e.g., "maya_tools.utilities.time_date_tool.TimeDateTool().show()"
                # -> "maya_tools.utilities.time_date_tool.TimeDateTool().show_workspace_control(ui_script=maya_tools.utilities.time_date_tool.UI_SCRIPT)"
                # For module-based tools, UI_SCRIPT may be in parent module's __init__.py
                base_command = self.launch_command.replace('.show()', '')
                parent_module = '.'.join(import_match.split('.')[:-1]) if '.' in import_match else import_match

                launch_code = f'''            _setup_plugin_path()
            import {import_match}
            # Try to get UI_SCRIPT from module or parent module (for module-based tools)
            ui_script_module = {import_match} if hasattr({import_match}, 'UI_SCRIPT') else None
            if ui_script_module is None and '{parent_module}':
                import {parent_module}
                ui_script_module = {parent_module} if hasattr({parent_module}, 'UI_SCRIPT') else None
            if ui_script_module:
                {base_command}.show_workspace_control(ui_script=ui_script_module.UI_SCRIPT)
            else:
                cmds.warning("{self.plugin_name}: UI_SCRIPT not found in module or parent module")'''
            else:
                launch_code = f"            _setup_plugin_path()\n            import {import_match}\n            {self.launch_command}"
        else:
            if self.dockable:
                launch_code = f'''            _setup_plugin_path()
            import {main_module}
            # Launch as dockable workspace control
            if hasattr({main_module}, 'UI_SCRIPT'):
                widget = {main_module}.{self.plugin_name}()
                widget.show_workspace_control(ui_script={main_module}.UI_SCRIPT)
            else:
                cmds.warning("{self.plugin_name}: UI_SCRIPT not found for dockable widget")'''
            else:
                launch_code = f'''            _setup_plugin_path()
            import {main_module}
            # Check if main() or show() function exists
            if hasattr({main_module}, 'main'):
                {main_module}.main()
            elif hasattr({main_module}, 'show'):
                {main_module}.show()
            else:
                cmds.warning("{self.plugin_name}: No main() or show() function found")'''

        # Menu creation code
        menu_code = ""
        menu_uninit = ""
        if menu_parent:
            menu_code = f'''

def create_menu():
    """Create menu item for the tool."""
    menu_parent = "{menu_parent}"
    menu_label = "{self.plugin_name}"
    
    # Create menu parent if it doesn't exist
    if not cmds.menu(menu_parent, exists=True):
        # Get the main Maya window
        main_window = mel.eval('$temp = $gMainWindow')
        
        # Create the menu
        cmds.menu(
            menu_parent,
            parent=main_window,
            label=menu_parent,
            tearOff=True
        )
        print(f"Created menu: '{menu_parent}'")
    
    # Remove old menu item if it exists
    menu_items = cmds.menu(menu_parent, query=True, itemArray=True) or []
    for item in menu_items:
        label = cmds.menuItem(item, query=True, label=True)
        if label == menu_label:
            cmds.deleteUI(item, menuItem=True)
    
    # Create new menu item
    cmds.menuItem(
        parent=menu_parent,
        label=menu_label,
        command='import maya.cmds as cmds; cmds.{self.plugin_name}()'
    )
    print(f"Menu item '{{menu_label}}' added to '{{menu_parent}}'")


def remove_menu():
    """Remove menu item for the tool."""
    menu_parent = "{menu_parent}"
    menu_label = "{self.plugin_name}"
    
    if not cmds.menu(menu_parent, exists=True):
        return
    
    # Remove menu item
    menu_items = cmds.menu(menu_parent, query=True, itemArray=True) or []
    for item in menu_items:
        label = cmds.menuItem(item, query=True, label=True)
        if label == menu_label:
            cmds.deleteUI(item, menuItem=True)
            print(f"Menu item '{{menu_label}}' removed from '{{menu_parent}}'")
            break
    
    # Check if menu is now empty and delete it if so
    remaining_items = cmds.menu(menu_parent, query=True, itemArray=True) or []
    if not remaining_items:
        cmds.deleteUI(menu_parent, menu=True)
        print(f"Menu '{{menu_parent}}' was empty and has been removed")
'''
            menu_uninit = "remove_menu()"

        # Shelf creation code
        shelf_code = ""
        shelf_uninit = ""
        if shelf_name:
            icon_for_shelf = icon_filename or "commandButton.png"
            shelf_code = f'''

def create_shelf_button():
    """Create shelf button for the tool."""
    shelf_name = "{shelf_name}"
    tool_label = "{self.plugin_name}"
    # Find icon path relative to this plugin file
    # Plugin file is at: plug-ins/PluginName.py
    # Icons are at: plug-ins/PluginName/icons/
    icon_name = "{icon_for_shelf}"
    
    # Get the directory where this plugin file lives
    plugins = cmds.pluginInfo(query=True, listPlugins=True) or []
    plugin_base_dir = None
    for plugin_name in plugins:
        if plugin_name.startswith("{self.plugin_name}"):
            plugin_file = cmds.pluginInfo(plugin_name, query=True, path=True)
            plugin_base_dir = os.path.dirname(plugin_file)
            break
    
    if plugin_base_dir:
        icon_path = os.path.join(plugin_base_dir, "{self.plugin_name}", "icons", icon_name)
    else:
        icon_path = icon_name
    
    # Create shelf if it doesn't exist
    if not cmds.shelfLayout(shelf_name, exists=True):
        print(f"Shelf '{{shelf_name}}' does not exist. Creating it...")
        mel.eval(f'addNewShelfTab("{{shelf_name}}")')
    
    # Remove existing button if it exists
    buttons = cmds.shelfLayout(shelf_name, query=True, childArray=True) or []
    for button in buttons:
        try:
            if cmds.objectTypeUI(button) == 'shelfButton':
                label = cmds.shelfButton(button, query=True, label=True)
                if label == tool_label:
                    cmds.deleteUI(button)
        except:
            continue
    
    # Use icon if it exists, otherwise use default
    if os.path.exists(icon_path):
        icon = icon_path
    else:
        icon = icon_name
    
    # Create shelf button
    cmds.shelfButton(
        parent=shelf_name,
        label=tool_label,
        annotation=f"Launch {{tool_label}}",
        image=icon,
        command="import maya.cmds as cmds; cmds.{self.plugin_name}()",
        sourceType="python"
    )
    print(f"Shelf button '{{tool_label}}' added to '{{shelf_name}}' shelf")


def remove_shelf_button():
    """Remove shelf button for the tool."""
    shelf_name = "{shelf_name}"
    tool_label = "{self.plugin_name}"
    
    if not cmds.shelfLayout(shelf_name, exists=True):
        return
    
    # Get all buttons on the shelf
    buttons = cmds.shelfLayout(shelf_name, query=True, childArray=True) or []
    
    for button in buttons:
        try:
            # Check if this is a shelfButton and matches our label
            if cmds.objectTypeUI(button) == 'shelfButton':
                label = cmds.shelfButton(button, query=True, label=True)
                if label == tool_label:
                    cmds.deleteUI(button)
                    print(f"Shelf button '{{tool_label}}' removed from '{{shelf_name}}' shelf")
                    break
        except:
            continue
    
    # Check if shelf is now empty and delete it if so
    remaining_buttons = cmds.shelfLayout(shelf_name, query=True, childArray=True) or []
    if not remaining_buttons:
        # Get the shelf's parent (the tab layout)
        shelf_parent = mel.eval('$temp = $gShelfTopLevel')
        cmds.deleteUI(shelf_name, layout=True)
        print(f"Shelf '{{shelf_name}}' was empty and has been removed")
'''
            shelf_uninit = "remove_shelf_button()"

        content = f'''"""
{self.plugin_name} - Maya Plugin
Auto-generated plugin file for Maya Plug-in Manager

Generated by: Maya Tool Bundler v{BUNDLER_VERSION}
Generated on: {self._get_timestamp()}
"""

import sys
import os
from maya.api import OpenMaya
from maya import cmds, mel

# Add scripts directory to path
# Note: __file__ is not available in Maya plugin context, so we get the path from the plugin object
_plugin_path = None

def _setup_plugin_path():
    """Setup the plugin path when the plugin is initialized."""
    global _plugin_path
    if _plugin_path is None:
        # Get all loaded plugins
        plugins = cmds.pluginInfo(query=True, listPlugins=True) or []
        for plugin_name in plugins:
            if plugin_name.startswith("{self.plugin_name}"):
                plugin_file = cmds.pluginInfo(plugin_name, query=True, path=True)
                plugin_dir = os.path.dirname(plugin_file)
                # Scripts are in a subdirectory named after the plugin
                _plugin_path = os.path.join(plugin_dir, "{self.plugin_name}")
                scripts_path = os.path.join(_plugin_path, 'scripts')
                if scripts_path not in sys.path:
                    sys.path.insert(0, scripts_path)
                break


def maya_useNewAPI():
    """Tell Maya to use the Python API 2.0."""
    pass


class {self.plugin_name}Command(OpenMaya.MPxCommand):
    """Command to launch the tool."""
    
    kPluginCmdName = "{self.plugin_name}"
    
    def __init__(self):
        OpenMaya.MPxCommand.__init__(self)
    
    def doIt(self, args):
        """Execute the command."""
        try:
{launch_code}
        except Exception as e:
            cmds.error(f"{self.plugin_name} error: {{e}}")
    
    @staticmethod
    def creator():
        return {self.plugin_name}Command()

{menu_code}{shelf_code}

def cleanup_tool_instances():
    """Clean up any open tool instances when plugin is unloaded."""
    try:
        # For dockable tools, delete workspace controls
        all_workspace_controls = cmds.lsUI(workspaceControls=True) or []
        for workspace_control in all_workspace_controls:
            # Check if this workspace control might be related to our plugin
            if "{self.plugin_name}" in workspace_control or workspace_control.endswith("_WorkspaceControl"):
                try:
                    # Try to get the UI script to see if it's ours
                    ui_script = cmds.workspaceControl(workspace_control, query=True, uiScript=True)
                    if ui_script and "{self.plugin_name}" in ui_script:
                        cmds.deleteUI(workspace_control)
                        print(f"Closed workspace control: {{workspace_control}}")
                except:
                    pass
        
        # For non-dockable tools, search Maya main window children
        # Try both PySide2 and PySide6
        for pyside_module in ["PySide6", "PySide2"]:
            try:
                # Import the required modules
                QtWidgets = __import__(f"{{pyside_module}}.QtWidgets", fromlist=["QtWidgets"]).QtWidgets
                shiboken = __import__(f"shiboken6" if pyside_module == "PySide6" else "shiboken2", fromlist=["wrapInstance"])
                
                # Get Maya main window
                from maya import OpenMayaUI as omui
                main_window_ptr = omui.MQtUtil.mainWindow()
                maya_main_window = shiboken.wrapInstance(int(main_window_ptr), QtWidgets.QMainWindow)
                
                # Search through all children of Maya main window
                for widget in maya_main_window.findChildren(QtWidgets.QWidget):
                    # Check by objectName or class name
                    if (widget.objectName() == "{self.plugin_name}" or 
                        widget.__class__.__name__ == "{self.plugin_name}"):
                        try:
                            widget.close()
                            widget.deleteLater()
                            print(f"Closed tool window: {{widget.__class__.__name__}}")
                        except:
                            pass
                
                break  # Successfully found and processed, don't try other PySide version
            except (ImportError, AttributeError):
                continue
            
    except Exception as e:
        print(f"Warning: Error during tool cleanup: {{e}}")


def initializePlugin(plugin):
    """Initialize the plugin."""
    # Import developer name from core
    try:
        from core import DEVELOPER
        vendor = DEVELOPER
    except ImportError:
        vendor = "Robotools"  # Fallback if core module not available
    
    pluginFn = OpenMaya.MFnPlugin(plugin, vendor, "1.0")
    try:
        _setup_plugin_path()
        pluginFn.registerCommand(
            {self.plugin_name}Command.kPluginCmdName,
            {self.plugin_name}Command.creator
        )
        {"create_menu()" if menu_parent else "pass"}
        {"create_shelf_button()" if shelf_name else "pass"}
    except:
        sys.stderr.write(f"Failed to register command: {{{self.plugin_name}Command.kPluginCmdName}}")
        raise


def uninitializePlugin(plugin):
    """Uninitialize the plugin."""
    pluginFn = OpenMaya.MFnPlugin(plugin)
    try:
        # Close any open tool instances
        cleanup_tool_instances()
        
        {shelf_uninit if shelf_uninit else "pass"}
        {menu_uninit if menu_uninit else "pass"}
        pluginFn.deregisterCommand({self.plugin_name}Command.kPluginCmdName)
    except:
        sys.stderr.write(f"Failed to deregister command: {{{self.plugin_name}Command.kPluginCmdName}}")
        raise
'''

        with open(plugin_file, 'w') as f:
            f.write(content)

        print(f"Created plugin file: {plugin_file.name}")
        return str(plugin_file)

    def _create_shelf_script(self, shelf_name: str, icon_filename: str = None) -> str:
        """Create a Python script for creating a shelf button."""
        script_file = self.plugin_dir / f'{self.plugin_name}_shelf.py'

        icon_name = icon_filename or "commandButton.png"
        icon_path = f"{self.plugin_dir}/icons/{icon_name}" if icon_filename else icon_name

        content = f'''"""
Shelf Button Script for {self.plugin_name}
Run this script in Maya to create a shelf button on the "{shelf_name}" shelf.
"""

from maya import cmds
import os

def create_shelf_button():
    """Create a shelf button for {self.plugin_name} on the {shelf_name} shelf."""
    
    shelf_name = "{shelf_name}"
    plugin_dir = r"{self.plugin_dir}"
    icon_path = os.path.join(plugin_dir, "icons", "{icon_name}")
    
    # Create shelf if it doesn't exist
    if not cmds.shelfLayout(shelf_name, exists=True):
        cmds.warning(f"Shelf '{{shelf_name}}' does not exist. Creating it...")
        mel.eval(f'addNewShelfTab("{{shelf_name}}")')
    
    # Switch to the shelf
    shelf_parent = mel.eval('$temp = $gShelfTopLevel')
    cmds.tabLayout(shelf_parent, edit=True, selectTab=shelf_name)
    
    # Remove existing button if it exists
    buttons = cmds.shelfLayout(shelf_name, query=True, childArray=True) or []
    for button in buttons:
        if cmds.shelfButton(button, query=True, label=True) == "{self.plugin_name}":
            cmds.deleteUI(button)
    
    # Use icon if it exists, otherwise use default
    if os.path.exists(icon_path):
        icon = icon_path
    else:
        icon = "{icon_name}"
    
    # Create shelf button
    cmds.shelfButton(
        parent=shelf_name,
        label="{self.plugin_name}",
        annotation=f"Launch {self.plugin_name}",
        image=icon,
        command="import maya.cmds as cmds; cmds.{self.plugin_name}()",
        sourceType="python"
    )
    
    print(f"Shelf button created on '{{shelf_name}}' shelf!")

# Run it
if __name__ == '__main__':
    import maya.mel as mel
    create_shelf_button()
'''

        with open(script_file, 'w') as f:
            f.write(content)

        print(f"Created shelf script: {script_file.name}")
        return str(script_file)

    def _create_menu_script(self, menu_parent: str) -> str:
        """Create a Python script for adding to a custom menu."""
        script_file = self.plugin_dir / f'{self.plugin_name}_menu.py'

        content = f'''"""
Menu Item Script for {self.plugin_name}
This menu item is automatically created when the plugin loads.
Run this script manually if you need to recreate the menu item.
"""

from maya import cmds

def create_menu_item():
    """Create menu item for {self.plugin_name} in {menu_parent}."""
    
    menu_parent = "{menu_parent}"
    menu_label = "{self.plugin_name}"
    
    # Create menu parent if it doesn't exist
    if not cmds.menu(menu_parent, exists=True):
        # Get the main Maya window
        main_window = mel.eval('$temp = $gMainWindow')
        
        # Create the menu
        cmds.menu(
            menu_parent,
            parent=main_window,
            label=menu_parent,
            tearOff=True
        )
        print(f"Created menu: '{{menu_parent}}'")
    
    # Remove old menu item if it exists
    menu_items = cmds.menu(menu_parent, query=True, itemArray=True) or []
    for item in menu_items:
        label = cmds.menuItem(item, query=True, label=True)
        if label == menu_label:
            cmds.deleteUI(item, menuItem=True)
    
    # Create new menu item
    cmds.menuItem(
        parent=menu_parent,
        label=menu_label,
        command='import maya.cmds as cmds; cmds.{self.plugin_name}()'
    )
    
    print(f"Menu item '{{menu_label}}' added to '{{menu_parent}}'!")

# Run it
if __name__ == '__main__':
    import maya.mel as mel
    create_menu_item()
'''

        with open(script_file, 'w') as f:
            f.write(content)

        print(f"Created menu script: {script_file.name}")
        return str(script_file)

    def _create_readme(self, icon_filename: str = None, menu_parent: str = None,
                       shelf_name: str = None) -> str:
        """Create installation README."""
        readme_file = self.plugin_dir / 'README.md'

        dockable_info = ""
        if self.dockable:
            dockable_info = "\n**Note**: This tool is configured as a dockable workspace control and will dock into Maya's UI.\n"

        content = f'''# {self.plugin_name} - Maya Plugin

## Installation

### Step 1: Copy Plugin Files

Copy both the plugin file and support folder to your Maya plug-ins directory:

**Files to copy:**
- `{self.plugin_name}.py` (plugin file)
- `{self.plugin_name}/` (support folder)

**Default Maya plug-ins locations:**
- **Windows**: `Documents/maya/<version>/plug-ins/`
- **Mac**: `~/Library/Preferences/Autodesk/maya/<version>/plug-ins/`
- **Linux**: `~/maya/<version>/plug-ins/`

**Alternative: Custom plug-ins directory**

If you prefer a custom location, set the `MAYA_PLUG_IN_PATH` environment variable in your `Maya.env` file:

1. Locate your `Maya.env` file:
   - **Windows**: `Documents/maya/<version>/Maya.env`
   - **Mac**: `~/Library/Preferences/Autodesk/maya/<version>/Maya.env`
   - **Linux**: `~/maya/<version>/Maya.env`

2. Add or edit the `MAYA_PLUG_IN_PATH` line:
   ```
   MAYA_PLUG_IN_PATH = /your/custom/path/to/plug-ins
   ```
   
3. For multiple paths, use `;` (Windows) or `:` (Mac/Linux):
   ```
   MAYA_PLUG_IN_PATH = /path/one;/path/two        (Windows)
   MAYA_PLUG_IN_PATH = /path/one:/path/two        (Mac/Linux)
   ```

For more information about Maya.env, see: [Autodesk Maya Environment Variables](https://help.autodesk.com/view/MAYAUL/2024/ENU/?guid=GUID-8EFB1AC1-ED7D-4099-9EEE-624097872C04)

### Step 2: Load the Plugin

1. Restart Maya (if it was running)
2. Open Maya's Plug-in Manager: `Windows > Settings/Preferences > Plug-in Manager`
3. Find `{self.plugin_name}.py` in the list
4. Check both "Loaded" and "Auto load" boxes

## Creating Launch UI

The plugin registers a Maya command `{self.plugin_name}()` that can be called from:
- MEL: `{self.plugin_name}`
- Python: `cmds.{self.plugin_name}()`
{dockable_info}
### Automatic Setup (Recommended)

The plugin is configured to launch via:
'''

        if menu_parent:
            content += f'''
**Custom Menu**: A menu item is automatically added to `{menu_parent}` when the plugin loads.
- To manually recreate: Run the script `{self.plugin_name}_menu.py` in the Script Editor
'''

        if shelf_name:
            content += f'''
**Shelf Button**: Run the script `{self.plugin_name}_shelf.py` to add a button to the `{shelf_name}` shelf.
- Opens the Script Editor (`Windows > General Editors > Script Editor`)
- File > Open Script: `{self.plugin_name}_shelf.py`
- Select all (Ctrl/Cmd+A) and execute (Ctrl/Cmd+Enter)
'''

        if not menu_parent and not shelf_name:
            content += '''
**Manual Setup Required**: No automatic menu or shelf was configured.
'''

        content += f'''

### Manual Creation

You can also create a shelf button manually:
1. Open the Script Editor
2. Enter: `import maya.cmds as cmds; cmds.{self.plugin_name}()`
3. Select the text and middle-mouse-drag it to your shelf
4. Right-click the button > Edit to set the icon (located in `icons/` folder)

Or add to any menu:
```python
cmds.menuItem(
    parent="YourMenu",
    label="{self.plugin_name}",
    command='import maya.cmds as cmds; cmds.{self.plugin_name}()'
)
```

## Usage

Once installed, launch the tool via:
'''

        if menu_parent:
            content += f"- **Menu**: `{menu_parent}` > `{self.plugin_name}`\n"
        if shelf_name:
            content += f"- **Shelf**: Click the button on the `{shelf_name}` shelf\n"

        content += f'''- **Command**: `cmds.{self.plugin_name}()` in Script Editor or MEL

## Uninstallation

1. Unload the plugin from the Plug-in Manager
2. Delete both files from your plug-ins directory:
   - Plugin file: `{self.plugin_name}.py`
   - Support folder: `{self.plugin_name}/`

## Distribution

To share this plugin with others, provide both:
1. The plugin file: `{self.plugin_name}.py`
2. The support folder: `{self.plugin_name}/`

Recipients should follow the Installation instructions above to install the plugin in their Maya environment.
'''

        with open(readme_file, 'w') as f:
            f.write(content)

        print(f"Created README: {readme_file.name}")
        return str(readme_file)


# Example usage
if __name__ == '__main__':
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(
        description='Bundle a Maya tool into a portable plugin',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Basic bundle with menu
  python maya_tool_bundler.py /path/to/stopwatch.py --name stopwatch --menu "MayaWindow|mainRigMenu"
  
  # With shelf and icon
  python maya_tool_bundler.py /path/to/tool.py --shelf "Custom" --icon /path/to/icon.png
  
  # With custom launch command
  python maya_tool_bundler.py /path/to/tool.py --launch "tool.show_ui()" --menu "MayaWindow|mainModelMenu"
  
  # Dockable widget (requires UI_SCRIPT constant in tool)
  python maya_tool_bundler.py /path/to/tool.py --dockable --launch "maya_tools.utilities.time_date_tool.TimeDateTool().show()" --shelf "Robotools"
  
Default paths:
  Icon directory: /Users/andrewdavis/Dropbox/Technology/Python3/Projects/Maya2025/images/icons/
  Output directory: Imports from core.core_paths.ROBOTOOLS_PLUGINS_DIR
        '''
    )
    parser.add_argument('root_file', help='Path to the main Python file of your tool')
    parser.add_argument('--output-dir', help='Output directory for the bundled plugin (optional)')
    parser.add_argument('--scripts-root', help='Root directory for script imports (e.g., .../scripts)')
    parser.add_argument('--name', help='Plugin name (defaults to root file name)')
    parser.add_argument('--icon', help='Path to icon file (.png, .svg, etc.)')
    parser.add_argument('--launch', help='Custom launch command (e.g., "my_module.launch()")')
    parser.add_argument('--menu', help='Parent menu to add tool to (e.g., "MayaWindow|mainRigMenu")')
    parser.add_argument('--shelf', help='Shelf name to add button to (e.g., "Custom")')
    parser.add_argument('--dockable', action='store_true', help='Make tool dockable (requires UI_SCRIPT constant)')

    args = parser.parse_args()

    root_file = Path(args.root_file)
    scripts_root = Path(args.scripts_root) if args.scripts_root else None

    # Import ROBOTOOLS_PLUGINS_DIR if output_dir not specified
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        try:
            from core.core_paths import ROBOTOOLS_PLUGINS_DIR
            output_dir = ROBOTOOLS_PLUGINS_DIR
        except ImportError:
            print("Error: Could not import ROBOTOOLS_PLUGINS_DIR from core.core_paths")
            print("Please specify --output-dir explicitly")
            sys.exit(1)

    bundler = MayaToolBundler(root_file, output_dir, args.name, args.launch, scripts_root, args.dockable)
    result = bundler.bundle(args.icon, args.menu, args.shelf)

    print("\nFiles created:")
    for key, path in result.items():
        print(f"  {key}: {path}")