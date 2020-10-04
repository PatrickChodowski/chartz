from setuptools import setup

setup(
    name='plotter',
    url='https://github.com/PatrickChodowski/plotter',
    author='Patrick Chodowski',
    author_email='chodowski.patrick@gmail.com',
    packages=['plotter'],
    install_requires=['flask', 'bokeh', 'google-cloud-bigquery', 'pandas', 'pyyaml'],
    # *strongly* suggested for sharing
    version='0.1',
    license='MIT',
    description='Flask module allowing to build dashboards for data defined in single yml files',
    long_description=open('README.txt').read(),
)