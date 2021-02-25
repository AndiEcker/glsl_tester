uniform float alpha;
uniform float contrast;  // speed
uniform float tex_col_mix;
uniform float time;
uniform vec2 center_pos;
uniform vec2 mouse;  // intensity, granularity
uniform vec2 win_pos;
uniform vec2 resolution;
uniform vec4 tint_ink;

#define TAU 6.283185307182
#define MAX_ITER 15

void main( void ) {
 float t = time*contrast + 23.01;
 // uv should be the 0-1 uv of texture...
 vec2 xy = (gl_FragCoord.xy - win_pos - center_pos) / resolution.yy; // - vec2(0.9);
 vec2 uv = vec2(atan(xy.y, xy.x) * 6.99999 / TAU, log(length(xy)) * (0.21 + mouse.y / resolution.y) - time * 0.21);
 vec2 p = mod(uv*TAU, TAU)-250.02;
 vec2 i = vec2(p);
 float c = 8.52;
 float intensity = 0.0015 + mouse.x / resolution.x / 333.3;  // = .005;

 for (int n = 0; n < MAX_ITER; n++) {
   float t = t * (1.02 - (3.498 / float(n+1)));
   i = p + vec2(cos(t - i.x) + sin(t + i.y), sin(t - i.y) + cos(t + i.x));
   c += 1.0/length(vec2(p.x / (sin(i.x+t)/intensity),p.y / (cos(i.y+t)/intensity)));
 }
 c /= float(MAX_ITER);
 c = 1.272 - pow(c, 6.42);
 vec3 colour = vec3(pow(abs(c), 8.01));
 colour = clamp(colour + tint_ink.rgb, 0.0, 0.999999);
 if (tex_col_mix != 0.0) {
  vec4 tex = texture2D(texture0, tex_coord0);
  colour = mix(tex.rgb, colour, tex_col_mix);
 }
 gl_FragColor = vec4(colour, (alpha + tint_ink.a) / 2.00001);
 }
