project('gnofract4d', 'cpp',
    license: 'BSD',
    default_options: ['cpp_std=c++17',
        'buildtype=release',
        'warning_level=3',
        'b_ndebug=if-release',
        'b_lto=true',
        'strip=true',
    ],
    meson_version: '>= 0.56',
    version: '4.3',
)

project_datadir = get_option('datadir') /  meson.project_name()
if get_option('docdir') != ''
    project_docdir = get_option('docdir')
else
    project_docdir = get_option('datadir') /  'doc/gnofract4d'
endif

pymod = import('python')
py = pymod.find_installation()

py_version = py.language_version()
if py_version.version_compare('< 3.9')
    error('Sorry, you need Python 3.9 or higher to run Gnofract 4D.'
          + ' You have version ' + py_version + '. Please upgrade.')
endif

py_dep = py.dependency(required: true)

gnome = import('gnome')
gresource = gnome.compile_resources('gnofract4d', 'fract4dgui/gnofract4d.gresource.xml',
    source_dir: 'fract4dgui',
    gresource_bundle: true,
    install: true,
    install_dir: project_datadir,
)

install_data('gnofract4d',
    install_dir: get_option('bindir'),
)

subdir('fract4d/c')

packages = ['fract4d', 'fract4d_compiler', 'fract4dgui']
foreach p: packages
    install_subdir(p,
        install_dir: py.get_install_dir(),
        exclude_directories: ['tests', 'builder', 'c', 'fract4d_new'],
        exclude_files: ['gnofract4d.css', 'gnofract4d.gresource.xml'],
    )
endforeach

conf_data = configuration_data()
conf_data.set('app_datadir', get_option('prefix') / project_datadir)
conf_data.set('version', meson.project_version())
conf_file = configure_file(input: '_conf_data.py.in',
   output: '_conf_data.py',
   configuration: conf_data,
   install: true,
   install_dir: py.get_install_dir() / 'fract4d',
)

# Application Data

install_data(['LICENSE', 'README.md'],
    install_dir: project_docdir,
)

install_subdir('help',
    exclude_directories: 'svg',
    exclude_files: ['favicon.svg', 'flexsearch.min.js', 'index.xml',
        'manifest.json', 'mermaid.min.js', 'sitemap.xml'],
    install_dir: project_datadir / 'help',
    strip_directory: true,
)

install_subdir('formulas',
    install_dir: project_datadir,
)

install_subdir('maps',
    install_dir: project_datadir,
)

# Desktop Environment Data

install_data('pixmaps/logo/48x48/gnofract4d.png',
    install_dir: 'share/pixmaps',
)

icon_sizes = [16, 32, 48, 64, 128, 256]
icon_template = 'pixmaps/logo/@0@x@0@/gnofract4d.png'
icon_dir_template = '@0@x@0@/apps/gnofract4d.png'
icons = []
icon_dirs = []

foreach s: icon_sizes
    icons += icon_template.format(s)
    icon_dirs += icon_dir_template.format(s)
endforeach

install_data(icons,
    rename: icon_dirs,
    install_dir: 'share/icons/hicolor',
)

install_data('io.github.fract4d.desktop',
    install_dir: 'share/applications',
)

install_data('gnofract4d-mime.xml',
    install_dir: 'share/mime/packages',
)

# Test

cp = find_program('cp')
custom_target('cp_so',
    command: [cp,
        fract4dc.full_path(),
        meson.project_source_root() / 'fract4d/',
    ],
    output: 'none1',
    build_by_default: true,
    depends: fract4dc,
)
custom_target('cp_gresource',
    command: [cp,
        gresource,
        meson.project_source_root(),
    ],
    output: 'none2',
    build_by_default: true,
    depends: gresource,
)
custom_target('cp_confdata',
    command: [cp,
        conf_file,
        meson.project_source_root() / 'fract4d/',
    ],
    output: 'none3',
    build_by_default: true,
)

pytest = find_program('pytest', required: false)
if pytest.found()
    test('testing',
        pytest,
        args: [
            'fract4d',
            'fract4dgui',
            'fract4d_compiler',
            'test.py',
        ],
        timeout: 60,
        workdir: meson.project_source_root(),
    )
endif
