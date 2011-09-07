from setuptools import setup, find_packages

setup(name='hyde',
      version='0.5.3',
      description='Hyde is a static website generator originally inspired by Jekyll',
      author='Lakshmi Vyas',
      author_email='lakshmi.vyas@gmail.com',
      url='http://ringce.com/hyde',
      packages=find_packages(),
      install_requires=(
          'django',
          'pyYAML',
          'markdown',
          'pygments',
          'pyrss2gen',
      ),
      scripts=['hyde.py', 'clyde.py'],
      entry_points={
          'console_scripts': [
              'hyde = hyde:main',
              'clyde = clyde.main'
          ]
      },
      classifiers=[
            'Development Status :: 5 - Production/Stable',
            'Environment :: Console',
            'Intended Audience :: End Users/Desktop',
            'Intended Audience :: Developers',
            'Intended Audience :: System Administrators',
            'License :: OSI Approved :: MIT License',
            'Operating System :: MacOS :: MacOS X',
            'Operating System :: Unix',
            'Operating System :: POSIX',
            'Programming Language :: Python',
            'Programming Language :: Python :: 2.6',
            'Programming Language :: Python :: 2.7',
            'Topic :: Software Development',
            'Topic :: Software Development :: Build Tools',
            'Topic :: Software Development :: Websites',
            'Topic :: Software Development :: Static Websites',
      ],
)
