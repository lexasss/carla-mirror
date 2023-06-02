# Experiment controller for CARLA drivers

## Requires

- CARLA 0.9.13
- Python 3.7.9
- [VC++ 2019 runtime](https://aka.ms/vs/17/release/vc_redist.x64.exe)

## Setup

The project must be located inside CARLA's PythonAPI folder

### Configuring Pylance (`Python > Analysis`)

Add `{path_to_carla}\PythonAPI\carla\dist\carla-0.9.13-py3.7-win-amd64.egg` to the `Extra Paths`

It is expected that
- `Type Checking Mode` = `strict`
- `Stub Path` = `typings`

### External dependencies

- [glslViewer](https://github.com/patriciogonzalezvivo/glslViewer) to inspect the shader (run `glslViewer ./shaders/zoom_x.frag "path/to/some/image.png"`)
- [glslang@12.1](https://github.com/KhronosGroup/glslang) binaries: path to `glslangValidator` to be set in `Validator Path` of __GLSL Linter__ extension settings

### Virtual environment and installing dependencies

After cloning the project, run the following scripts form the VS Code terminal
 - `env.bat` to create the virtual environment,
 - `install.bat` to install dependencies (make sure you run this in the cmd line prefixed with )
