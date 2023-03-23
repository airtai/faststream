from pkg_resources import parse_version
from configparser import ConfigParser
import setuptools
assert parse_version(setuptools.__version__)>=parse_version('36.2') # nosec

# note: all settings are in settings.ini; edit there, not here
config = ConfigParser(delimiters=['='])
config.read('settings.ini')
cfg = config['DEFAULT']

cfg_keys = 'version description keywords author author_email'.split()
expected = cfg_keys + "lib_name user branch license status min_python audience language".split()
for o in expected: assert o in cfg, "missing expected setting: {}".format(o) # nosec
setup_cfg = {o:cfg[o] for o in cfg_keys}

licenses = {
    'apache2': ('Apache Software License 2.0','OSI Approved :: Apache Software License'),
    'mit': ('MIT License', 'OSI Approved :: MIT License'),
    'gpl2': ('GNU General Public License v2', 'OSI Approved :: GNU General Public License v2 (GPLv2)'),
    'gpl3': ('GNU General Public License v3', 'OSI Approved :: GNU General Public License v3 (GPLv3)'),
    'bsd3': ('BSD License', 'OSI Approved :: BSD License'),
}
statuses = [ '1 - Planning', '2 - Pre-Alpha', '3 - Alpha',
    '4 - Beta', '5 - Production/Stable', '6 - Mature', '7 - Inactive' ]
py_versions = '3.6 3.7 3.8 3.9 3.10 3.11'.split()

requirements = [
    "pydantic>=1.9",
    "anyio>=3.0",
    "aiokafka>=0.8.0",
    "fastcore>=1.5.27",
    "asyncer>=0.0.2",
    "tqdm>=4.62",
    "docstring-parser>=0.15",
    "typer>=0.7.0",
]
test_requirements = [
    "install-jdk==0.3.0",
    "nest-asyncio>=1.5.6",
    "ipywidgets>=8.0,<=8.0.4",
    "requests>=2.20",
]
docs_requirements = [
    "PyYAML>=5.3.1",
    "aiohttp>=3.8.4"
]

min_python = cfg['min_python']
lic = licenses.get(cfg['license'].lower(), (cfg['license'], None))

dev_requirements = [
    "nbconvert>=7.2.9",
    "nbformat>=5.7.3",
    "nbdev-mkdocs==0.2.2",
    "mypy==1.0.1",
    "pre-commit==3.0.4",
    "nbqa==1.6.3",
    "black==23.1.0",
    "isort==5.12.0",
    "bandit==1.7.4",
    "semgrep==1.14.0",
    "pytest==7.2.1",
    "numpy>=1.21.0",
    "pandas>=1.2.0",
    "email-validator==1.3.1",
    "scikit-learn==1.2.1",
]

project_urls = {
   'Bug Tracker': cfg['git_url'] + '/issues',
   'CI': cfg['git_url'] + '/actions',
   'Documentation': 'https://fastkafka.airt.ai/',
#    'Source Code': cfg['git_url'],
    'Tutorial': 'https://colab.research.google.com/github/airtai/fastkafka/blob/main/nbs/guides/Guide_00_FastKafka_Demo.ipynb'
}

setuptools.setup(
    name = cfg['lib_name'],
    license = lic[0],
    classifiers = [
        'Development Status :: ' + statuses[int(cfg['status'])],
        'Intended Audience :: ' + cfg['audience'].title(),
        'Natural Language :: ' + cfg['language'].title(),
    ] + ['Programming Language :: Python :: '+o for o in py_versions[py_versions.index(min_python):]] + (['License :: ' + lic[1] ] if lic[1] else []),
    url = cfg['git_url'],
    project_urls=project_urls,
    packages = setuptools.find_packages(),
    include_package_data = True,
    install_requires = requirements,
    extras_require={ 'dev': dev_requirements + test_requirements + docs_requirements, "test": test_requirements, "docs": docs_requirements },
    dependency_links = cfg.get('dep_links','').split(),
    python_requires  = '>=' + cfg['min_python'],
    long_description = open('README.md', encoding="UTF-8").read(),
    long_description_content_type = 'text/markdown',
    zip_safe = False,
    entry_points = {
        'console_scripts': cfg.get('console_scripts','').split(),
        'nbdev': [f'{cfg.get("lib_path")}={cfg.get("lib_path")}._modidx:d']
    },
    **setup_cfg) # type: ignore
