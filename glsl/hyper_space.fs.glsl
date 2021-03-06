uniform float alpha;
uniform float contrast;
uniform float tex_col_mix;
uniform float time;
uniform vec2 win_pos;
uniform vec2 resolution;
uniform vec2 center_pos;

const int MAX_STEPS = 64;
const int MAX_HITS = 4;
const float EPS = 1.0 / 256.0;
const float MOUSE_SENS = 6.0;
const vec3 CAM_POS = vec3(-5, 0, 0);
const vec3 CAM_DIR = vec3(1, 0, 0);

float sphereSDF(vec3 pos, float r) {
  return length(pos) - r;
}

float sceneSDF(vec3 pos) {
  return sphereSDF(pos, 1.0);
}

vec3 sceneNormal(vec3 pos) {
  vec3 eps = vec3(EPS, 0, 0) / 16.0;
  return normalize(vec3(sceneSDF(pos + eps.xyy) - sceneSDF(pos - eps.xyy),
                        sceneSDF(pos + eps.yxy) - sceneSDF(pos - eps.yxy),
                        sceneSDF(pos + eps.yyx) - sceneSDF(pos - eps.yyx)));
}

struct Ray {
 vec3 pos;
 vec3 dir;
 vec4 color;
 int steps;
};

vec3 loop(vec3 p) {
 const float l = 10.0;
 p += vec3(l / 2.0);
 p /= l;
 p = fract(p);
 p *= l;
 p -= vec3(l / 2.0);
 return p;
}

Ray fixRay(Ray n) {
 n.pos = loop(n.pos);
 n.dir = normalize(n.dir);
 return n;
}

mat2 rotate(float a) {
 float si = sin(a), co = cos(a);
 return mat2(co, si, -si, co);
}

Ray getRay(vec2 p) {
 Ray r = Ray( CAM_POS, CAM_DIR, vec4(vec3(0), 0.001), 0 );
 p *= center_pos;
 r.dir.y += p.y;
 r.dir.z += p.x;
 r.dir.xy *= rotate(MOUSE_SENS * (0.5- time / 99.9 * alpha));
 r.dir.xz *= rotate(MOUSE_SENS * (0.5 - time / 99.9 * contrast));
 return r;
}

Ray updateRay(Ray r) {
 // Hit detection
 if(sceneSDF(r.pos) < EPS) {
  vec3 norm = sceneNormal(r.pos);
  r.dir -= 2.0 * norm * dot(norm, r.dir);
  r.pos += EPS * norm;

  vec4 color = vec4((norm + r.dir) / 2.0, min(0.5, 16.0 / float(r.steps)));
  r.color += color * (color.a) * (1.0 - r.color.a);
  r.steps = 0;
 }
 r = fixRay(r);
 r.pos += r.dir * sceneSDF(r.pos);
 r.steps++;
 return r;
}

void main( void ) {
 vec2 position = 2.0 * ((gl_FragCoord.xy - win_pos) / resolution.xy - 0.5);
 position.x *= resolution.x / resolution.y;
 Ray r = getRay(position);
 for(int i = 0; i < MAX_STEPS; ++i) {
  r = updateRay(r);
 }
 vec4 col = r.color / r.color.a;
 if (tex_col_mix != 0.0) {
  vec4 tex = texture2D(texture0, tex_coord0);
  col = mix(tex, col, tex_col_mix);
 }
 gl_FragColor = col;
}
