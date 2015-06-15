from distutils.core import setup

with open('README.rst') as description:
    long_description = description.read()

setup(
    name='Marnadi',
    version='0.4.0',
    author='Rinat Khabibiev',
    author_email='srenskiy@gmail.com',
    packages=[
        'marnadi',
        'marnadi.http',
        'marnadi.http.data',
        'marnadi.http.data.decoders',
        'marnadi.http.data.decoders.application',
        'marnadi.utils',
    ],
    url='https://github.com/renskiy/marnadi',
    license='MIT',
    description='Yet another WSGI web framework',
    keywords='WSGI, HTTP, REST',
    long_description=long_description,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Environment :: Web Environment',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Internet :: WWW/HTTP :: WSGI',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)