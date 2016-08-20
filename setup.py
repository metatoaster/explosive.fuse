from setuptools import setup, find_packages
import os

version = '0.5'

setup(name='explosive.fuse',
      version=version,
      description="Mount archives as a filesystem.",
      long_description=open("README.rst").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.rst")).read(),
      # Get more strings from
      # http://pypi.python.org/pypi?:action=list_classifiers
      classifiers=[
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'Intended Audience :: End Users/Desktop',
          'Operating System :: POSIX :: Linux',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: Implementation :: PyPy',
          'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
          'Topic :: System :: Filesystems',
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
      test_suite="tests",
      entry_points="""
      # -*- Entry points: -*-
      [console_scripts]
      explode = explosive.fuse.ctrl:main
      """,
      )
