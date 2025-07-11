import sys
import os
from pathlib import Path

# Get the subtopology parameters from cookiecutter
subtopology_template_path = "{{ cookiecutter.subtopology_template_path }}"
subtopology_instance_name = "{{ cookiecutter.subtopology_instance_name }}"

# Handle both absolute and relative paths
current_dir = Path.cwd()
template_path = Path(subtopology_template_path)
if not template_path.is_absolute():
    # Need to go up one level since we're already in the target directory
    parent_dir = current_dir.parent
    template_path = (parent_dir / template_path).resolve()
else:
    template_path = template_path.resolve()

source_ping_entries = template_path / "PingEntries.hpp"
target_ping_entries = Path(".") / "PingEntries.hpp"
cmake_file = Path(".") / "CMakeLists.txt"

def path_to_target_name(path):
    """
    Convert a filesystem path to a CMake target name using only the F' builder API.
    
    This function attempts to use the CMakeHandler class from the F' build system to 
    convert a path to a CMake target name following F' conventions.
    
    Args:
        path: Path object or string representing the path to convert
        
    Returns:
        String representing the CMake target name
    """
    try:
        # Import the F' builder API - we import here to avoid making it a hard requirement
        # that could break the template for users who don't have the full environment
        from fprime.fbuild.cmake import CMakeHandler
        
        # Create CMakeHandler instance without requiring a build directory
        cmake_handler = CMakeHandler()
        
        # Try to use the CMakeHandler to get the module name
        # Since we don't have a build directory, we'll pass None
        return cmake_handler.get_cmake_module(str(Path(path).resolve()), None)
    except Exception:
        # If the CMakeHandler approach fails (either import error or runtime error),
        # fall back to a simple approach that mimics the core logic of the F' build system
        
        # Get standardized path string
        path_obj = Path(path).resolve()
        
        # Get the final components of the path
        # This is a simplified version of what F' does with project-relative paths
        components = path_obj.parts
        
        # Use the last three path components, which is often sufficient
        # when we can't determine the project-relative path properly
        rel_path = "/".join(components[-3:] if len(components) >= 3 else components)
        
        # Convert path separators to underscores for target name, which is
        # exactly what the CMakeHandler.get_cmake_module method does
        target_name = rel_path.replace("/", "_").replace("\\", "_")
        
        # Remove any leading/trailing underscores
    return target_name.strip("_")

def resolve_subtopology_dependencies(template_path):
    """
    Resolve subtopology dependencies following F' naming conventions.
    
    Args:
        template_path: Path to the subtopology template directory
    
    Returns:
        List of CMake target dependencies needed for this subtopology instance
    """
    template_path = Path(template_path).resolve()
    template_name = template_path.name
    
    dependencies = []
    
    # Add the main subtopology target
    main_target = path_to_target_name(template_path)
    dependencies.append(main_target)

    # Check for and add the Config dependency if it exists
    config_dir = template_path / f"{template_name}Config"
    if config_dir.exists() and config_dir.is_dir():
        config_target = path_to_target_name(config_dir)
        dependencies.append(config_target)
    
    return dependencies

try:
    # Step 1: Copy and modify PingEntries.hpp
    with open(source_ping_entries, 'r') as f:
        content = f.read()
    
    # Extract the subtopology template name from the path for replacement
    template_name = template_path.name
    
    # Replace the subtopology template name with instance name
    content = content.replace(template_name, subtopology_instance_name)
    
    # Fix header guard: replace any variant of template name in uppercase with instance name
    template_upper = template_name.upper()
    instance_upper = subtopology_instance_name.upper()
    content = content.replace(f"{template_upper}_PINGENTRIES_HPP", f"{instance_upper}_PINGENTRIES_HPP")
    
    with open(target_ping_entries, 'w') as f:
        f.write(content)
    
    print(f"[INFO] Successfully copied and modified PingEntries.hpp from {template_path}")
    
    # Step 2: Resolve dependencies and update CMakeLists.txt
    dependencies = resolve_subtopology_dependencies(template_path)
    dependencies_str = ";".join(dependencies)
    
    with open(cmake_file, 'r') as f:
        cmake_content = f.read()
    
    cmake_content = cmake_content.replace('set(SUBTOPOLOGY_DEPENDS "PLACEHOLDER_DEPENDENCIES")', 
                                         f'set(SUBTOPOLOGY_DEPENDS "{dependencies_str}")')
    
    with open(cmake_file, 'w') as f:
        f.write(cmake_content)
    
    print(f"[INFO] Resolved subtopology dependencies: {dependencies_str}")
    print(f"[INFO] Successfully updated CMakeLists.txt with dependencies")
    
except PermissionError:
    print(f"[ERROR] Permission denied accessing files. Check file permissions.")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] Failed to process subtopology instance: {e}")
    sys.exit(1)
