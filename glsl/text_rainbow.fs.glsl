// Original shader from: https://www.shadertoy.com/view/3lKyzW
// Fork of "cosmos font smooth" by netgrind. https://shadertoy.com/view/Xdjfzw 2021-01-14 00:00:36
uniform float alpha;
uniform float tex_col_mix;
uniform float time;
uniform float contrast;
uniform vec2 win_pos;
uniform vec2 resolution;

#define line1 _ y_ o_ u_ _ a_ r_ e_ _ a_ crlf
#define line2 _ _ r_ a_ i_ n_ b_ o_ w_

// line function, used in k, s, v, w, x, y, z
float line(vec2 p, vec2 a, vec2 b)
{
	vec2 pa = p - a;
	vec2 ba = b - a;
	float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0);
    return length(pa - ba * h);
}

vec2 size = vec2(1., -1);
vec2 edge = vec2(1, 0.);
vec2 xLine = vec2(0., 0.);

float circle(vec2 uv){
	return abs(length(uv)-size.x);   
}
float circleS(vec2 uv){
	return abs(length(uv)-size.x*.5);   
}

float vert(vec2 uv){
	return length(vec2(uv.x,max(0.,abs(uv.y)-size.x)));   
}
float halfvert(vec2 uv){
	return length(vec2(uv.x,max(0.,abs(uv.y)-size.x*.5)));   
}
float hori(vec2 uv){
	return length(vec2(max(0.,abs(uv.x)-size.x),uv.y));   
}
float halfhori(vec2 uv){
	return length(vec2(max(0.,abs(uv.x)-size.x*.5),uv.y));   
}
float diag(vec2 uv){
	return length(vec2(max(0.,abs((uv.y-uv.x))-size.x*2.),uv.y+uv.x));   
}
float halfdiag(vec2 uv){
	return length(vec2(max(0.,abs(uv.x-uv.y)-size.x),uv.y+uv.x));   
}

// Here is the alphabet
float aa(vec2 uv) {
    float x = circle(uv);
    x = mix(x, min(vert(uv-edge), vert(uv+edge)), step(uv.y, 0.));
    x = min(x, hori(uv-xLine));
    return x;
}
float bb(vec2 uv) {
    float x = vert(uv+edge);
    x = min(x, hori(uv-edge.yx));
    x = min(x, hori(uv+edge.yx));
    x = min(x, hori(uv-xLine));
    x = mix(min(circleS(uv-size.xx*.5),circleS(uv-size*.5)),x, step(uv.x, .5));
    return x;
}
float cc(vec2 uv) {
    float x = circle(uv);
    float p = .8;
    float a = atan(uv.x, abs(uv.y));
    a = smoothstep(.7, 1.5707, a);
   	x += a;
    uv.y = -abs(uv.y);
    x = min(length(uv+size.x*vec2(-cos(p), sin(p))), x);
    return x;
}
float dd(vec2 uv) {
    float x = vert(uv+edge);
    x = min(x, hori(uv+edge.yx));
    x = min(x, hori(uv-edge.yx));
    x = mix(circle(uv),x, step(uv.x, 0.));
    return x;
}
float ee(vec2 uv) {
    float x = cc(uv);
    x = mix(circle(uv), x, step(uv.y, 0.));
    x = min(x, hori(uv));
    return x;
}
float ff(vec2 uv) {
   	float x = vert(uv+edge);
    x = min(x, hori(uv-edge.yx));
    x = mix(circle(uv), x, step(min(-uv.x, uv.y), 0.));
    x = min(x, halfhori(uv+edge*.5));
    return x;
}
float gg(vec2 uv) {
    float x = cc(uv);
    x = mix(x, circle(uv), step(uv.y, 0.));
    x = min(x, halfhori(uv-edge*.5));
    return x;
}
float hh(vec2 uv) {
    float x = vert(abs(uv)-edge);
    x = min(x, hori(uv));
    //x = min(x, circle(uv+edge.yx));
    //x = mix(x, min(length(uv-size.xy), length(uv-size.yy)), step(uv.y, size.y));
    return x;
}
float ii(vec2 uv) {
    return hh(uv.yx);
}
float jj(vec2 uv) {
    float x = vert(uv-edge);
    x = min(x, length(uv+edge));
    x = mix(x, circle(uv), step(uv.y, 0.));
    return x;
}
float kk(vec2 uv) {
    uv.y = abs(uv.y);
    float x = circle(uv-edge.yx);
    x = mix( length(uv-size.xx),x,step(uv.y, size.x)); 
    x = mix(x,min(vert(uv+edge), hori(uv)), step(uv.x, 0.));
    return x;
}
float ll(vec2 uv) {
    return min(vert(uv+edge), hori(uv+edge.yx));
}
float mm(vec2 uv) {
    uv.x = abs(uv.x);
    float x = vert(uv-edge);
    x = min(x, halfvert(uv-edge.yx*.5));
    x = mix( circleS(uv-size.xx*.5),x, step(uv.y, 0.5));
    return x;
}
float nn(vec2 uv) {
    float x = circle(uv);
    x = mix(min(vert(uv-edge), vert(uv+edge)), x, clamp(ceil(uv.y), 0., 1.));
    return x;
}
float oo(vec2 uv) {
    return circle(uv);
}
float pp(vec2 uv) {
    float x = hori(uv);
    x = min(x, hori(uv-edge.yx));
    x = mix( circleS(uv+size.yy*.5),x, step(uv.x, size.x*.5));
    x = min(x, vert(uv+edge));
    return x;
}
float qq(vec2 uv) {
    float x = circle(uv);
    x = min(x, halfdiag(uv-size.xy*.5));
    return x;
}
float rr(vec2 uv) {
    float x = min(hori(uv-edge.yx), vert(uv+edge));
    x = mix(x, circle(uv), step(0., min(-uv.x, uv.y)));
    return x;
}
float ss(vec2 uv) {
    float x = hori(uv-edge.yx);
    x = min(x, halfhori(uv));
    vec2 u = uv;
    u+=vec2(-size.y*.5, size.y*.5);
    x = mix(circleS(u),x, step(-edge.x*.5, uv.x));
    
    float x2 = hori(uv+edge.yx);
    x2= min(x2, halfhori(uv));
    u = uv;
    u-=vec2(-size.y*.5, size.y*.5);
    x2 = mix(x2,circleS(u),step(edge.x*.5, uv.x));
    
    return min(x,x2);
}
float tt(vec2 uv) {
    /*float x = min(hori(uv+edge.yx), vert(uv+edge));
    x = mix( circle(uv),x, step(0., max(uv.x, uv.y)));
    x = min(halfhori(uv+edge*.5), x);*/
    float x = min(vert(uv), hori(uv-edge.yx));
    return x;
}
float uu(vec2 uv) {
    uv.x = abs(uv.x);
    float x = mix(circle(uv), vert(uv-edge),  step(0., uv.y));
    return x;
}
float vv(vec2 uv) {
    uv.x = abs(uv.x);
    float p = .5;
    uv *= mat2(cos(p), -sin(p), sin(p), cos(p));
    float x = vert(uv-edge*.5);
    return x;
}
float ww(vec2 uv) {
    uv.y = -uv.y;
    return mm(uv);
}
float xx(vec2 uv) {
    return diag(abs(uv)*vec2(-1., 1.));
}
float yy(vec2 uv) {
    uv.x = abs(uv.x);
    float x = min(halfvert(uv+edge.yx*.5), circle(uv-edge.yx));
    x = mix(x, length(uv-size.xx), step(size.x, uv.y));
    return x;
}
float zz(vec2 uv) {
    float x = min(hori(uv-edge.yx), hori(uv+edge.yx));
    uv.x = -uv.x;
    return min(x, diag(uv));
}

//Render char if it's up
#define ch(l)  x=min(x,l(uv+vec2(spacing.x*nr, 0.)));nr-=size.x;

//Make it a bit easier to type text
#define a_ ch(aa);
#define b_ ch(bb);
#define c_ ch(cc);
#define d_ ch(dd);
#define e_ ch(ee);
#define f_ ch(ff);
#define g_ ch(gg);
#define h_ ch(hh);
#define i_ ch(ii);
#define j_ ch(jj);
#define k_ ch(kk);
#define l_ ch(ll);
#define m_ ch(mm);
#define n_ ch(nn);
#define o_ ch(oo);
#define p_ ch(pp);
#define q_ ch(qq);
#define r_ ch(rr);
#define s_ ch(ss);
#define t_ ch(tt);
#define u_ ch(uu);
#define v_ ch(vv);
#define w_ ch(ww);
#define x_ ch(xx);
#define y_ ch(yy);
#define z_ ch(zz);

//Space
#define _ nr--;
//Space
#define _half nr-=.5;

//Next line
#define crlf uv.y += spacing.w; nr = 0.;

vec4 spacing = vec4(3.33, 2., .25, 3.33);

float field(vec2 uv){
    float x = 100.;
    float nr = 0.;
    
    line1;
    line2;
    return x;
}

vec2 fieldNormal(vec2 uv)
{
   const vec2 e = vec2(0.3,0.0);
   return normalize(vec2(
      field(uv + e.xy) - field(uv - e.xy),
      field(uv + e.yx) - field(uv - e.yx) 
   ));
}

// Repeat around the origin by a fixed angle. For easier use, num of repetitions is use to specify the angle.
float pModPolar(inout vec2 p, float repetitions, float phase) {
	float angle = 2.*3.14159/repetitions;
	float a = atan(p.y, p.x) + angle/2.+phase/repetitions;
	float r = length(p);
	float c = floor(a/angle);
	a = mod(a,angle) - angle*.5;
    a = abs(a);
	p = vec2(cos(a), sin(a))*r;
	// For an odd number of repetitions, fix cell index of the cell in -x direction
	// (cell index would be e.g. -5 and 5 in the two halves of the cell):
	if (abs(c) >= (repetitions/2.)) c = abs(c);
	return c;
}

vec3 art(vec2 uv){
 float aa = atan(uv.x, uv.y);
 pModPolar(uv, 6., time);
 uv.x = abs(mod(uv.x-time, 10.)-5.);
 uv.y = abs(mod(uv.y+15., 30.)-15.);
 float a = atan(uv.x, uv.y);
 float d= length(uv)*.2;
 uv.x*=1.+sin(uv.x+a-d+time)*.1;
 uv.y*=1.+cos(uv.y+a+d+time)*.1;
 float grid = smoothstep(.03, .5, abs(mod(a/3.1415*7., 2.)-1.));
 grid += smoothstep(0., 1.,pow(mod(d, 1.), 3.));
 vec3 c =vec3(mix(d, grid, smoothstep(.1, 1., d)));
 c.rgb +=aa/3.1415;
 return c;
}

void main(void) {
 spacing.y = spacing.x*.5;
 spacing.z = 1./spacing.x;
 float scale = 1.0;
 vec2 uv = ((gl_FragCoord.xy - win_pos - 0.5*resolution.xy)/resolution.xx)*40.;
 vec2 p = uv;
 uv.x*=1.+sin(uv.y*.2-time)*.05;
 uv.y*=1.+cos(uv.x*.5+time)*.1;
 uv.y+=cos(uv.x*.1-time);
 uv.x += 5.*spacing.x;
 uv.y -= spacing.w*.5;
 float x = field(uv);
 vec2 norm = fieldNormal(uv);
 float amp = pow(smoothstep(5., .5, x), .7);
 vec3 c = art(p*(1. + contrast*10.)-norm*amp);
 c = sin((vec3(0., .33, .66)+c+smoothstep(.5, .0, x)+smoothstep(.1, 2., x))*6.28+time)*.5+.5;
 // c = mix(c, vec3(0.), smoothstep(.5, .4, x));
 float v = smoothstep(.2, .3, x);
 c = mix( sin(vec3(0., .33, .66)*7.+p.x+p.y+time)*.3+.9, c*smoothstep(15., 5., x), v);
 if (tex_col_mix != 0.0) {
  vec4 tex = texture2D(texture0, tex_coord0);
  c = mix(tex.rgb, c, tex_col_mix);
 }
 gl_FragColor = vec4(c, alpha);  // vec4(clamp(clr,0.0,1.0),alpha);
}
