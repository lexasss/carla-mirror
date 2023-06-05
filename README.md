# Experiment controller for CARLA drivers

## Requires

- [CARLA 0.9.13](https://github.com/carla-simulator/carla/releases/tag/0.9.13/)
- [Python 3.7.9](https://www.python.org/downloads/release/python-379/)
- [VC++ 2019 runtime](https://aka.ms/vs/17/release/vc_redist.x64.exe)

## Setup

The project must be located inside CARLA's `PythonAPI` folder

VS Code extension used:
- Python + Pylance
- GLSL Linter
- Shader languages support for VS Code
- WebGL GLSL Editor

### Configuring Pylance (`Python > Analysis`)

Add `{path_to_carla}\PythonAPI\carla\dist\carla-0.9.13-py3.7-win-amd64.egg` to the `Extra Paths`

It is expected that
- `Type Checking Mode` = `strict`
- `Stub Path` = `typings`

### External dependencies

- [glslViewer](https://github.com/patriciogonzalezvivo/glslViewer) to inspect the shader (run `glslViewer ./shaders/zoom_in.frag "path/to/some/image.png"`)
- [glslang@12.1](https://github.com/KhronosGroup/glslang) binaries: set the path of `glslangValidator` to `Validator Path` of __GLSL Linter__ extension settings

### Setting up the virtual environment and installing dependencies

After cloning the project, run the following scripts form the VS Code terminal
 - `env.bat` to create the virtual environment,
 - `install.bat` to install dependencies (make sure you run this in the cmd line prefixed with `(.venv)`)

## Running

Run `python main.py [options]` to display a mirror
Run `python main.py --help` to see all options available

Run `python map.py <id>` to set a map (`python main.py` also allows settings a map, but could be slow and result in time-out error)