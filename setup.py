from setuptools import setup, find_packages


setup(
    name = 'multi-rq',
    version = '0.1',
    description = 'Simple async multiprocessing with RQ',
    long_description = 'an extension of rq that emulates the mp.Pool.apply_async behavior in multiprocessing with a task queue',
    keywords = ' dash rq redis plotly multiprocessing task queue',
    url = 'https://github.com/russellromney/multi-rq',
    author = 'Russell Romney',
    author_email = 'russellromney@gmail.com',
    license = 'MIT',
    packages = find_packages(),
    install_requires = [
        'rq>=1.0',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    include_package_data = False,
    zip_safe = False
)
