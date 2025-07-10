#!/usr/bin/env python3
"""
Post-generation hook for F Prime deployment cookiecutter template.
Provides guidance to the user after project generation.
"""

# Get cookiecutter variables
name = "{{ cookiecutter.deployment_name }}"
use_subtopologies = "{{ cookiecutter.use_core_subtopologies }}"
communication_type = "{{ cookiecutter.communication_type }}"
com_driver_type = "{{ cookiecutter.com_driver_type }}"

print("\n" + "="*60)
print(f"✅ F Prime deployment '{name}' generated successfully!")
print("="*60)

if use_subtopologies == "yes":
    print(f"\n🚀 Your deployment uses F Prime core subtopologies:")
    print(f"   • CdhCore: Command dispatch, health monitoring, events, telemetry")
    print(f"   • {communication_type}: Communication subsystem")
    print(f"   • DataProducts: Data product management")
    print(f"   • FileHandling: File upload/download capabilities")
    print(f"\n💡 Benefits of using subtopologies:")
    print(f"   • Modular, reusable architecture")
    print(f"   • Reduced configuration complexity")
    print(f"   • Consistent with F Prime best practices")
    print(f"   • Pre-configured component interconnections")
    print(f"   • Automatic dependency management")
else:
    print(f"\n🔧 Your deployment uses individual components (legacy mode)")
    print(f"   • Communication driver: {com_driver_type}")
    print(f"   • All components configured individually")
    print(f"   • Full manual control over topology")
    print(f"\n💡 Consider upgrading to subtopologies for:")
    print(f"   • Better modularity and reusability")
    print(f"   • Simplified configuration")
    print(f"   • Alignment with F Prime best practices")

print(f"\n🏁 Next steps:")
print(f"   1. Navigate to your deployment: cd {name}")
print(f"   2. Build the deployment: fprime-util build")
print(f"   3. Generate the deployment: fprime-util impl")
print(f"   4. Build again: fprime-util build")
print(f"   5. Run the deployment: ./build-fprime-automatic-*/bin/{name}")

print(f"\n📚 For more information:")
print(f"   • F Prime Tutorial: https://fprime.jpl.nasa.gov/latest/docs/tutorials/")
print(f"   • F Prime User Guide: https://fprime.jpl.nasa.gov/latest/docs/")
print(f"   • Subtopologies Guide: https://fprime.jpl.nasa.gov/latest/docs/subtopologies/")

print("\n" + "="*60)
