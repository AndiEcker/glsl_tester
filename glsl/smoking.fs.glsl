$HEADER$

uniform float alpha;
uniform float contrast;
uniform float tex_col_mix;
uniform float time;
uniform vec2 center_pos;
uniform vec2 mouse;         // density, speed
uniform vec2 win_pos;
uniform vec2 resolution;
uniform vec4 tint_ink;

const float ONE = 0.99999999999999;

float rand(vec2 n) {
 //This is just a compounded expression to simulate a random number based on a seed given as n
 return fract(cos(dot(n, vec2(12.98982, 4.14141))) * 43758.54531);
}

float noise(vec2 n) {
 //Uses the rand function to generate noise
 const vec2 d = vec2(0.0, ONE);
 vec2 b = floor(n), f = smoothstep(vec2(0.0), vec2(ONE), fract(n));
 return mix(mix(rand(b), rand(b + d.yx), f.x), mix(rand(b + d.xy), rand(b + d.yy), f.x), f.y);
}

float fbm(vec2 n) {
 //fbm stands for "Fractal Brownian Motion" https://en.wikipedia.org/wiki/Fractional_Brownian_motion
 float total = 0.0;
 float amplitude = 1.62;
 for (int i = 0; i < 3; i++) {
  total += noise(n) * amplitude;
  n += n;
  amplitude *= 0.51;
 }
 return total;
}

void main() {
 //This is where our shader comes together
 const vec3 c1 = vec3(126.0/255.0, 0.0/255.0, 96.9/255.0);
 //const vec3 c2 = vec3(173.0/255.0, 0.0/255.0, 161.4/255.0);
 vec3 c2 = tint_ink.rgb;
 const vec3 c3 = vec3(0.21, 0.0, 0.0);
 const vec3 c4 = vec3(165.0/255.0, 129.0/255.0, 214.4/255.0);
 const vec3 c5 = vec3(0.12);
 const vec3 c6 = vec3(0.9);
 vec2 pix_pos = (gl_FragCoord.xy - win_pos - center_pos) / resolution.xy - vec2(0.0, 0.51);
 //This is how "packed" the smoke is in our area. Try changing 15.0 to 2.1, or something else
 vec2 p = pix_pos * (ONE + mouse.x / resolution.x * 15.0);
 //The fbm function takes p as its seed (so each pixel looks different) and time (so it shifts over time)
 float q = fbm(p - time * 0.12);
 float speed = 3.9 * time * mouse.y / resolution.y;
 vec2 r = vec2(fbm(p + q + speed - p.x - p.y), fbm(p + q - speed));
 vec3 col = (mix(c1, c2, fbm(p + r)) + mix(c3, c4, r.y) - mix(c5, c6, r.x)) * cos(contrast * pix_pos.y);
 col *= ONE - pix_pos.y;
 if (tex_col_mix != 0.0) {
  vec4 tex = texture2D(texture0, tex_coord0);
  col = mix(tex.rgb, col, tex_col_mix);
 }
 gl_FragColor = vec4(col, (alpha + tint_ink.a) / 2.01);
}
