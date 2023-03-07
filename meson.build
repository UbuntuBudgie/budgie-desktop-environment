project('budgie-desktop-environment',
	version: '1.5.0',
	meson_version: '>= 0.40.0',
)

appdir = 'arm'

prefix = get_option('prefix')
libdir = join_paths(prefix, get_option('libdir'))
INSTALL_DIR = join_paths(libdir, 'budgie-desktop', appdir)

subdir('ubpi/configuration-app/src')
subdir('ubpi/configuration-app/data')
subdir('ubpi/configuration-app/ui')

install_data(
    'ubpi/configuration-app/schema/org.ubuntubudgie.armconfig.gschema.xml',
    install_dir: '/usr/share/glib-2.0/schemas',
)
