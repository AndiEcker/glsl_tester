// AlgebraicSurface_Caley: ray-marching algebraic surfaces with orthographic projection by 焦堂生 jiaotangsheng@126.com
// Idea from RealSurf (http://realsurf.informatik.uni-halle.de/)
uniform float alpha;
uniform float contrast;
uniform float tex_col_mix;
uniform float time;
uniform vec2 mouse;
uniform vec2 win_pos;
uniform vec2 resolution;
uniform vec4 tint_ink;

const float R = 4.;
const float oo = 1000.;
const int IT = 10;

vec3 turbo(float x) {
 const vec4 kRedVec4 = vec4(0.13572138, 4.61539260, -42.66032258, 132.13108234);
 const vec4 kGreenVec4 = vec4(0.09140261, 2.19418839, 4.84296658, -14.18503333);
 const vec4 kBlueVec4 = vec4(0.10667330, 12.64194608, -60.58204836, 110.36276771);
 const vec2 kRedVec2 = vec2(-152.94239396, 59.28637943);
 const vec2 kGreenVec2 = vec2(4.27729857, 2.82956604);
 const vec2 kBlueVec2 = vec2(-89.90310912, 27.34824973);
 x = fract(x);
 vec4 v4 = vec4(1.0, x, x*x, x*x*x);
 vec2 v2 = v4.zw * v4.z;
 return vec3(
  dot(v4, kRedVec4)   + dot(v2, kRedVec2),
  dot(v4, kGreenVec4) + dot(v2, kGreenVec2),
  dot(v4, kBlueVec4)  + dot(v2, kBlueVec2));
}

float F(vec3 v) 
{
 float x = v.x;
 float y = v.y;
 float z = v.z;
 return x*x*y + z*y*y + x*y*z + contrast*x*y*z - 1.;
}

vec3 dF(vec3 v) {
 float x = v.x;
 float y = v.y;
 float z = v.z;
 return vec3(2.*x+contrast*y*z, 2.*y+contrast*x*z, 2.*z+contrast*x*y);
}

float SR(vec3 v) {
 return dot(v,v) - R*R;
}

vec3 ray(vec2 pos, float t) {
 float th = time*.15-4.*mouse.x/resolution.x;
 float phi = time*.17+3.*mouse.y/resolution.y;
 return mat3(vec3(cos(th),0.,sin(th)), vec3(0.,1.,0.), vec3(-sin(th),0.,cos(th)))
      * mat3(vec3(1.,0,0.), vec3(0,cos(phi),sin(phi)), vec3(0,-sin(phi),cos(phi)))
      * (vec3(pos,6.) + vec3(0.,0.,-1.) * t);
}

float eval(vec4 poly, float t) {
 return (((poly[3])*t + poly[2])*t + poly[1])*t + poly[0]; // horner scheme
}

vec4 d(vec4 p) {
 vec4 r = vec4(0.);
 for(int i=0; i<3; i++) {
  r[i] = p[i+1]*float(i+1);
 }
 return r;
}

float bisect(vec4 p, float l, float u, float def) {
 if(l==u) return def;

 float lv = eval(p, l);
 float uv = eval(p, u);
 if(lv*uv>=0.) return def;

 float m, mv;
 for(int i=0; i<IT; i++) {
  m = (l+u)/2.;
  mv = eval(p, m);
  if(lv*mv>0.) {
   l = m;
   //lv = mv;
  } else {
   u = m;
  }
 }
 return m;
}

float first_root(vec4 poly, float l, float u) { //finds first root of poly in interval [l, u]
 vec4 p[4];   //derivatives
 p[3] = poly; //deg 3
 for(int i=2; i>=1; i--) {
  p[i] = d(p[i+1]);
 }
 vec4 roots = vec4(u); //always consider u as root
 vec4 old_r = vec4(u);
 for(int i=1; i<4; i++) { //i: degree
  roots[0] = bisect(p[i], l, old_r[0], l);
  for(int j=1; j<4; j++) {
   if(j<i) roots[j] = bisect(p[i], old_r[j-1], old_r[j], roots[j-1]);
  }
  old_r = roots;
 }
 for(int i=0; i<4; i++) {
  if(roots[i]!=l && roots[i]!=u) return roots[i];
  //if(abs(eval(poly,roots[i]))<.01) return roots[i];
 }
 return oo;
}

mat4 A = mat4( //polynomial interpolation for base points 0, 5, 10, 15 (better use chebyshev nodes)
 vec4(  1.000000000000000, -0.366666666666667,  0.040000000000000, -0.001333333333333),
 vec4( -0.000000000000000,  0.600000000000000, -0.100000000000000,  0.004000000000000),
 vec4(  0.000000000000000, -0.300000000000000,  0.080000000000000, -0.004000000000000),
 vec4( -0.000000000000000,  0.066666666666667, -0.020000000000000,  0.001333333333333)
);  //octave: inv(fliplr(vander([0,5,10,15])))'

void main( void ) {
  vec2 pos = ((gl_FragCoord.xy - win_pos) * 2.0 - resolution) / min(resolution.x, resolution.y)*4.;
  //pos.y *= resolution.y/resolution.x;
  vec4 tex = texture2D(texture0, tex_coord0);

  vec4 v1;
  vec4 v2;
  for(int i=0; i<4; i++) {
    vec3 p = ray(pos, 5.*float(i));
    v1[i] = F(p);
    v2[i] = SR(p);
  }
  
  vec4 p1 = A*v1;//interpolate
  vec4 p2 = A*v2;//p2 is quadratic
  float root = oo;
  float D = (p2[1]*p2[1])-4.*p2[2]*p2[0];
  
  if(D>=0.)
    root = first_root(p1, max(0.,(-p2[1]-sqrt(D))/(2.*p2[2])), max(0.,(-p2[1]+sqrt(D))/(2.*p2[2])));

  //gl_FragColor = vec4(0., .0, .25, alpha);
  gl_FragColor = vec4(tint_ink.rgb, alpha);
  
  if(root != oo) {
    vec3 n = normalize(dF(ray(pos,root)));
    
    vec3 l[5]; //position of light
    vec3 c[5]; //color of light
    l[0] = vec3(-1.,1.,0.);
    l[1] = vec3(0.,-1.,1.);
    l[2] = vec3(1.,0.,-1.);
    l[3] = -ray(vec2(.0,.0),-10.);
    l[4] = ray(vec2(.0,.0),-10.);
    
    c[0] = vec3(1.,.6,.3);
    c[1] = vec3(.3,1.,.6);
    c[2] = vec3(.6,.3,1.);
    c[3] = vec3(.9,.3,.0);
    c[4] = vec3(0.,.8,.8);
    
    //gl_FragColor = vec4(0.,0.,0.,alpha);
    vec3 col = tint_ink.rgb;
    for(int i=0; i<5; i++) {
      float illumination = max(0.,dot(normalize(l[i]),n));
      col += pow(illumination*illumination*turbo(illumination * 5.), vec3(2.75)) * 2.75;
    }
    if (tex_col_mix != 0.0) {
      vec4 tex = texture2D(texture0, tex_coord0);
      col = mix(tex.rgb, col, tex_col_mix);
    }
    gl_FragColor = vec4(col, alpha);
  } 
}

