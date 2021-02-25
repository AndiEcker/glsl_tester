uniform float alpha;
uniform float tex_col_mix;
uniform float time;
uniform vec2 win_pos;
uniform vec2 resolution;
uniform vec4 tint_ink;
uniform float contrast;   // orbit distance

float waveLength = 200.;

void main( void ) {
 vec2 pix_pos = (gl_FragCoord.xy - win_pos) / resolution;
 vec2 p1 = (vec2(sin(time), cos(time))*contrast/39.6)+0.5;
 vec2 p2 = (vec2(sin(time+3.142), cos(time+3.142))*contrast/39.6)+0.5;
 float d1 = 1.-length(pix_pos - p1);
 float d2 = 1.-length(pix_pos - p2);
 float wave1 = sin(d1*waveLength+(time*5.))*0.5 + 0.5 * (((d1 - 0.5) * 2.) + 0.5);
 float wave2 = sin(d2*waveLength+(time*5.))*0.5 + 0.5 * (((d1 - 0.5) * 2.) + 0.5);
 float c = d1 > 0.99 || d2 > 0.99 ? 1. : 0.;
 vec4 col = (vec4(c + wave1*wave2,c,c,alpha) + tint_ink) / 2.0;
 if (tex_col_mix != 0.0) {
  vec4 tex = texture2D(texture0, tex_coord0);
  col = mix(tex, col, tex_col_mix);
 }
 gl_FragColor = col;
}
