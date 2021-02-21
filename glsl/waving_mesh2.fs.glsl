// Original shader from: https://www.shadertoy.com/view/wdVBWd, https://twitter.com/gam0022/status/1339584625929175042
$HEADER$

uniform float alpha;
uniform float tex_col_mix;
uniform float time;
uniform vec2 win_pos;
uniform vec2 resolution;
uniform vec4 tint_ink;

void main(void)
{
 vec2 p = (gl_FragCoord.xy - win_pos) / min(resolution.x, resolution.y) * 8.;
 float a = length(p);
 a += 6.*time*smoothstep(0.10  ,0.20001,length(p-vec2(7.0,4.0))*.06+0.08*sin(time)+0.06);
 p += 0.08*tan(a)*cos(a);
 vec4 col = tint_ink * mod(floor(p.x)+floor(p.y),2.1) * (2.+sin(a+3.0)) + 0.1;
 col.a = alpha;
 if (tex_col_mix != 0.0) {
  vec4 tex = texture2D(texture0, tex_coord0);
  col = mix(tex, col, tex_col_mix);
 }
 gl_FragColor = col;
}
