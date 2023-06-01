#version 300 es

#ifdef GL_ES
precision mediump float;
#endif

/*
 The shader has two behaviours:
    1. distorts the image on a side like in real cars
    2. colorizes the inspection matrix pixels
 This shader may run from ModernGL, but also from glslViewer.
 These environments instantiate the uniforms differently,
 this is why there are few if-else statements in this code
 exploring what data is available for the shader
*/

// Position 0 in the list of uniforms has the texture
uniform sampler2D u_texture;

// These uniforms are injected automatically by glslViewers,
// and also manually in opengl_renderer.py to support compatibility with glslViewer
uniform vec2 u_resolution;
uniform float u_time;
uniform vec2 u_mouse;

// These additional uniform set in opengl_renderer.py
// - supports zomming with the mouse scroll
uniform float u_zoom;
// - enables colorization of the inspection matrix pixels
uniform bool u_colorize;
// - reverses the thredhold
uniform bool u_reversed;

const vec3 BLANK_COLOR = vec3(0.0, 0.0, 0.2);

// Constants used for colorizing the inspection matrix
const float PI = 3.14159265359;
const float COLOR_GAIN = 1.0 / sin( PI / 3.0 ) / 2.0;
const float PHASE_120 = 2.0 * PI / 3.0;
const vec3 MATRIX_COLOR = vec3(1, 0, 1);

// Constants for image distortion
const float THRESHOLD = 0.30;
const float ZOOM = 1.4;

// Pipeline attributes
in vec2 v_uv;      // modernGL only
out vec4 out_color;

void main() {
    vec2 uv;

    // Choose the source of UV coordinates
    uv = v_uv == vec2(0) ? gl_FragCoord.xy / u_resolution : v_uv;

    // Choose the source of the parameters of the image distortion algorithm
    float zoom = u_zoom == 0. ? ZOOM : u_zoom;

    float threshold = u_mouse.x == 0.
        ? (u_reversed ? 1. - THRESHOLD : THRESHOLD)
        : 1. - u_mouse.x / u_resolution.x;

    // Apply distortion
    float zy = zoom * threshold;
    float denom = 1. - threshold;

    if (threshold < 0. || threshold > 1. || zoom <= 0.) {
        // do nothing
    }
    else if (u_reversed) {
        // Line started from the origin
        float a = 1. - (1. - threshold) / threshold * (zoom - 1.);
        float b = 0.;

        if (uv.x <= threshold) {
            uv.x = a * uv.x + b;
        }
        else {
            // Parabolic end
            float a_ =  (1. - a - b) / denom / denom;
            float b_ =  a - 2. * threshold * a_;
            float c_ = 1. - a_ - b_;
            uv.x = a_ * uv.x * uv.x + b_ * uv.x + c_;
        }
    }
    else {
        // Line ending in (1,1)
        float a = (1. - zy) / denom;
        float b = (zy - threshold) / denom;

        if (uv.x <= threshold) {
            // Parabolic start
            float a_ =  -b / threshold / threshold;
            float b_ =  a + 2. * b / threshold;
            uv.x = a_ * uv.x * uv.x + b_ * uv.x;
        }
        else {
            uv.x = a * uv.x + b;
        }
        // uv.x *= zoom;
    }

    // Calculate the output color
    vec3 color;

    if (uv.x > 1. || uv.x < 0. || uv.y > 1. || uv.y < 0.) {
        // sets the pixels outside the texture to the blank color
        color = BLANK_COLOR;
    } else {
        color = texture(u_texture, uv).rgb;

        // colorize the matrix pixels if the colorization mode is on
        if (u_colorize && color == MATRIX_COLOR) {
            color = vec3(
                0.5 + COLOR_GAIN * sin(u_time + PHASE_120), 
                0.5 + COLOR_GAIN * sin(u_time), 
                0.5 + COLOR_GAIN * sin(u_time - PHASE_120)
            );
        }
    }

    out_color = vec4(color, 1.);
}
