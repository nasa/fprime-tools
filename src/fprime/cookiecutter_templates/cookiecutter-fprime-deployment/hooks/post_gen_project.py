import os
import shutil

"""
Post-generation hook to clean up ComLoggerTee directories when logging is disabled.
"""
use_core_subtopologies = "{{ cookiecutter.use_core_subtopologies }}"
enable_logging = "{{ cookiecutter.enable_logging }}"

# Only remove directories if logging is disabled or subtopologies are not used
if enable_logging != "yes":
    # Remove EventLoggerTee directory if it exists
    event_logger_dir = os.path.join("Top", "EventLoggerTee")
    if os.path.exists(event_logger_dir):
        shutil.rmtree(event_logger_dir)
    
    # Remove TlmLoggerTee directory if it exists  
    tlm_logger_dir = os.path.join("Top", "TlmLoggerTee")
    if os.path.exists(tlm_logger_dir):
        shutil.rmtree(tlm_logger_dir)
