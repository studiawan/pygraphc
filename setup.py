from setuptools import setup

setup(name='pygraphc',
      version='0.0.1',
      description='Event log clustering in Python',
      url='http://github.com/studiawan/pygraphc/',
      author='Hudan Studiawan',
      author_email='studiawan@gmail.com',
      license='MIT',
      packages=['pygraphc'],
      install_requires=[
          'networkx',
          'scikit-learn',
          'nltk',
          'numpy',
          'Sphinx',
          'numpydoc',
          'TextBlob',
      ],
      zip_safe=False)
