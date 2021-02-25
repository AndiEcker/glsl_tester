uniform float alpha;
uniform float tex_col_mix;
uniform float time;
uniform vec2 win_pos;
uniform vec2 resolution;

void main( void ) {
  vec2 st = (gl_FragCoord.xy - win_pos) / resolution;
  vec3 col = vec3(st.x, st.y, sin(time / 9.0));
  if (tex_col_mix != 0.0) {
   vec4 tex = texture2D(texture0, tex_coord0);
   col = mix(tex.rgb, col, tex_col_mix);
  }
  gl_FragColor = vec4(col, alpha);
}
