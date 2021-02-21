$HEADER$

uniform float alpha;
uniform float contrast;         // red
uniform float tex_col_mix;      // relabeled
uniform float time;
uniform vec2 center_pos;        // green, (unused)
uniform vec2 mouse;             // (unused), blue
uniform vec2 win_pos;
uniform vec2 resolution;
uniform vec4 tint_ink;          // (unused)

void main(void)
{
  //vec2 pix_pos = (frag_modelview_mat * gl_FragCoord).xy - win_pos;
  vec2 pix_pos = gl_FragCoord.xy - win_pos;

  vec4 col = vec4(contrast, center_pos.x / resolution.x, mouse.y / resolution.y, fract(time));  // REPLACE ME

  if (tex_col_mix != 0.0) {
    vec4 tex = texture2D(texture0, tex_coord0);
    col = mix(tex, col, tex_col_mix);
  }

  gl_FragColor = vec4(col.rgb, col.a * sqrt(alpha));
}
