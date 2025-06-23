project('span', 'c', 'cython', version : '0.1.0')

py = import('python').find_installation()
cython = find_program(meson.get_compiler('cython').cmd_array()[0])

# https://github.com/mesonbuild/meson/issues/8693#issuecomment-2511060673
cythonize = generator(cython,
    output : '@BASENAME@.c',
    arguments : ['--output-file', '@OUTPUT@', '--include-dir', '@BUILD_ROOT@', '@INPUT@'])

subdir('src')
