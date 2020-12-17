# Continuous zooming feature

Continuous zooming feature allows the user to dynamically explore the fractal by creating an animation. Animation will zoom in/out the fractal following up the pointer position, while the user holds left/right mouse button.

## User experience

While the CZ feature is running, a fixed amount of zoom is performed in/out depending on which button the user is holding (left/right). The framerate is fixed, as well as the amount of zooming, but since some computers could take longer than the time expected to render a single frame, the frame rate might drop and not be constant. As it might be already obvious, the higher the resolution the more chances for the frame rate to drop, always depending on the CPU power.

CZ uses different algorithms to enhance performance and get a decent framerate, including "pixel reutilization" or "dynamic resolution" which are explained further below in this document. Nevertheless, since Gnofract4d is highly customizable and allows the user the create his own fractals, the computing power needed to render each frame could vary a lot.

Some of the regular preferences or features of Gnofract4d do not take effect when working in CZ mode. That includes "auto deepen", "auto tolerance" and "antialiasing".

### Enabling/disabling the feature

Users can enable/disable CZ under the image preferences (Edit -> Preferences).
While the CZ is enabled, creating a selection rect is not possible, and, as described before, some other features/improvements stop working.

### Limitations

One of the foundations of the continuous zooming feature is the "pixel reutilization algorithm". This algorithm is based on the principle that, on the complex plane XY, imaginary values keep constant while moving across X axis and real values do the same for the Y axis. Thus, rotations on the XY plane, prevent CZ to work properly.

If you zoom in all the way down till the precision limit, you'll find yourself with a very low detail fractal. The reason for this is staticstics-based improvements (auto-deepen, auto-tolerance) don't take effect while running CZ mode. To partially mitigate this, every time the user releases the mouse button, a "regular" drawing so staticstics-based improvements are applied, adjusting for example the "max iters" value.

If the user enters the "explorer mode" while CZ is enabled, only the central canvas will produce the animation. The external permutation canvas will update after user releases the mouse button.

## Developer manual

### Implementation approach and algorithms
