from typing import Tuple, Set, Any
from datetime import datetime

import pygame
import struct
import moderngl

SHADER_CONTROL_WITH_MOUSE = False

class OpenGLRenderer:
    def __init__(self, size: Tuple[int,int], shader_name: str = '', display_check_matrix: bool = False):
        screen = pygame.display.set_mode(size, pygame.constants.DOUBLEBUF | pygame.constants.OPENGL | pygame.constants.NOFRAME ).convert((0xff, 0xff00, 0xff0000, 0))
        ctx = moderngl.create_context()

        self._program = ctx.program(
            vertex_shader = open(f'shaders/{shader_name}.vert').read(),
            fragment_shader = open(f'shaders/{shader_name}.frag').read()
        )
        
        texture_coordinates = [0, 1,  1, 1,  0, 0,  1, 0]
        world_coordinates = [-1, -1,  1, -1,  -1,  1,  1,  1]
        render_indices = [0, 1, 2,  1, 2, 3]
                  
        vbo = ctx.buffer(struct.pack('8f', *world_coordinates))
        uvmap = ctx.buffer(struct.pack('8f', *texture_coordinates))
        ibo = ctx.buffer(struct.pack('6I', *render_indices))

        vao_content = [
            (vbo, '2f', 'in_coords'),
            (uvmap, '2f', 'in_uv')
        ]

        self._vao = ctx.vertex_array(self._program, vao_content, ibo) # pyright: ignore

        screen_texture = ctx.texture(size, 3, pygame.image.tostring(screen, 'RGB'))
        screen_texture.repeat_x = False
        screen_texture.repeat_y = False
        self._screen_texture = screen_texture

        self._zoom = 0.5
        self._timestamp = datetime.now().timestamp()

        self.screen = screen
        self.mouse = 0.0, 0.0
        
        #self.ctx = ctx

        self._glsl_uniforms: Set[str] = set()
        self._injectUniform(size, display_check_matrix)
        
    def zoomIn(self):
        self._zoom += 0.1

    def zoomOut(self):
        self._zoom -= 0.1

    def render(self, texture_data: Any):
        if SHADER_CONTROL_WITH_MOUSE:
            if ('u_time' in self._glsl_uniforms):
                self._program['u_time'] = datetime.now().timestamp() - self._timestamp
            if ('u_mouse' in self._glsl_uniforms):
                self._program['u_mouse'] = self.mouse
            if ('u_zoom' in self._glsl_uniforms):
                self._program['u_zoom'] = self._zoom
        
        self._screen_texture.write(texture_data)
        self._screen_texture.use()
        self._vao.render()
        
    # Internal

    def _injectUniform(self, size: Tuple[int,int], colorize: bool):
        # only for debugging
        for name in self._program:
            member = self._program[name]
            if isinstance(member, moderngl.Uniform):
                self._glsl_uniforms.add(name)
                print(f'OGL: {member.location}: uniform [{member.dimension}] {name}')
            elif isinstance(member, moderngl.Attribute):
                print(f'OGL: {member.location}: in [{member.dimension}] {name}')
        
        if SHADER_CONTROL_WITH_MOUSE:
            if ('u_resolution' in self._glsl_uniforms):
                self._program['u_resolution'] = size
            if ('u_colorize' in self._glsl_uniforms):
                self._program['u_colorize'] = colorize
        