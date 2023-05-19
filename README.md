# Experiment controller for CARLA drivers

## Requires

Python 3.7.9

## Setup

The project mus tbe located inside CARLA's PythonAPI folder, so that `PythonAPI/carla/dist` exists nearby

### Configuring Pylance (`Python > Analysis`)

Add `{path_to_carla}\PythonAPI\carla\dist\carla-0.9.13-py3.7-win-amd64.egg` to the `Extra Paths`

It is expected that
- `Type Checking Mode` = `strict`
- `Stub Path` = `typings`

### External dependencies

- [glslViewer](https://github.com/patriciogonzalezvivo/glslViewer) to inspect the shader (run `glslViewer ./shaders/zoom_x.frag "path/to/some/image.png"`)
- [glslang@12.1](https://github.com/KhronosGroup/glslang) for GLSL Linter extension to be set in `Validator Path` in its settings (clone this repo)

### Virtual environment and installing dependencies

After cloning the project, run the following scripts form the VS Code terminal
 - `env.bat` to create the virtual environment,
 - `install.bat` to install dependencies
