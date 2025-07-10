# {{cookiecutter.deployment_name}} F' Deployment

This F' deployment was generated using the F' cookiecutter template.

{%- if cookiecutter.use_core_subtopologies == "yes" %}

## Architecture Overview

This deployment uses F' **core subtopologies** for a modular, reusable architecture:

### 🏗️ Core Subtopologies Included

- **CdhCore**: Command & Data Handling
  - Command dispatching and sequencing
  - Event logging and telemetry collection  
  - Health monitoring system
  - Fatal error handling

- **{{cookiecutter.communication_type}}**: Communication Subsystem
  - {{cookiecutter.communication_type}} protocol implementation
  - Uplink/downlink data handling
  - Frame processing and routing

- **DataProducts**: Data Product Management
  - Data product cataloging
  - Storage and retrieval capabilities
  - Product metadata management

- **FileHandling**: File Transfer Capabilities
  - File upload and download services
  - Parameter database management
  - File system operations

### 💡 Benefits of Subtopology Architecture

- **Modularity**: Well-defined interfaces between subsystems
- **Reusability**: Standard subtopologies across F' projects
- **Maintainability**: Centralized configuration and updates
- **Best Practices**: Follows F' architectural guidelines

{%- else %}

## Architecture Overview

This deployment uses **individual components** (legacy mode) with the following communication setup:
- **Communication Driver**: {{cookiecutter.com_driver_type}}
- **Protocol**: F' standard framing and protocol

This mode provides full control over individual component configuration but requires more manual setup compared to subtopology-based deployments.

{%- endif %}

## Building the {{cookiecutter.deployment_name}} Deployment

### Prerequisites
- F' development environment set up
- Required dependencies installed

### Build Process

1. **Generate build cache**:
   ```bash
   cd {{cookiecutter.deployment_name}}
   fprime-util generate
   ```

2. **Build the deployment**:
   ```bash
   fprime-util build
   ```

{%- if cookiecutter.use_core_subtopologies == "yes" %}

   > **Note**: When using subtopologies, the build process automatically includes all subtopology dependencies and configurations.

{%- endif %}

## Running the Application

### Option 1: Run with F' Ground Data System (GDS)

The easiest way to run and interact with your deployment:

```bash
cd {{cookiecutter.deployment_name}}
fprime-gds
```

This command will:
- Start the {{cookiecutter.deployment_name}} application
- Launch the F' Ground Data System interface
- Set up communication between the app and GDS

### Option 2: Run GDS and Application Separately

Start the GDS without automatically launching the app:
```bash
cd {{cookiecutter.deployment_name}}
fprime-gds --no-app
```

Then run the application binary manually:
```bash
cd {{cookiecutter.deployment_name}}/build-artifacts/<platform>/bin/
./{{cookiecutter.deployment_name}} -a 127.0.0.1 -p 50000
```

{%- if cookiecutter.use_core_subtopologies == "no" %}

### Communication Configuration

{%- if cookiecutter.com_driver_type in ["TcpClient", "TcpServer"] %}
This deployment uses {{cookiecutter.com_driver_type}} for communication. Ensure the specified hostname and port are available.
{%- elif cookiecutter.com_driver_type == "UART" %}
This deployment uses UART communication. Ensure the UART device is available and properly configured.
{%- endif %}

{%- endif %}

## Project Structure

```
{{cookiecutter.deployment_name}}/
├── Top/                         # Topology definition
│   ├── topology.fpp            # F' topology specification
│   ├── instances.fpp           # Component instances
│   └── {{cookiecutter.deployment_name}}Topology.*  # C++ topology implementation
├── Main.cpp                    # Application entry point
└── CMakeLists.txt             # Build configuration
```

{%- if cookiecutter.use_core_subtopologies == "yes" %}

## Working with Subtopologies

### Configuration
Most component configuration is handled automatically by the subtopologies. Deployment-specific configuration can be added in:
- `{{cookiecutter.deployment_name}}Topology.cpp` in the `configureTopology()` function

### Adding Custom Components
To add custom components to your subtopology-based deployment:
1. Add your component instances to `instances.fpp`
2. Connect them in the `{{cookiecutter.deployment_name}}` connections block in `topology.fpp`
3. Register commands and configure as needed in the topology C++ files

### Subtopology Documentation
- [F' Subtopologies Guide](https://fprime.jpl.nasa.gov/latest/docs/subtopologies/)
- [CdhCore Documentation](https://fprime.jpl.nasa.gov/latest/docs/subtopologies/cdhcore/)
- [Communication Subtopologies](https://fprime.jpl.nasa.gov/latest/docs/subtopologies/comm/)

{%- else %}

## Customizing Your Deployment

### Adding Components
1. Add component instances to `instances.fpp`
2. Wire connections in `topology.fpp`  
3. Configure components in `{{cookiecutter.deployment_name}}Topology.cpp`
4. Register commands and set up parameters as needed

### Communication Setup
The deployment is configured for {{cookiecutter.com_driver_type}} communication. To change communication settings, modify the topology files and rebuild.

{%- endif %}

## Next Steps

1. **Explore the F' Tutorial**: https://fprime.jpl.nasa.gov/latest/docs/tutorials/
2. **Read the User Guide**: https://fprime.jpl.nasa.gov/latest/docs/
3. **Add Custom Components**: Create your own components following F' patterns
4. **Configure for Your Mission**: Customize the deployment for your specific requirements

## Troubleshooting

### Build Issues
- Ensure all F' dependencies are installed
- Check that `fprime-util generate` completed successfully
- Verify you're in the correct directory

### Runtime Issues  
- Check that communication ports are available
- Verify hostname/IP addresses are correct
- Ensure proper permissions for hardware access (if using UART)

{%- if cookiecutter.use_core_subtopologies == "yes" %}
- Review subtopology logs for configuration issues
{%- endif %}

For more help, visit the [F' Community](https://github.com/nasa/fprime) or [Documentation](https://fprime.jpl.nasa.gov/latest/docs/).
