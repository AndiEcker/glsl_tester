# glsl_tester app

glsl_tester is a Python multi-platform application project to test shaders written in the OpenGL glsl language.

this app project is based on the [__Kivy__ Framework](https://kivy.org) as well as on the
[__ae__ (Application Environment)](https://ae.readthedocs.io "ae on rtd") namespace portions.

glsl `uniform` parameter arguments can be synchronized and dynamically changed on running shaders. mix outputs/drawings
of multiple shaders by using values below 1.0 for the `alpha` (opacity) uniform arguments.

the shader code examples, bundled into this app, got taken from the [__glsl sandbox__](http://glslsandbox.com/). most of
them got adapted by adding some useful `uniform`/input parameters to control their output dynamically. as dynamic inputs
can be used e.g. the mouse pointer position, the last touch position(s), key presses and/or the colors and sliders in
the user preferences menu (like e.g. the vibration and sound volume).

credits to:

* [__Erokia__](https://freesound.org/people/Erokia/) and 
  [__plasterbrain__](https://freesound.org/people/plasterbrain/) at
  [freesound.org](https://freesound.org) for the sounds.
* [__glsl sandbox__](http://glslsandbox.com/) for glsl shader code examples (see individual copyrights in shader files).
* [__iconmonstr__](https://iconmonstr.com/interface/) for the icon images.
* [__Kivy__](https://kivy.org) for this great multi-platform framework.
