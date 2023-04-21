#version 300 es
precision mediump float;
uniform sampler2D Texture;

vec2 CENTER = vec2(0.5, 0.4);
vec2 EXP = vec2(2.0, 1.4);
float ZOOM = 0.5;

out vec4 color;
in vec2 v_text;
void main() {
  vec2 off_center = v_text - CENTER;

  off_center *= (1.0 + ZOOM * pow(abs(2.0 * off_center.xy), EXP))/(1.0 + ZOOM);

  vec2 v_text2 = CENTER + off_center;

  if (v_text2.x > 1.0 || v_text2.x < 0.0) {
    color = vec4(0.0, 0.0, 0.0, 1.0);
  } else {
    color = vec4(texture(Texture, v_text2).rgb, 1.0);
  }
}
