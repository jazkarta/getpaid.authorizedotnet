from setuptools import setup, find_packages

setup(
    name="getpaid.authorizedotnet",
    version="0.0.1",
    packages=find_packages('src'),
    package_dir={'':'src'},
    namespace_packages=['getpaid'],
    include_package_data=True,
    install_requires = [ 'setuptools',
                         'zope.interface',
                         'zope.component',
                         ],
    zip_safe = False,
    )
