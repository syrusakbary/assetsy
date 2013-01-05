from setuptools import setup, find_packages

setup(
    name='Assetsy',
    version=".".join(map(str, __import__("assetsy").__version__)),
    description='A vitaminated way to minify, combine and optimize your web resources',
    long_description=open('README.rst').read(),
    author='Syrus Akbary Nieto',
    author_email='me@syrusakbary.com',
    url='http://github.com/syrusakbary/assetsy',
    license='BSD',
    packages=find_packages(exclude=['ez_setup']),
    install_requires=[],
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Flask',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries',
    ],
)
