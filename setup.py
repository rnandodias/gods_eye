from setuptools import setup, find_packages

setup(
    name='olho_de_deus',
    version='0.1.0',
    author='Rodrigo Dias',
    author_email='rnandodias@gmail.com',
    description='Ferramenta de acompanhamento do time da Escola de Dados da Alura',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='',
    packages=find_packages(),
    install_requires=[
        'requests',
        'openai',
        'python-dotenv',
        'google_auth_oauthlib',
        'google',
        'tqdm',
        'pymongo',
        'pandas',
        'discord'
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)