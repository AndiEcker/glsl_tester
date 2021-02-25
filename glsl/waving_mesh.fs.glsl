uniform float alpha;
uniform float contrast;
uniform float tex_col_mix;
uniform float time;
uniform vec2 win_pos;
uniform vec2 resolution;
uniform vec4 tint_ink;

void main(void)
{
 vec2 uPos = ((gl_FragCoord.xy - win_pos) / resolution.xy);
 uPos.x -= 0.95;
 uPos.y -= 0.95;
 vec3 color = tint_ink.rgb;  // vec3(0.0);
 float vertColor = 0.0;
 float t = time * (0.9);
 for (float i = 0.0; i < 15.0; i++) {
  float j = i / 10.0;
  uPos.y += sin((uPos.x + j) * (contrast + 2.1) + t + contrast / 2.4) * 0.01;
  float fTempY = abs(1.0 / (uPos.y + j) / 500.0);
  color += vec3(fTempY * (15.9 - contrast) / 10.0, fTempY * contrast / 4.5, pow(fTempY, 0.99) * 1.9);
  uPos.x += sin((uPos.y + j) * (contrast + 2.1) + t + 2.4 / contrast) * 0.01;
  float fTempX = abs(1.0 / (uPos.x + j) / 190.0);
  color += vec3( fTempX * contrast / 4.5);
 }
 vec4 color_final = vec4(color, alpha);
 if (tex_col_mix != 0.0) {
  vec4 tex = texture2D(texture0, tex_coord0);
  color_final = mix(tex, color_final, tex_col_mix);
 }
 gl_FragColor = color_final;
}
