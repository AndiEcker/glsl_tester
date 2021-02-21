$HEADER$

uniform float alpha;
uniform float tex_col_mix;
uniform float time;
uniform vec2 win_pos;
uniform vec2 resolution;
uniform vec2 mouse;

#define pi2_inv 0.159154943091895335768883763372

float border(vec2 uv, float thickness){
 uv = fract(uv - vec2(0.5));
 uv = min(uv, vec2(1.)-uv)*2.;
 //	return 1.-length(uv-0.5)/thickness;
 return clamp(max(uv.x,uv.y)-1.+thickness,0.,1.)/thickness;;
}

vec2 div(vec2 numerator, vec2 denominator){
 return vec2( numerator.x*denominator.x + numerator.y*denominator.y,
              numerator.y*denominator.x - numerator.x*denominator.y)/
        vec2(denominator.x*denominator.x + denominator.y*denominator.y);
}

vec2 spiralzoom(vec2 domain, vec2 center, float n, float spiral_factor, float zoom_factor, vec2 pos){
 vec2 uv = domain - center;
 float d = length(uv);
 return vec2( atan(uv.y, mouse.x)*n*pi2_inv/sin(mouse.y) + log(d)*spiral_factor, -log(d)*zoom_factor) + pos;
}

void main( void ) {
 vec2 uv = (gl_FragCoord.xy - win_pos) / resolution.xy;
 uv = 0.5 + (uv - 0.5)*vec2(resolution.x/resolution.y,1.);
 vec2 p1 = vec2(0.2,0.5);
 vec2 p2 = vec2(0.8, 0.5);
 vec2 moebius = div(uv-p1, uv-p2);
 uv = uv-0.5;
 vec2 spiral_uv = spiralzoom(moebius,vec2(0.),8.,-.5,1.8,vec2(0.5,0.5)*time*0.5);
 vec2 spiral_uv2 = spiralzoom(moebius,vec2(0.),3.,.9,1.2,vec2(-0.5,0.5)*time*.8);
 vec2 spiral_uv3 = spiralzoom(moebius,vec2(0.),5.,.75,4.0,-vec2(0.5,0.5)*time*.7);
 vec4 col = vec4(border(spiral_uv,0.9), border(spiral_uv2,0.9), border(spiral_uv3,0.9), alpha);

 vec2 weed_uv = (uv);
 weed_uv.y += 0.38;
 float w = 0.05 * mouse.y / resolution.y;
 float r = 0.33 * mouse.x / resolution.x + 0.1;
 float o = atan(weed_uv.y, weed_uv.x);
 r *= (1.+sin(o+(time*0.09)))*(1.+0.9 * cos(8.*o))*(1.+0.1*cos(24.*o))*(0.9+0.05*cos(200.*o));
 float l = length(weed_uv);
 float d = clamp(1.-abs(l - r + w*2.)/w, 0., 1.);
 col *= 1.-d;

 if (tex_col_mix != 0.0) {
  vec4 tex = texture2D(texture0, tex_coord0);
  col = mix(tex, col, tex_col_mix);
 }
 gl_FragColor = col;
}
