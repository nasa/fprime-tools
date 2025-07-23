from pathlib import Path
from fprime.fbuild.builder import Build
from fprime.fbuild.types import BuildType

"""
Post-generation hook that configures the generated subtopology instance:
1. Copies the PingEntries.hpp file from the subtopology template, with correct references to the template name
2. Updates include paths in the subtopology instance file, if the template path was relative
3. Updates the CMakeLists.txt file with proper subtopology dependencies
"""

project_path = Build.find_nearest_parent_project(Path.cwd())
build = Build(BuildType.BUILD_NORMAL, project_path)
build.load()

subtopology_template_path = "{{ cookiecutter.subtopology_template_path }}"
subtopology_instance_name = "{{ cookiecutter.subtopology_instance_name }}"

# Handle both absolute and relative paths, and remember if it was relative
current_dir = Path.cwd()
template_path = Path(subtopology_template_path)
was_relative = not template_path.is_absolute()
if was_relative:
    parent_dir = current_dir.parent
    template_path = (parent_dir / template_path).resolve()
else:
    template_path = template_path.resolve()

# Extract the subtopology template name from the path for replacement
template_name = template_path.name

# Access files
source_ping_entries = template_path / "PingEntries.hpp"
target_ping_entries = Path(".") / "PingEntries.hpp"
cmake_file = Path(".") / "CMakeLists.txt"
subtopology_file = Path(".") / f"{subtopology_instance_name}.fpp"

with open(source_ping_entries, "r") as f:
    content = f.read()

# Replace the subtopology template name with instance name
content = content.replace(template_name, subtopology_instance_name)

# Fix header guard: replace any variant of template name in uppercase with instance name
template_upper = template_name.upper()
instance_upper = subtopology_instance_name.upper()
content = content.replace(
    f"{template_upper}_PINGENTRIES_HPP", f"{instance_upper}_PINGENTRIES_HPP"
)


with open(subtopology_file, "r") as f:
    subtopology_content = f.read()

with open(cmake_file, "r") as f:
    cmake_content = f.read()

# If the original template path was relative, prepend ../ to all its occurrences in the subtopology instance file
if was_relative:
    subtopology_content = subtopology_content.replace(
        subtopology_template_path, f"../{subtopology_template_path}"
    )

cmake_content = cmake_content.replace(
    "PLACEHOLDER_DEPENDENCIES", f"{build.get_module_name(template_path)}"
)

with open(target_ping_entries, "w") as f:
    f.write(content)

with open(subtopology_file, "w") as f:
    f.write(subtopology_content)

with open(cmake_file, "w") as f:
    f.write(cmake_content)

print(f"[INFO] Successfully copied and modified PingEntries.hpp from {template_path}")
print(f"[INFO] Updated {subtopology_file} with correct include path(s) if needed.")
print(f"[INFO] Updated {cmake_file} with correct subtopology dependencies.")

print("[REMINDER] Don't forget to:")
print(
    f"  1. Import {subtopology_instance_name}.Subtopology in your main topology.fpp file"
)
print(
    f"  2. Include {subtopology_instance_name}/PingEntries.hpp in your main topology's TopologyDefs.hpp file"
)
