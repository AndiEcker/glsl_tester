uniform float alpha;
uniform float tex_col_mix;
uniform float time;
uniform vec2 win_pos;
uniform vec2 resolution;

void main( void ) {
 vec2 p = 2.*((gl_FragCoord.xy-win_pos) - resolution/2.) / resolution.y;
 float f=0., r;
 const float I = 16.;
 for(float i=1.; i<=I; i++) {
  if(length(p)<1.) {
   r = cos(time*.2 + .3*i)/2.;
   if(p.x < 2.*r) {
    p.x -= r-.5;
    p /= r+.5;
   } else {
    p.x -= r+.5;
    p /= r-.5;
   }
   f = i/I;
  }
 }
 vec3 col = vec3(fract(f), fract(p));
 if (tex_col_mix != 0.0) {
  vec4 tex = texture2D(texture0, tex_coord0);
  col = mix(tex.rgb, col, tex_col_mix);
 }
 gl_FragColor = vec4(col, alpha);
}
