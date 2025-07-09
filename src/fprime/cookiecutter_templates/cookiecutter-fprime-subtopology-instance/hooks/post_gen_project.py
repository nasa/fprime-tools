"""
Post-generation hook for subtopology instance creation.
This hook copies the actual PingEntries.hpp from the selected subtopology template
and modifies it to use the instance-specific naming.
"""

import sys
from pathlib import Path

# Get cookiecutter variables
subtopology_template = "{{ cookiecutter.subtopology_template }}"
subtopology_instance_name = "{{ cookiecutter.subtopology_instance_name }}"
framework_path = "{{ cookiecutter._framework_path_str }}"

if subtopology_template == "None":
    print(f"[INFO] No core subtopology template selected. Please manually configure PingEntries.hpp")
else:
    source_ping_entries = Path(framework_path) / "Svc" / "Subtopologies" / subtopology_template / "PingEntries.hpp"
    target_ping_entries = Path(".") / "PingEntries.hpp"

    try:
        with open(source_ping_entries, 'r') as f:
            content = f.read()
        
        # Simple find and replace
        # Replace the subtopology template name with instance name
        content = content.replace(subtopology_template, subtopology_instance_name)
        
        # Fix header guard: replace any variant of template name in uppercase with instance name
        template_upper = subtopology_template.upper()
        instance_upper = subtopology_instance_name.upper()
        content = content.replace(f"{template_upper}_PINGENTRIES_HPP", f"{instance_upper}_PINGENTRIES_HPP")
        
        with open(target_ping_entries, 'w') as f:
            f.write(content)
        
        print(f"[INFO] Successfully copied and modified PingEntries.hpp from {subtopology_template}")
        
    except Exception as e:
        print(f"[ERROR] Failed to copy and modify PingEntries.hpp: {e}")
        sys.exit(1)
