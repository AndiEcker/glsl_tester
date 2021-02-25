// Original shader from: https://www.shadertoy.com/view/Wl3fzM
// License CC0: Apollian with a twist - Playing around with apollian fractal
uniform float alpha;
uniform float tex_col_mix;
uniform float time;
uniform vec2 win_pos;
uniform vec2 resolution;

// Emulate some GLSL ES 3.x
float tanh(float x) {
  float ex = exp(2.0 * x);
  return ((ex - 1.) / (ex + 1.));
}

#define PI              3.141592654
#define TAU             (2.0*PI)

vec3 hsv2rgb(vec3 c) {
  const vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
  vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
  return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
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
  return abs(p.y)/scale;
}

float weird(vec2 p) {
  float z = 4.0;
  float tm = 0.1*time;
  p *= mat2(cos(tm), sin(tm), -sin(tm), cos(tm));
  tm = 0.2*time;
  vec4 off = vec4(0.5*(0.5 + 0.5*sin(tm*sqrt(3.0))),
                  0.5*(0.5 + 0.5*sin(tm*sqrt(1.5))),
                  0.5*(0.5 + 0.5*sin(tm*sqrt(2.0))),
                  0.0);
  vec4 pp = vec4(p.x, p.y, 0.0, 0.0)+off;
  pp.w = 0.125*(1.0-tanh(length(pp.xyz)));
  pp.yz *= mat2(cos(tm), sin(tm), -sin(tm), cos(tm));
  tm = tm*sqrt(0.5);
  pp.xz *= mat2(cos(tm), sin(tm), -sin(tm), cos(tm));
  pp /= z;
  float d = apollian(pp, 1.2);
  return d*z;
}

float df(vec2 p) {
  const float zoom = 0.5;
  p /= zoom;
  float d0 = weird(p);
  return d0*zoom;
}

vec3 color(vec2 p) {
  float aa   = 2.0/resolution.y;
  const float lw = 0.0235;
  const float lh = 1.25;

  const vec3 lp1 = vec3(0.5, lh, 0.5);
  const vec3 lp2 = vec3(-0.5, lh, 0.5);

  float d = df(p);

  float b = -0.125;
  float t = 10.0;

  vec3 ro = vec3(0.0, t, 0.0);
  vec3 pp = vec3(p.x, 0.0, p.y);

  vec3 rd = normalize(pp - ro);

  vec3 ld1 = normalize(lp1 - pp);
  vec3 ld2 = normalize(lp2 - pp);

  float bt = -(t-b)/rd.y;
  
  vec3 bp   = ro + bt*rd;
  vec3 srd1 = normalize(lp1-bp);
  vec3 srd2 = normalize(lp2-bp);
  float bl21= dot(lp1-bp, lp1-bp);
  float bl22= dot(lp2-bp, lp2-bp);

  float st1= (0.0-b)/srd1.y;
  float st2= (0.0-b)/srd2.y;
  vec3 sp1 = bp + srd1*st1;
  vec3 sp2 = bp + srd2*st1;

  float bd = df(bp.xz);
  float sd1= df(sp1.xz);
  float sd2= df(sp2.xz);

  vec3 col  = vec3(0.0);
  const float ss =15.0;
  
  col       += vec3(1.0, 1.0, 1.0)*(1.0-exp(-ss*(max((sd1+0.0*lw), 0.0))))/bl21;
  col       += vec3(0.5)*(1.0-exp(-ss*(max((sd2+0.0*lw), 0.0))))/bl22;
  float l   = length(p);
  float hue = fract(0.75*l-0.3*time)+0.3+0.15;
  float sat = 0.75*tanh(2.0*l);
  vec3 hsv  = vec3(hue, sat, 1.0);
  vec3 bcol = hsv2rgb(hsv);
  col       *= (1.0-tanh(0.75*l))*0.5;
  col       = mix(col, bcol, smoothstep(-aa, aa, -d));  
  col       += 0.5*sqrt(bcol.zxy)*(exp(-(10.0+100.0*tanh(l))*max(d, 0.0)));

  return col;
}

vec3 postProcess(vec3 col, vec2 q)  {
  col=pow(clamp(col,0.0,1.0),vec3(1.0/2.2)); 
  col=col*0.6+0.4*col*col*(3.0-2.0*col);  // contrast
  col=mix(col, vec3(dot(col, vec3(0.33))), -0.4);  // saturation
  col*=0.5+0.5*pow(19.0*q.x*q.y*(1.0-q.x)*(1.0-q.y),0.7);  // vignetting
  return col;
}

void main(void) {
  vec2 q = (gl_FragCoord.xy - win_pos) / resolution;
  vec2 p = -1. + 2. * q;
  p.x *= resolution.x / resolution.y;
  vec3 col = color(p);
  col = postProcess(col, q);
  
  if (tex_col_mix != 0.0) {
   vec4 tex = texture2D(texture0, tex_coord0);
   col = mix(tex.rgb, col, tex_col_mix);
  }
  gl_FragColor = vec4(col, alpha);
}
