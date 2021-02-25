uniform float alpha;
uniform float contrast;
uniform float tex_col_mix;
uniform float time;
uniform vec2 center_pos;
uniform vec2 mouse;         // intensity, granularity
uniform vec2 win_pos;
uniform vec2 resolution;
uniform vec4 tint_ink;

#define TAU 6.283185307182
#define MAX_ITER 15

void main( void ) {
 float t = time * 0.27;
 // uv should be the 0-1 uv of texture...
 vec2 xy = (gl_FragCoord.xy - win_pos - center_pos) / resolution.yy;
 vec2 uv = vec2(atan(xy.y , xy.x) * 4.000000001 / TAU, log(length(xy)) * (0.21 + mouse.y / resolution.y) - time / 20.1);
 vec2 p = mod(uv*TAU, TAU)-270.0;
 float c = 10.2 - 3.0 * contrast;
 float intensity = 0.0015 + mouse.x / resolution.x / 333.3;  //.0042;

 vec2 i = p;
 for (int n = 0; n < MAX_ITER; n++) {
  float t = t * (1.02 - (3.6 / float(n+1)));
  i = p + vec2(cos(t - i.x) + sin(t + i.y), sin(t - i.y) + cos(t + i.x));
  c += 0.999999/length(vec2(p.x / (sin(i.x+t)/intensity),p.y / (cos(i.y+t)/intensity)));
 }
 c /= float(MAX_ITER);
 c = 1.26-pow(c, 5.01);
 vec3 colour = vec3(pow(abs(c), 8.01));
 colour = clamp((colour + tint_ink.rgb) / 2.01, 0.0, 0.99);

 if (tex_col_mix != 0.0) {
  vec4 tex = texture2D(texture0, tex_coord0);
  colour = mix(tex.rgb, colour, tex_col_mix);
 }
 gl_FragColor = vec4(colour, (alpha + tint_ink.a) / 2.00001);
}
