jpeg = dependency('libjpeg')
png = dependency('libpng')

fract4dc = py.extension_module('fract4dc',
    'fract4dmodule.cpp',
    'fract_stdlib.cpp',

    'fract4dc/colormaps.cpp',
    'fract4dc/loaders.cpp',
    'fract4dc/sites.cpp',
    'fract4dc/images.cpp',
    'fract4dc/calcs.cpp',
    'fract4dc/workers.cpp',
    'fract4dc/functions.cpp',
    'fract4dc/arenas.cpp',
    'fract4dc/utils.cpp',
    'fract4dc/calcargs.cpp',
    'fract4dc/pysite.cpp',

    'fract4dc/controllers.cpp',

    'model/calcfunc.cpp',
    'model/fractfunc.cpp',
    'model/site.cpp',
    'model/image.cpp',
    'model/imagewriter.cpp',
    'model/imagereader.cpp',
    'model/colormap.cpp',
    'model/worker.cpp',
    'model/STFractWorker.cpp',
    'model/MTFractWorker.cpp',
    'model/pointfunc.cpp',
    'model/stats.cpp',
    'model/colorutils.cpp',
    'model/imageutils.cpp',

    dependencies: [jpeg, png, py_dep],
    include_directories: ['fract4dc', 'model'],
    cpp_args: ['-DTHREADS=1', '-DPNG_ENABLED=1', '-DJPG_ENABLED=1'],
    gnu_symbol_visibility: 'default',
    install: true,
    subdir: 'fract4d',
)

install_headers(
    'fract_stdlib.h',
    'pf.h',
    install_dir: py.get_install_dir() / 'fract4d/c',
)

install_headers(
    'model/colorutils.h',
    'model/imageutils.h',
    install_dir: py.get_install_dir() / 'fract4d/c/model',
)
