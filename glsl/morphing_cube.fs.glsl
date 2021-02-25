uniform float alpha;
uniform float tex_col_mix;
uniform float time;
uniform vec2 win_pos;
uniform vec2 resolution;
uniform vec4 tint_ink;

#define EPS 0.001

mat2 rotate2d (float angle)    // create 2d rotation matrix
{
 float ca = cos(angle);
 float sa = sin(angle);
 return mat2(ca, -sa, sa, ca);
}

float sdSphere(vec3 p, float r) {
 return length(p) - r;
}

float map(vec3 p) {
 float r = 8.0;
 float d = sdSphere(p, r);
 for (int i = 0; i < 9; i++) {
  p.xy *= rotate2d(time * 0.2);
  p.yz *= rotate2d(time * 0.1);
  p.zx *= rotate2d(time * 0.3);
  p = abs(p) - r*.33;
  r /= 1.5;
  d = min(d, sdSphere(p, r));
 }
 // d = sdSphere(p, r);
 return d;
}

vec3 getNormal(vec3 p) {
 const vec2 eps = vec2(EPS, 0);
 float d = map(p);
 return normalize(vec3(map(p + eps.stt) - d, map(p + eps.tst) - d, map(p + eps.tts) - d));
}

void main( void ) {
 vec2 pos =   ((gl_FragCoord.xy - win_pos) * 2.0 - resolution) / min(resolution.x, resolution.y)*26.;
 vec3 ro = vec3(pos, -50);
 vec3 rd = vec3(0, 0, 1);
 vec3 light = normalize(vec3(1, 1, -1));
 float dist = 0.0;
 float bright = 0.0;
 for (int i = 0; i < 50; i++) {
  vec3 p = ro + rd * dist;
  float d = map(p);
  if (d < EPS) {
   bright = max(dot(light, getNormal(p)), 0.1);
   break;
  }
  dist += d;
 }
 //gl_FragColor = vec4(vec3(1,1,2) * bright, alpha);
 vec4 col = vec4(tint_ink.rgb * bright, alpha);
  if (tex_col_mix != 0.0) {
   vec4 tex = texture2D(texture0, tex_coord0);
   col = mix(tex, col, tex_col_mix);
  }
 gl_FragColor = col;
}
