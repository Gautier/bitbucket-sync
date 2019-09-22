from setuptools import setup, find_packages

setup(
    name='bitbucket-sync',
    version='0.3.4',
    description='bitbucket-sync synchronize locally all the repositories of a bitbucket account',
    author='Gautier Hayoun',
    author_email='ghayoun@gmail.com',
    url='https://github.com/gautier/bitbucket-sync',
    license='MIT',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'bitbucket-sync = bitbucket_sync.main:main',
        ]
    },
    install_requires=['docopt==0.5.0',
                      'requests>=2.0.0',
                      'requests-oauthlib==0.4.0',
                      'oauthlib==0.6.0'],
)
