from setuptools import setup

classifiers=[
        'Development Status :: Alpha',
        'Environment :: MacOS X',
        'Environment :: Win32 (MS Windows)',
        'Environment :: X11 Applications',
        'Intended Audience :: Globus Users',
        'License :: OSI Approved :: Apache License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Topic :: Utility',
    ]
install_requires = [
    'globus_sdk',
]
setup(
    name='archeion',
    version='0.0.1',
    description='High level tools to manage globus transfers',
    author='Ashutosh Bhudia',
    author_email='ashu.bhudia@gmail.com',
    license='Apache License, Version 2.0',
    classifiers=classifiers,
    platfroms=['MacOS X', 'Linux', 'Windows'],
    install_requires=install_requires,
    packages=['archeion']
)