// Original shader from: https://www.shadertoy.com/view/wl3fR7
// License CC0: Slicing a 4D apollian
// Was experimenting with slicing 3D fractals in 2D. Naturally I wondered how it looks if we +1 dimension
// Based upon: https://www.shadertoy.com/view/4ds3zn
uniform float alpha;
uniform float tex_col_mix;
uniform float time;
uniform vec2 win_pos;
uniform vec2 resolution;

#define PI  3.141592654

const int max_iter = 130;
const vec3 bone = vec3(0.89, 0.855, 0.788);

void rot(inout vec2 p, float a) {
  float c = cos(a);
  float s = sin(a);
  p = vec2(c*p.x + s*p.y, -s*p.x + c*p.y);
}

float box(vec3 p, vec3 b) {
  vec3 q = abs(p) - b;
  return length(max(q,0.0)) + min(max(q.x,max(q.y,q.z)),0.0);
}

float apollian(vec4 p, float s) {
  float scale = 1.0;

  for(int i=0; i<7; ++i) {
    p = -1.0 + 2.0*fract(0.5*p+0.5);
    float r2 = dot(p,p);
    float k = s/r2;
    p *= k;
    scale *= k;
  }
  return 0.45*abs(p.y)/scale;
}

float df(vec3 p) { 
  vec4 p4 = vec4(p, 0.125);
  float tm = 0.1*time;
  rot(p4.xw, tm*sqrt(0.5));
  rot(p4.yw, tm*sqrt(0.4));
  rot(p4.zw, tm*sqrt(0.3));
  float d1 = apollian(p4, 1.5);
  float db = box(p - vec3(0.0, 0.5, 0.0), vec3(0.75,1.0, 0.75)) - 0.5;
  float dp = p.y;
  return max(d1, db); 
}

float intersect(vec3 ro, vec3 rd, out int iter) {
  float res;
  float t = 0.2;
  iter = max_iter;
    
  for(int i = 0; i < max_iter; ++i) {
    vec3 p = ro + rd * t;
    res = df(p);
    if(res < 0.0003 * t || res > 20.) {
      iter = i;
      break;
    }
    t += res;
  }
    
  if(res > 20.) t = -1.;
  return t;
}

float ambientOcclusion(vec3 p, vec3 n) {
  float stepSize = 0.012;
  float t = stepSize;
  float oc = 0.0;

  for(int i = 0; i < 12; i++) {
    float d = df(p + n * t);
    oc += t - d;
    t += stepSize;
  }
  return clamp(oc, 0.0, 1.0);
}

vec3 normal(in vec3 pos) {
  vec3  eps = vec3(.001,0.0,0.0);
  vec3 nor;
  nor.x = df(pos+eps.xyy) - df(pos-eps.xyy);
  nor.y = df(pos+eps.yxy) - df(pos-eps.yxy);
  nor.z = df(pos+eps.yyx) - df(pos-eps.yyx);
  return normalize(nor);
}

vec3 lighting(vec3 p, vec3 rd, int iter) {
  vec3 n = normal(p);
  float fake = float(iter)/float(max_iter);
  float fakeAmb = exp(-fake*fake*9.0);
  float amb = ambientOcclusion(p, n);

  vec3 col = vec3(mix(1.0, 0.125, pow(amb, 3.0)))*vec3(fakeAmb)*bone;
  return col;
}

vec3 post(vec3 col, vec2 q) {
  col=pow(clamp(col,0.0,1.0),vec3(0.65)); 
  col=col*0.6+0.4*col*col*(3.0-2.0*col);  // contrast
  col=mix(col, vec3(dot(col, vec3(0.33))), -0.5);  // saturation
  col*=0.5+0.5*pow(19.0*q.x*q.y*(1.0-q.x)*(1.0-q.y),0.7);  // vignetting
  return col;
}

void main(void) {
  vec2 q = (gl_FragCoord.xy - win_pos) / resolution.xy;
  vec2 uv = -1.0 + 2.0*q;
  uv.y += 0.225;
  uv.x*=resolution.x/resolution.y;
    
  vec3 la = vec3(0.0, 0.0, 0.0); 
  vec3 ro = vec3(-4.0, 1., -0.0);
  rot(ro.xz, 2.0*PI*time/120.0);
  vec3 cf = normalize(la-ro); 
  vec3 cs = normalize(cross(cf,vec3(0.0,1.0,0.0))); 
  vec3 cu = normalize(cross(cs,cf)); 
  vec3 rd = normalize(uv.x*cs + uv.y*cu + 3.0*cf);  // transform from view to world

  vec3 bg = mix(bone*0.5, bone, smoothstep(-1.0, 1.0, uv.y));
  vec3 col = bg;

  vec3 p=ro; 

  int iter = 0;
  
  float t = intersect(ro, rd, iter);
    
  if(t > -0.5) {
    p = ro + t * rd;
    col = lighting(p, rd, iter); 
    col = mix(col, bg, 1.0-exp(-0.001*t*t));
  }

  col=post(col, q);
  if (tex_col_mix != 0.0) {
   vec4 tex = texture2D(texture0, tex_coord0);
   col = mix(tex.rgb, col, tex_col_mix);
  }
  gl_FragColor=vec4(col, alpha);
}
