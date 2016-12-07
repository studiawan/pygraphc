from setuptools import setup

setup(name='pygraphc',
      version='0.0.1',
      description='Event log clustering in Python',
      long_description='This package contains event log clustering method including non-graph and '
                       'graph-based approaches.',
      classifiers=[
            'Development Status :: 2 - Pre-Alpha',
            'License :: OSI Approved :: MIT License',
            'Programming Language :: Python :: 2.7',
            'Topic :: Security',
      ],
      keywords='log clustering graph anomaly',
      url='http://github.com/studiawan/pygraphc/',
      author='Hudan Studiawan',
      author_email='studiawan@gmail.com',
      license='MIT',
      packages=['pygraphc'],
      scripts=['scripts/pygraphc'],
      install_requires=[
            'networkx',
            'sklearn',  # scikit-learn
            'nltk',
            'numpy',
            'Sphinx',
            'numpydoc',
            'TextBlob',
      ],
      include_package_data=True,
      zip_safe=False)
