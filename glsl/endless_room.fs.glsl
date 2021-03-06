uniform float alpha;
uniform float contrast;  // room height
uniform float tex_col_mix;
uniform float time;
uniform vec2 resolution;
uniform vec2 win_pos;
uniform vec4 tint_ink;

void main(void) {
 vec2 centered_coord = (2.*(gl_FragCoord.xy - win_pos) - resolution.xy) / resolution.y;
 float dist_from_center_y = (.21 + contrast) * length(centered_coord.y);
 float u = 6./dist_from_center_y + time*4.;
 float v = (6./dist_from_center_y) * centered_coord.x;
 float grid = (1. - pow(sin(u) + 1., .1) + (1.0 - pow(sin(v) + 1., .1))) * dist_from_center_y * 3.;
 vec3 col = vec3(grid)*tint_ink.rgb;
 if (tex_col_mix != 0.0) {
  vec4 tex = texture2D(texture0, tex_coord0);
  col = mix(tex.rgb, col, tex_col_mix);
 }
 gl_FragColor = vec4(col, alpha);
}
