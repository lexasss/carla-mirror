from typing import Tuple, Any

import pygame
import struct
import moderngl

class OpenGLRenderer:
    def __init__(self, size: Tuple[int,int], shader_name: str = ''):
        screen = pygame.display.set_mode(size, pygame.constants.DOUBLEBUF | pygame.constants.OPENGL | pygame.constants.NOFRAME ).convert((0xff, 0xff00, 0xff0000, 0))
        ctx = moderngl.create_context()

        texture_coordinates = [0, 1,  1, 1,  0, 0,  1, 0]
        world_coordinates = [-1, -1,  1, -1,  -1,  1,  1,  1]
        render_indices = [0, 1, 2, 1, 2, 3]
                  
        prog = ctx.program(
            vertex_shader = open(f'shaders/vert_{shader_name}.glsl').read(),
            fragment_shader = open(f'shaders/frag_{shader_name}.glsl').read()
        )

        screen_texture = ctx.texture(size, 3, pygame.image.tostring(screen, 'RGB'))
        screen_texture.repeat_x = False
        screen_texture.repeat_y = False

        vbo = ctx.buffer(struct.pack('8f', *world_coordinates))
        uvmap = ctx.buffer(struct.pack('8f', *texture_coordinates))
        ibo = ctx.buffer(struct.pack('6I', *render_indices))

        vao_content = [
            (vbo, '2f', 'vert'),
            (uvmap, '2f', 'in_text')
        ]

        self.vao = ctx.vertex_array(prog, vao_content, ibo) # pyright: ignore
        self.screen = screen
        self.screen_texture = screen_texture
        #self.ctx = ctx


    def render(self, texture_data: Any):
        self.screen_texture.write(texture_data)
        self.screen_texture.use()
        self.vao.render()

