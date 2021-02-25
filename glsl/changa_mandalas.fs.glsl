// Original shader from: https://www.shadertoy.com/view/tsdfWf
uniform float alpha;
uniform float tex_col_mix;
uniform float time;
uniform vec2 win_pos;
uniform vec2 resolution;
uniform vec4 tint_ink;

float n2D(vec2 p) {
 vec2 i = floor(p);
 p -= i;
 p *= p*(3. - p*2.);
 return dot(mat2(fract(sin(vec4(0, 1, 113, 114) + dot(i, vec2(1, 113)))*43758.5453))*vec2(1. - p.y, p.y),
            vec2(1. - p.x, p.x));
}

float fbm(vec2 p){
 return n2D(p)*.533 + n2D(p*2.)*.267 + n2D(p*4.)*.133 + n2D(p*8.)*.067;
}

void radialFold(inout vec2 p, float cant, float offset) {
 float d = 3.1416 / cant * 2.;
 float at = atan(p.y, p.x);
 float a = mod(at, d) - d * .5;
 p = vec2(cos(a), sin(a)) * length(p) - vec2(offset, 0.);
}

float fractal(vec2 p) {
 float m = 100., s = 1.5, d = 1., t = mod(floor(time * .81 - .5), 6.);
 for (float i = 0.; i < 12.; i++)
 {
  radialFold(p, 3. + t, 2. + t * 3.);
  p *= s; d *= s;
  m = min(m, (abs(p.y) + 2. *step(.5, fract(p.x * .02 - time * .81 + i * .05))) / d);
 }
 return exp(-250. * m);
}

void main(void) {
 vec2 uv = (gl_FragCoord.xy - win_pos - resolution.xy * .5) / resolution.y;
 //uv -= (vec2(fbm(uv*16.), fbm(uv*16. + .5)) - .5)*.01; // mod by Shane, subtle perturbation to enhance ink pen feel
 //vec3 col = 1. - vec3(1., .7, 0) * fractal(uv * 2.5);
 vec3 col = tint_ink.rgb * fractal(uv * 2.5);
 if (tex_col_mix != 0.0) {
   vec4 tex = texture2D(texture0, tex_coord0);
   col = mix(tex.rgb, col, tex_col_mix);
 }
 gl_FragColor = vec4(col, alpha);
}
