// Original shader from: https://www.shadertoy.com/view/Wt3BzM
// Created by inigo quilez - iq/2013
// License Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License.
// More info here:  http://www.iquilezles.org/www/articles/lyapunovfractals/lyapunovfractals.htm
uniform float alpha;
uniform float tex_col_mix;
uniform float time;
uniform vec2 win_pos;
uniform vec2 resolution;
uniform vec4 tint_ink;

vec3 calc( in vec2 p ) {
 float x = 0.5;
 float h = 0.0;
 for( int i=0; i<9; i++ ) {
  x = p.x*x*(1.0-x+sin(time)/100.);
  h += log2(abs(p.x*(1.0-2.0*x)));
  x = p.x*x*(1.0-x+sin(time*2.)/100.);
  h += log2(abs(p.x*(1.0-2.0*x)));
  x = p.x*x*(1.0-x);
  h += log2(abs(p.x*(1.0-2.0*x)));
  x = p.x*x*(1.0-x);
  h += log2(abs(p.x*(1.0-2.0*x)));
  x = p.y*x*(1.0-x);
  h += log2(abs(p.y*(1.0-2.0*x)));
  x = p.y*x*(1.0-x+sin(time/2.)/50.);
  h += log2(abs(p.y*(1.0-2.0*x)));
  x = p.y*x*(1.0-x);
  h += log2(abs(p.y*(1.0-2.0*x)));
  x = p.y*x*(1.0-x+sin(time*1.5)/100.);
  h += log2(abs(p.y*(1.0-2.0*x)));
 }
 h /= 290.0;
 vec3 col = vec3(0.0);
 if( h<0.0 ) {
  h = abs(h);
  //col = 1.0*sin(vec3(0.9,0.5,0.0) + 6.8*h);
  col = 1.0*sin(tint_ink.rgb + 6.8*h);
 }
 return col;
}

void main(void) {
  vec3 col = calc(vec2(2.2, 3.4) + 1.5*(gl_FragCoord.xy - win_pos) / resolution.x);
  if (tex_col_mix != 0.0) {
   vec4 tex = texture2D(texture0, tex_coord0);
   col = mix(tex.rgb, col, tex_col_mix);
  }
  gl_FragColor = vec4(col, alpha);
}
