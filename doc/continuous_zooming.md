# Continuous zooming feature

Continuous zooming feature allows the user to dynamically explore the fractal by creating an animation. Animation will zoom in/out the fractal following up the pointer position, while the user holds left/right mouse button.

## User experience

While the CZ feature is running, a fixed amount of zoom is performed in/out depending on which button the user is holding (left/right). The frame rate is fixed, as well as the amount of zooming, but since some computers could take longer than the time expected to render a single frame, the frame rate might drop and not be constant. As it might be already obvious, the higher the resolution the more chances for the frame rate to drop, always depending on the CPU power.

CZ uses different algorithms to enhance performance and get a decent frame rate, including _pixel reutilization_ or _dynamic resolution_ which are explained further below in this document. Nevertheless, since Gnofract 4D is highly customizable and allows the user the create his own fractals, the computing power needed to render each frame could vary a lot.

Some of the regular preferences or features of Gnofract 4D do not take effect when working in CZ mode. That includes _auto deepen_, _auto tolerance_ and _antialiasing_.

### Enabling/disabling the feature

Users can enable/disable CZ under the image preferences (Edit -> Preferences).
While the CZ is enabled, creating a selection rect is not possible, and, as described before, some other features/improvements stop working.

### Limitations

One of the foundations of the continuous zooming feature is the _pixel reutilization algorithm_. This algorithm is based on the principle that, on the complex plane XY, imaginary values keep constant while moving across X axis and real values do the same for the Y axis. Thus, rotations on the XY plane, prevent CZ to work properly.

If you zoom in all the way down till the precision limit, you'll find yourself with a very low detail fractal. The reason for this is staticstics-based improvements (auto-deepen, auto-tolerance) don't take effect while running CZ mode. To partially mitigate this, every time the user releases the mouse button, a _regular_ drawing so staticstics-based improvements are applied, adjusting for example the _max iters_ value.

If the user enters the _explorer mode_ while CZ is enabled, only the central canvas will produce the animation. The external permutation canvas will update after user releases the mouse button.

## Developer manual

As it is better explained in [Gnofract 4D internals](https://fract4d.github.io/gnofract4d/manual/index.html#gnofract-4d-internals), heavy fractal computations are performed in the `fract4dc` C++ extension.

This produces a two layer architecture, being python layer responsible for presenting the UI and thus drawing the fractal canvas. Gnofract 4D uses Gtk and Cairo for that purpose.

Communication between the two layers is managed in the following ways:
- custom [python extension](https://docs.python.org/3/extending/extending.html): this is how python layer sends information to the C++ layer
- using [pipes](https://docs.python.org/3/library/os.html#os.pipe): this is how python layer receives (asynchronous) information from the C++ layer

With this basic idea in mind, and in a few words, Gnofract 4D sends all the parameters to the C++ and triggers the fractal calculation process from python, then the C++ layer informs about the progress by writing in the pipe that python layer is reading. When the python layer acknowledges there's something new to present to the user it reads the image information from a shared buffer and draws it accordingly in the image canvas.
### Implementation approach and algorithms

While the communication scheme subtlely explained above is fine for the regular functioning mode, it presents some drawbacks for the CZ mode.

In the regular mode, every time a new fractal image has to be drawn, C++ performs some boilerplate initializations. Doing this for an on-going animation that creates a new image every few miliseconds is unbearable.

For that reason, scheme communication for CZ is slightly different. Instead of using the _regular_ image calculation trigger API from the `fract4dc` extension, a new API has been created with the following conceptual facade:
- start CZ process: this triggers the image calculation process and perform boilerplate initializations on the C++ layer. It also creates an infinite loop waiting for updates from the python layer.
- update CZ location: sends an update to be processed by the infinite loop from the previous API.
- stop CZ process: tells the infinite loop to stop waiting for updates and finish off.

The other communication flow remains the same: python part will be reading the pipe to draw image updates from C++.
#### Pixel reutilization algorithm

This is the main algorithm and the foundation of the CZ feature.
The basic idea behind this is that, for every new frame you want to draw there are some pixels from the previous frame you can reuse.

While Gnofract 4D utilizes some algorithms to improve performance, the basic idea behind the image calculation process is that every single pixel of the image is assigned a point in the complex plane XY (actually Gnofract allows to work in a 4D space with six plane rotation), and that point is the _driving_ parameter to pass to the fractal formula to calculate every pixel color.

`Location` (`X`, `Y` ... and `Z`, `W` in 4D space) and `Size` parameters will determine which point of the complex plane correspond to every pixel of the image (we leave out from this explanation the plane rotation parameters). This makes very likely to happen that subsequent frames, where location and size would change slightly, have pixels with the same, or very close point in the complex plane. So it makes sense to, instead of calculate the color of that pixel again (which is the heaviest process) we take the already calculated value.

The process to find those pixels with same or close complex plane point values, in an efficient way, is based in the assumption that _imaginary values `y` remain constant while moving across X axis, while real values `x` do the same for the Y axis_. And it consist in the following steps:
- find all the `x` values or columns for the new fractal (image) that are close enough to the previous image ones.
- find all the `y` values or rows for the new fractal (image) that are close enough to the previous image ones.
- for every row/column found combination pixel might be reused. And the rest of the pixels should be calculated anew.

The third step of the process states _pixel might be reused_ because pixels cannot be carried out from one frame to another endlessly, to prevent building up error. As we don't look for exact matches but _close enough_ complex plane points, if we calculate a pixel for a frame and reuse it for the next frame, we assume some error margin. Then we have to save the exact value we are reusing, so further frames can check if the margin error is still acceptable.

#### Dynamic resolution

As explained before, there are multiple factors that influence the ability of Gnofract 4D to keep up the frame rate while running CZ. CPU power, fractal formula complexity and image resolution are the main ones.

This algorithm is not a magic solution to produce smooth animations under every condition, but it should help to boot frame rate in some cases.

At a high level point of view, this algorithm gives more priority to pixels close to the center of the image when zooming in and the other way around when zooming out. This is because, for example, when zooming in, pixels around the center are more likely to be reused in further frames. That said, at a certain point, we stop calculating pixels and instead we use reused pixels from previous frame to interpolate remaining ones.
That _certain point_ is enabled when:
- the time to calculate the current frame is over (we cannot keep up frame rate)
- we have calculated/reused a minimum number of pixels. Otherwise, we wouldn't have enough detail, and it will get worse for subsequent frames (no pixels to reuse).

The regular calculation process, without taking into account advanced algorithms like _box-guessing_, basically calculates pixels row by row from left to right.
CZ calculation process does this using a spiral loop, this way inner/outer pixels can be calculated before.

#### Multithread and box guessing

Gnofract4D already implements some performance enhancement and concurrency algorithms.
Some have been ported to CZ implementation.

**Box guessing** prevents calculating the image one pixel at a time. Instead, boxes of 16x16 are processed in the following way:
- calculate edge pixels
- if all pixels in edges are equal then fill the whole box with the same color. Otherwise divide the box in four pieces and for each one start over this process.

**Thread pool** to take advantage of multithreading, Gnofract 4D implements a job thread pool. Every piece of work (calculating a box using _box guessing_ for example) is put into this pool an proceesed as soon as a thread is available.
For CZ, we have adapted this algorithm, so using _dynamic resolution_ approach (spiral loop) we put every box calculation into the pool. Then instead of a `queue` we use a `list` so we are able to take jobs from the front or from the back, depending which ones we want to prioritize.
