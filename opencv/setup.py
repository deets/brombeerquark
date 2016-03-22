from setuptools import setup, find_packages

setup(
    name = "bq.opencv",
    version = "0.1",
    packages = find_packages(),
    author = "Diez B. Roggisch",
    author_email = "deets@web.de",
    description = "Some OpenCV examples and tools for the Raspberry PI",
    license = "GPLv3",
    keywords = "python opencv raspberry pi",
    url = "https://github.com/deets/brombeerquark",
    entry_points={
        'console_scripts': [
            'wasserzaehler-calibration = bq.wasserzaehler:calibration',
            'wasserzaehler = bq.wasserzaehler:wasserzaehler',
        ],
    },
)
