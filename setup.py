from setuptools import setup, find_packages
import os

version = '0.1'

setup(name='explosive.fuse',
      version=version,
      description="Mount archives as a filesystem.",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from
      # http://pypi.python.org/pypi?:action=list_classifiers
      classifiers=[
        "Programming Language :: Python",
        ],
      keywords='',
      author='Tommy Yu',
      author_email='y@metatoaster.com',
      url='https://github.com/metatoaster/explosive.fuse',
      license='GPL',
      packages=find_packages('src'),
      package_dir={'': 'src'},
      namespace_packages=['explosive'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          # -*- Extra requirements: -*-
          'fusepy',
      ],
      entry_points="""
      # -*- Entry points: -*-
      [console_scripts]
      explode = explosive.fuse.ctrl:main
      """,
      )
