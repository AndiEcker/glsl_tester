uniform float alpha;
uniform float tex_col_mix;
uniform float time;
uniform vec2 win_pos;
uniform vec2 resolution;

#define rot(a) mat2(cos(a), sin(a), -sin(a), cos(a))

float scale;

float map(vec3 p) {
 p.z -= time * -3.0;
 p.xy = abs(p.xy) - 2.0;
 if (p.x < p.y) p.xy = p.yx;
 p.z = mod(p.z, 4.0) - 2.0;

 p.x -= 4.+sin(time+p.z*0.2+p.y*.6)*0.5;
 p = abs(p);
 float s = 2.0;
 vec3 offset = p*1.1;
 for (float i = 0.0; i < 5.0; i++) {
  p = 1.0 - abs(p - 1.0);
  float r = -7.5 * clamp(0.38 * max(1.6 / dot(p, p), 1.0), 0.0, 1.0);
  s *= r;
  p *= r;
  p += offset;
 }
 s = abs(s);
 scale = s;
 float a = 100.0;
 p -= clamp(p, -a, a);
 return length(p) / s;
}

void main( void ) {
 gl_FragColor.w = alpha;  // 1.0;
 vec2 uv = ((gl_FragCoord.xy - win_pos) - 0.5 * resolution) / resolution.y;

 vec3 rd = normalize(vec3(uv, 1.0));
 vec3 p = vec3(0.0, 0.0, -3.0);
 for (int i = 1; i < 100; i++) {
   float d = map(p);
   p += rd * d;
   if (d < 0.001) {
     vec3 col = mix(vec3(1), cos(vec3(1.0, 9.0, 3.0) + log2(scale)) * 0.5 + 0.5, 0.5) * 10.0 / float(i);
     if (tex_col_mix != 0.0) {
      vec4 tex = texture2D(texture0, tex_coord0);
      col = mix(tex.rgb, col, tex_col_mix);
     }
     gl_FragColor.rgb = col;
     gl_FragColor.a = alpha;
     break;
   }
 }
}
