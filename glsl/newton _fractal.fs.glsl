// Smooth_Newton_Fractal_v4.glsl              
// v1 Newton Fractal 1-z^3 by @hintz
// v2 http://glslsandbox.com/e#39430.1   HSV2RGB changed                     
// v3 http://glslsandbox.com/e#42786.3   2017-10-02 @hintz
//    added smooth iteration value, which is needed for future 3D conversion.
// v4 rotate2d(angle), z4next(z) and z5next added 
//    
// What about to go 3D like http://www.josleys.com/show_gallery.php?galid=338 ?
uniform float alpha;
uniform float tex_col_mix;
uniform float time;
uniform vec2 win_pos;
uniform vec2 resolution;

mat2 rotate2d (float angle)    // create 2d rotation matrix
{
 float ca = cos(angle);
 float sa = sin(angle);
 return mat2(ca, -sa, sa, ca);
}

// for pretty colors: Hue-Saturation-Value to Red-Green-Blue
vec3 hsvToRgb(vec3 hsv)
{
 return ((clamp(abs(fract(hsv.x + vec3(0.,2./3.,1./3.))*2.-1.)*3.-1.,0.,1.)-1.)*hsv.y+1.)*hsv.z;
}

// complex number multiplication: a * b
vec2 mul(vec2 a, vec2 b)
{
 return vec2(a.x*b.x - a.y*b.y, a.y*b.x + a.x*b.y);
}

// complex number division: a / b 
vec2 div(vec2 a, vec2 b)
{
 return vec2((a.x*b.x + a.y*b.y) / (b.x*b.x + b.y*b.y), (a.y*b.x - a.x*b.y) / (b.x*b.x + b.y*b.y));
}

//     1 - z^3
// z - -------
//     3 * z^2
vec2 z3next(vec2 z)
{
 vec2 z2 = mul(z,z);
 vec2 z3 = mul(z2,z);
 return z - div(vec2(1.0,0.0)+z3, 3.0*z2);
}

//     1 - z^4
// z - -------
//     4 * z^3
vec2 z4next(vec2 z)
{
 vec2 z2 = mul(z,z);
 vec2 z3 = mul(z2,z);
 vec2 z4 = mul(z2,z2);
 return z - div(vec2(1.0,0.0)+z4, 4.0*z3);
}

//     1 - z^5
// z - -------
//     5 * z^4
vec2 z5next(vec2 z)
{
 vec2 z2 = mul(z,z);
 vec2 z3 = mul(z2,z);
 vec2 z4 = mul(z2,z2);
 vec2 z5 = mul(z3,z2);
 return z - div(vec2(1.0,0.0)+z5, 5.0*z4);
}


vec2 newtonFractal(vec2 z)
{
 for (int n=0; n<1000; n++) {
  vec2 old = z;
  //--- please select function ---
  //z = z3next(z);
  //z = z4next(z);
  z = z5next(z);
  float d = length(z - old);
  if (d < 0.01) {
   float u = float(n) + log2(log(0.01) / log(d));
   return vec2(z.x + z.y + time*0.1, u*0.03);
  }
 }
 return z;
}

void main(void)
{
  // shader compile error on Android if these variables get moved to module level (after uniform declarations).
  float deltax = 12.0 + sin(time*0.4) * 10.0;   // scale
  float deltay = resolution.y / resolution.x * deltax;
  float theta = time*0.1;         // rotation speed

  vec2 uv = vec2(deltax,deltay) * ((gl_FragCoord.xy - win_pos) / resolution.xy - 0.5);
  //vec2 uv = (gl_FragCoord.xy - win_pos - resolution.xy*0.5)/min(resolution.x, resolution.y)*deltax;
  uv *= rotate2d (theta);
  vec2 results = newtonFractal(uv);  // calculate newton fractal
  vec3 col = hsvToRgb(vec3(results.x + results.y, 0.8, 1.0 - results.y));
	
  if (tex_col_mix != 0.0) {
   vec4 tex = texture2D(texture0, tex_coord0);
   col = mix(tex.rgb, col, tex_col_mix);
  }
  gl_FragColor = vec4(col, alpha);
}
