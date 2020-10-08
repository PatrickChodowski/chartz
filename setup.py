from setuptools import setup

setup(
    name='plotter',
    url='https://github.com/PatrickChodowski/plotter',
    author='Patrick Chodowski',
    author_email='chodowski.patrick@gmail.com',
    packages=['plotter'],
    package_data={'plotter': ['plotter_templates/*.html',
                              'plotter_static/*.js',
                              'plotter_static/*.css',
                              'plotter_static/bootstrap/css/*.css',
                              'plotter_static/bootstrap/css/*.map',
                              'plotter_static/bootstrap/js/*.js',
                              'plotter_static/bootstrap/js/*.map']},
    install_requires=['flask', 'bokeh', 'google-cloud-bigquery', 'pandas', 'pyyaml', 'sqlalchemy'],
    # *strongly* suggested for sharing
    version='0.3.7',
    license='MIT',
    description='Flask module allowing to build dashboards for data defined in single yml files',
    long_description=open('README.rst').read(),
)