# Experiment controller for CARLA drivers

## Setup

CARLA PythonAPI is expected in `../carla/dist` relative to this project

### Configuring Pylance (`Python > Analysis`)

Add `{path_to_carla}\PythonAPI\carla\dist\carla-0.9.13-py3.7-win-amd64.egg` to the `Extra Paths`

It is expected that
- `Type Checking Mode` = `strict`
- `Stub Path` = `typings`

## Requires

### pip

- python@3.7
- pygame@2.2
- numpy@1.21
- pywin32@305
- pywin32-stubs@1.0
- jsonpickle@3.0
- moderngl@5.8

### external

- [glslViewer](https://github.com/patriciogonzalezvivo/glslViewer) to inspect the shader (`glslViewer ./shaders/zoom_x.frag "path/to/some/image.png"`)
- [glslang@12.1](https://github.com/KhronosGroup/glslang) for GLSL Linter extension to be set in `Validator Path` in its settings

May also require

### pip

- Pillow@9.4
- mypy@1.1
- mypy-extensions@1.0
- typing_extensions@4.5
- data-science-types@0.2
