uniform float alpha;
uniform float tex_col_mix;
uniform float time;
uniform vec2 win_pos;
uniform vec2 resolution;

void main( void ) {
 vec2 res = resolution.xy;
 vec2 p = 2.*(gl_FragCoord.xy - win_pos - res/2.) / res.y;
 float r;
 vec3 col = vec3(0.);
 const float I = 15.;
 for(float i=1.; i<=I; i++) {
  if(length(p)<1.) {
   r = cos(time*.2+.3*i)/2.;
   if(p.x<2.*r) {
    p.x -= r-.5;
    p /= r+.5;
   } else {
    p.x -= r+.5;
    p /= r-.5;
   }
   col.r = i/(I*p.x);
   col.b = p.x-r;
   col.b *= 0.5;
  }
 }
 if (tex_col_mix != 0.0) {
  vec4 tex = texture2D(texture0, tex_coord0);
  col = mix(tex.rgb, col, tex_col_mix);
 }
 gl_FragColor = vec4(col, alpha);
}
