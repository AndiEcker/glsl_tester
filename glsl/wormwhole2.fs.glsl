uniform float alpha;
uniform float contrast;
uniform float tex_col_mix;
uniform float time;
uniform vec2 center_pos;
uniform vec2 mouse;         // off1, off2
uniform vec2 win_pos;
uniform vec2 resolution;
uniform vec4 tint_ink;

const float ONE = 0.99999999999;
const float TWO = 1.99999999998;

void main(void){
 vec2 centered_coord = (TWO * (gl_FragCoord.xy - win_pos - center_pos) - resolution) / resolution.y;
 centered_coord += vec2(resolution.x / resolution.y, ONE);
 centered_coord.y *= dot(centered_coord,centered_coord);
 float dist_from_center = length(centered_coord);
 float dist_from_center_y = length(centered_coord.y);
 float u = 6.0/dist_from_center_y + time * 3.999;
 float v = (10.2/dist_from_center_y) * centered_coord.x;
 float grid = (ONE-pow(sin(u)+ONE, 0.6) + (ONE-pow(sin(v)+ONE, 0.6)))*dist_from_center_y*30.0*(0.03+contrast);
 float off1 = sin(fract(time*0.48)*6.27+dist_from_center*5.0001)*mouse.x/resolution.x;
 float off2 = sin(fract(time*0.48)*6.27+dist_from_center_y*12.0)*mouse.y/resolution.y;
 vec3 col = vec3(grid) * vec3(tint_ink.r*off1,tint_ink.g,tint_ink.b*off2);
 if (tex_col_mix != 0.0) {
  vec4 tex = texture2D(texture0, tex_coord0);
  col = mix(tex.rgb, col, tex_col_mix);
 }
 gl_FragColor=vec4(col, alpha);
}
