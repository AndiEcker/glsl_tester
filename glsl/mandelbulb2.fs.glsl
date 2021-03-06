// Original shader from http://glslsandbox.com/e#55620.1 using spherical coordinates to map up Mandelbulb-loop everytime
// https://en.wikipedia.org/wiki/Mandelbulb#:~:text=The%20Mandelbulb%20is%20a%20three,dimensional%20space%20of%20complex
// %20numbers. Spherical coordinates: https://en.wikipedia.org/wiki/Spherical_coordinate_system; References:
// - http://blog.hvidtfeldts.net/index.php/2011/06/distance-estimated-3d-fractals-part-i/
// - http://www.fractal.org/Formula-Mandelbulb.pdf and https://archive.bridgesmathart.org/2010/bridges2010-247.pdf
// Mandelbulb and Mandelbox are ESCAPE-TIME FRACTALS: we iterate a function for each point in space, and follow the
// orbit to see whether the sequence of points diverge for a maximum number of iterations, or whether the sequence stays
// inside a fixed escape radius.
uniform float alpha;
uniform float tex_col_mix;
uniform float time;
uniform vec2 win_pos;
uniform vec2 resolution;
uniform vec2 mouse;

float mandelbulb(vec3 pos) {
  const int MAX_ITER = 35; //Number of iteration //Adding details
  const float BAILOUT=4.0; //When to exit the loop
  // for power>3, the result is a 3D bulb-like structure with fractal surface detail, and a number of "lobes" depending
  // on power. adding transition here
  float Power=4.;//+sin(t2*3.)*3.;
  float transitionTime = time*0.3;  // *0.4*0.75;  // t2*0.75;
  if(sin(transitionTime)>0. && sin(transitionTime)<=0.5){
    Power=4.-sin(transitionTime)*4.;
  }else if(sin(transitionTime)>=0.25){
    Power=2.;
  }else if(sin(transitionTime)<0. && sin(transitionTime)>=0.5){
    Power=2.+sin(transitionTime)*4.;
  }else if(sin(transitionTime)<=-0.25){
    Power=4.;
  }
  //float Power=3.;
  //Declare bunch of stuff we are going to use here
  vec3 inputPos = pos;
  float r1=0.0;
  float d1=1.0;
  for(int n=0; n<=MAX_ITER; ++n) {
    //🌟🌟 Extract polar coordinates
    //Now start calculate the Spherical coordinates value, r1, theta and phi
    r1 = length(pos); //equal to sqrt(pos.x*pos.x+pos.y*pos.y+pos.z*pos.z);
    //When length(pos)>4.,escape the loop
    if(r1>BAILOUT) break;
    float theta = acos(pos.z/r1) ;//+ sin(t2);
    float phi = atan(pos.y, pos.x);
    /* Reference:https://www.iquilezles.org/www/articles/mandelbulb/mandelbulb.htm
    float theta = acos(pos.y/r1) ;//Try Power 2. and 3.
    float phi = atan(pos.x, pos.z);
    */
    // Distance estimator?
    d1 = pow(r1,Power-1.15)*Power*d1 ;//+ sin(t1);
    // 🌟🌟 Scale and rotate the point
    float zr = pow(r1,Power); //power of r value that will multiply in the position later
    // 🔴🔴🔴 Main adjustment here
    theta = theta*Power+mouse.y*5.6;//
    //theta = theta*(1.+sin(time)*2.);
    phi = phi*Power+1.-mouse.x*6.5;//
    //🌟🌟 Convert back to cartesian coordinates
    //Update the position here
    //pos = (vec3(sin(theta)*cos(phi),sin(theta)*cos(phi),-sin(theta))*zr)+inputPos;
    //pos = (vec3(sin(theta)*cos(phi),sin(theta)*cos(phi),cos(theta))*zr)+inputPos;
    //Original below
    pos = (vec3(sin(theta)*cos(phi), sin(phi)*sin(theta), cos(theta))*zr)+inputPos;
    //---> Have fun remove some Power here
    //---> Actually the (p,q) value (check wiki page) are not necessary equal to Power, have fun changing that
    //pos = (vec3(sin(theta*Power*(2.+mouse.x*2.5))*cos(phi*Power), sin(phi*Power*(2.+mouse.x*2.5))*sin(theta*Power),
    //         cos(theta*Power))*zr)+inputPos;
  }
  //🌟🌟 Return the distance estimator? / Smooth the edge?
  //Adjust the clipping plane??
  return 0.4*log(r1)*r1/d1;
  //The value of the distance estimator tells you how large a step you are allowed to march along the way.
  //which means you need to guaranteed not to hit anything within this radius
}

// Credit to Nan's code
float project(float n, float start1, float stop1, float start2, float stop2){
  float newVal = (n-start1)/(stop1-start1)*(stop2-start2)+start2;
  return newVal;
}

/*
Raymarching technique - Distance Estimation
  Check http://blog.hvidtfeldts.net/index.php/2011/06/distance-estimated-3d-fractals-part-i/
  For all points in space returns a length smaller than (or equal to) the distance to the closest object. March the ray
  according to the distance estimator and return a greyscale value based on the number of steps before hitting something
  Proceed in small steps along the ray and check how close you are to the object you are rendering. Distance estimation
  ONLY tells the distance from a point to an object. This in contrast to classic ray tracing, which is about finding the
  distance from a point to a given object along a line.
*/

void main( void ){
  //float t1 = time * 1.0; //1.1;
  //float t2 = time * 0.4;
  vec2 pos = ((gl_FragCoord.xy - win_pos)*2.0 - resolution.xy) / resolution.y;
  //Stop Camera rotation here
  vec3 camPos = vec3(3.,3.,2.5);//Use +abs(sin(t1))*28. to test
  //vec3 camPos = vec3(cos(t2*0.3+t2), sin(t2*0.3-t2), 2.-sin(t2*.2)/2.);
  vec3 camTarget = vec3(0.0, 0.0, 0.0);
  vec3 camDir = normalize(camTarget-camPos);
  vec3 camUp  = normalize(vec3(0.0, 0.0, 0.8));
  //vec3 camUp  = normalize(vec3(0.0, 1.0, 0.8));
  vec3 camSide = cross(camDir, camUp);//Camera X position
  //float focus = 2.5 + abs(sin(t2))*6.; //Move the camera back and forth
  float focus = 4.+sin(time * 0.4)*2.; //Move the camera back and forth
  //float focus = 3.;
  vec3 rayDir = normalize(camSide*pos.x + camUp*pos.y + camDir*focus)*1.;//Can adjust the brightness with multiplication
  vec3 ray = camPos;
  // gl_FragColor = vec4(vec3(trace(ray, rayDir)),0.0);
  float count = 0.0;
  float d = 0.0, total_d = 0.0;
  const int MAX_MARCH = 80;            //MaxRaySteps
  const float MAX_DISTANCE = 60.0;
  const float MIN_DISTANCE = 0.001;	 //When reach this distance to the edge, stop //Adding details
  for(int i=0; i<MAX_MARCH; i++) {
    d = mandelbulb(ray);
    total_d += d;
    ray += rayDir * d;
    count += 1.0;//Coloring method:The Iteration Count is the number of iteration it tales before the orbit diverges
    //(become larger than the escape radius)
    if(d<MIN_DISTANCE) { break; } // Escape when reach minima to boundaries of the objects, to increase the efficiency
    if(total_d>MAX_DISTANCE) { total_d=MAX_DISTANCE; break; }
  }
  float c = project(total_d,MIN_DISTANCE,MAX_DISTANCE,0.,1.);//sin(t1*2.)
  float brightness = 0.23;     //adjust the brightness of fractal
  float background_strips = 3.2;//0.04; //adding color and strips to the background
  //float c = (total_d)*0.00001;
  //vec4 result = vec4(1.0-vec3(c, c, c) - vec3(0.1024576534223, 0.02506, 0.2532)*count*0.8, alpha);
  //vec4 result = vec4(1.0-vec3(0.1*c,2.0*c,0.5*c+sin(t1*2.)*3.)-vec3(0.02506, 0.1024576534223, 0.2532)*count*0.8, 1.0);
  //🔵🟣 purple-blue
  //vec4 result = vec4( 1.0-vec3(0.01*c, 2.0*c, 0.5*c) - vec3(0.025, 0.1, 0.)*count*0.4, alpha );
  //⚪️🔵🟡
  //vec4 result = vec4( 1.0-vec3(background_strips*c, 2.0*c, 0.000005*c*-0.3)
  //            - vec3((0.025, 0.1, 0.25)*count*brightness*0.13), alpha );
  vec4 result = vec4( 1.0-vec3(background_strips*c, 2.0*c, 0.5*c) - vec3(0.025, 0.1, 0.25)*count*brightness, alpha );
  if (tex_col_mix != 0.0) {
   vec4 tex = texture2D(texture0, tex_coord0);
   result = mix(tex, result, tex_col_mix);
  }
  gl_FragColor = result;
}
