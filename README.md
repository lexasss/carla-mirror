# Experiment controller for CARLA drivers

## Requires

Python 3.7

## Setup

CARLA PythonAPI is expected to be in `../carla/dist` relative to this project

### Configuring Pylance (`Python > Analysis`)

Add `{path_to_carla}\PythonAPI\carla\dist\carla-0.9.13-py3.7-win-amd64.egg` to the `Extra Paths`

It is expected that
- `Type Checking Mode` = `strict`
- `Stub Path` = `typings`

### External dependencies

- [glslViewer](https://github.com/patriciogonzalezvivo/glslViewer) to inspect the shader (run `glslViewer ./shaders/zoom_x.frag "path/to/some/image.png"`)
- [glslang@12.1](https://github.com/KhronosGroup/glslang) for GLSL Linter extension to be set in `Validator Path` in its settings (clone this repo)

### PIP virtual environment

Activate the virtual environment by launching `run_env.bat` from the VS Code terminal
