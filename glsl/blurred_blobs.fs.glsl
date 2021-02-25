// Blobs By @paulofalcao
uniform float alpha;
uniform float tex_col_mix;
uniform float time;
uniform vec2 win_pos;
uniform vec2 resolution;

float makePoint(float x,float y,float fx,float fy,float sx,float sy,float t){
 float xx=x+sin(t*fx)*sx;
 float yy=y+cos(t*fy)*sy;
 return 1.0/sqrt(xx*xx+yy*yy);
}

void main( void ) {
 vec2 p = ((gl_FragCoord.xy - win_pos)/resolution.x*2.0 - vec2(1.0,resolution.y/resolution.x)) * 2.0;
 float x=p.x;
 float y=p.y;

 float a=
     makePoint(x,y,3.3,2.9,0.3,0.3,time);
 a=a+makePoint(x,y,1.9,2.0,0.4,0.4,time);
 a=a+makePoint(x,y,0.8,0.7,0.4,0.5,time);
 a=a+makePoint(x,y,2.3,0.1,0.6,0.3,time);
 a=a+makePoint(x,y,0.8,1.7,0.5,0.4,time);
 a=a+makePoint(x,y,0.3,1.0,0.4,0.4,time);
 a=a+makePoint(x,y,1.4,1.7,0.4,0.5,time);
 a=a+makePoint(x,y,1.3,2.1,0.6,0.3,time);
 a=a+makePoint(x,y,1.8,1.7,0.5,0.4,time);

 float b=
     makePoint(x,y,1.2,1.9,0.3,0.3,time);
 b=b+makePoint(x,y,0.7,2.7,0.4,0.4,time);
 b=b+makePoint(x,y,1.4,0.6,0.4,0.5,time);
 b=b+makePoint(x,y,2.6,0.4,0.6,0.3,time);
 b=b+makePoint(x,y,0.7,1.4,0.5,0.4,time);
 b=b+makePoint(x,y,0.7,1.7,0.4,0.4,time);
 b=b+makePoint(x,y,0.8,0.5,0.4,0.5,time);
 b=b+makePoint(x,y,1.4,0.9,0.6,0.3,time);
 b=b+makePoint(x,y,0.7,1.3,0.5,0.4,time);

 float c=
     makePoint(x,y,3.7,0.3,0.3,0.3,time);
 c=c+makePoint(x,y,1.9,1.3,0.4,0.4,time);
 c=c+makePoint(x,y,0.8,0.9,0.4,0.5,time);
 c=c+makePoint(x,y,1.2,1.7,0.6,0.3,time);
 c=c+makePoint(x,y,0.3,0.6,0.5,0.4,time);
 c=c+makePoint(x,y,0.3,0.3,0.4,0.4,time);
 c=c+makePoint(x,y,1.4,0.8,0.4,0.5,time);
 c=c+makePoint(x,y,0.2,0.6,0.6,0.3,time);
 c=c+makePoint(x,y,1.3,0.5,0.5,0.4,time);

 vec3 col = vec3(a,b,c) / 32.0;
 if (tex_col_mix != 0.0) {
   vec4 tex = texture2D(texture0, tex_coord0);
   col = mix(tex.rgb, col, tex_col_mix);
 }
 gl_FragColor = vec4(col.rgb, alpha);
}
