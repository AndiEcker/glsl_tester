// Original shader from: https://www.shadertoy.com/view/wtGyz1
// Code by Flopine / Thanks to wsmind, leon, XT95, lsdlive, lamogui, Coyhot, Alkama,YX, NuSan and slerpy for teaching me
// Thanks LJ for giving me the spark :3, Thanks to the Cookie Collective, which build a cozy and safe environment for me
// and other to sprout :)  https://twitter.com/CookieDemoparty
uniform float alpha;
uniform float tex_col_mix;
uniform float time;
uniform vec2 win_pos;
uniform vec2 resolution;

// Emulate some GLSL ES 3.x
#define round(x) (floor((x) + 0.5))
#define PI acos(-1.)
#define TAY 6.283185    // I know it's TAU but I found that typo funny :3
#define ITER 64.

#define rot(a) mat2(cos(a),sin(a),-sin(a),cos(a))
#define mo(uv,d)uv=abs(uv)-d;if(uv.y>uv.x)uv=uv.yx;
#define crep(p,c,l) p=p-c*clamp(round(p/c),-l,l)
#define cyl(p,r,h) max(length(p.xy)-(r),abs(p.z)-h)
#define dt(speed) fract(time*speed)
#define hash21(x) fract(sin(dot(x,vec2(12.4,33.8)))*1247.4)

struct obj {
  float d;
  vec3 color;
};

obj minobj (obj a, obj b) {
  if (a.d<b.d) return a;
  else return b;
}

void moda (inout vec2 p, float rep) {
  float per = TAY/rep;
  float a = mod(atan(p.y,p.x),per)-per*0.5;
  p = vec2(cos(a),sin(a))*length(p);
}

float box (vec3 p, vec3 c) {
  vec3 q = abs(p)-c;
  return min(0.,max(q.x,max(q.y,q.z)))+length(max(q,0.));
}

float torus( vec3 p, vec2 t ) {
  vec2 q = vec2(length(p.xz)-t.x,p.y);
  return length(q)-t.y;
}

float heightmap (vec2 uv) {
  uv = fract(uv)-.5;
  uv = abs(uv);
  return smoothstep(0.2,0.27,max(uv.x,uv.y*0.7));
}

obj tunnel (vec3 p) {
  vec3 pp = p;
  vec2 tuv = vec2(atan(p.x,p.z)*5.,p.y*0.4);
  float r;
  if (tuv.x > -5. && tuv.x < 20.) r = 10.5-heightmap(tuv)*0.15;
  else r = 10.5;
  float td = -cyl(p.xzy,r,1e10);

  float per = 10.;
  float id = floor(p.y/per);
  p.xz *= rot((TAY/6.)*(id+.5));
  p.y = mod(p.y,per)-per*0.5;
  float holes = -cyl(p,1.5,25.);   
  td = max(holes ,td);
  p.z = abs(p.z)-10.25;
  td = min(td,max(holes,cyl(p,1.8,0.3)));

  return obj(td,vec3(1.));
}

float pipe (vec3 p) {
  float pd = cyl(p.xzy,0.2,1e10);
  float per = 2.;
  p.y = mod(p.y,per)-per*0.5;
  pd = min(pd,cyl(p.xzy,0.25,0.1));

  return pd;
}

obj pipes (vec3 p) {
  moda(p.xz, 6.);
  p.x -= 9.;
  crep(p.z,0.7,2.);
  float psd = pipe(p);
  return obj(psd,vec3(.7,0.,0.));
}

float g1=0.;
float platform (vec3 p) {
  p.xz *= rot(TAY/6.);
  float s = length(p)-.5;
  g1 += 0.1/(0.1+s*s);

  mo(p.xz,vec2(.5));
  float d = box(p,vec3(10.,0.2,1.5));
  crep(p.xz,0.4,vec2(30.,4.));
  d = max(-box(p,vec3(0.2,0.5,0.1)),d);
  d = min(d,s);
  return d;
}

obj platforms (vec3 p) {
  float per = 40.;
  p.y = mod(p.y-per*0.5,per)-per*0.5;
  float pld = platform(p);
  return obj(pld,vec3(0.9,0.1,0.1));
}

float roundpipe (vec3 p) {
  float rpd = torus(p,vec2(10.3,0.2));
  moda(p.xz,18.);
  p.x -= 10.3;
  rpd = min(rpd, cyl(p,0.25,0.1));
  return rpd;
}

obj roundpipes (vec3 p) {
  float per = 20.;
  p.y = mod(p.y,per)-per*0.5;
  return obj(roundpipe(p),vec3(0.9,0.4,0.));
}

obj SDF (vec3 p) {
  p.y -= dt(1./5.)*120.;
  obj so = minobj(tunnel(p),pipes(p)); 
  so = minobj(so,platforms(p));
  so = minobj(so,roundpipes(p));
  return so;
}

vec3 getcam (vec3 ro, vec3 ta, vec2 uv) {
  vec3 f = normalize(ta-ro);
  vec3 l = normalize(cross(vec3(0.,1.,0.),f));
  vec3 u = normalize(cross(f,l));
  return f + l*uv.x + u*uv.y;
}

vec3 getnorm (vec3 p) {
  vec2 eps = vec2(0.01,0.);
  return normalize(SDF(p).d-vec3(SDF(p-eps.xyy).d,SDF(p-eps.yxy).d,SDF(p-eps.yyx).d));
}

float AO (float eps,vec3 n, vec3 p) {
  return SDF(p+eps*n).d/eps;
}

void main(void) {
  vec2 uv = (2.*(gl_FragCoord.xy - win_pos) - resolution.xy) / resolution.y;

  float dither = hash21(uv);
  vec3 ro = vec3(0.3,0.01,-6.), rd=getcam(ro,vec3(.5,-7.,0.),uv),p=ro, col=vec3(0.);
  float shad; bool hit=false; obj O;

  for(float i =0.; i<ITER; i++)
  {
    O = SDF(p);
    if (O.d<0.0001)
    {
      hit=true; shad=i/ITER; break;
    }
    O.d *= 0.5+dither*0.05;
    p += rd*O.d;
  }

  float t = length(ro-p);
  if(hit)
  {
    vec3 n = getnorm(p);
    float ao = AO(0.1,n,p) + AO(0.4,n,p) + AO(0.5,n,p);
    col = O.color;
    col *= (1.-shad);
    col *= ao/3.;
  }
  col = mix(col,vec3(0.,0.05,0.1),1.-exp(-0.001*t*t));
  col += g1*vec3(0.1,0.8,0.2)*0.8;
  col = sqrt(col);
  if (tex_col_mix != 0.0) {
   vec4 tex = texture2D(texture0, tex_coord0);
   col = mix(tex.rgb, col, tex_col_mix);
  }
  gl_FragColor = vec4(sqrt(col),alpha);
}
