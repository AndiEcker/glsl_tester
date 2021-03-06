uniform float alpha;
uniform float tex_col_mix;
uniform float time;
uniform vec2 win_pos;
uniform vec2 resolution;

#define PI 3.14159265359

void main(void) {
  vec2 st = (gl_FragCoord.xy - win_pos - resolution.xy * 0.5) / min(resolution.y, resolution.x) * 1.2;
  float u_time = time*0.25;

  // cartesian to polar coordinates
  float radius = length(st);
  float a = atan(st.y, st.x);

  // Repeat side according to angle
  float sides = 9.;
  float ma = mod(a, PI * 2.0 / sides);
  ma = abs(ma - PI / sides);

  // polar to cartesian coordinates
  st = radius * vec2(cos(ma), sin(ma));

  st += cos(log2(u_time) + radius * PI - ma);
  st = fract(st + u_time);
  st.x = smoothstep(0.0, 1.0, st.x);
  st.y = smoothstep(1.0, 0.0, st.y);
  vec4 color = vec4(st.x, st.y, sin(u_time / (radius + ma)), alpha);
  color = min(color, smoothstep(0.55, 0.5,	radius));
  if (tex_col_mix != 0.0) {
   vec4 tex = texture2D(texture0, tex_coord0);
   color = mix(tex, color, tex_col_mix);
  }
  gl_FragColor = color;
}
