from distutils.core import setup


install_requires = [
    "requests",
    "chromedriver-autoinstaller-fix",
    "selenium==4.5.0",
    "undetected_chromedriver>=3.4.6",
    "beautifulsoup4>=4.11.2",
    "joblib==1.2.0",
    "selenium-wire",
]
extras_require = {}
cpython_dependencies = [
    "PyDispatcher>=2.0.5",
]

def get_description():
    try:
      return open("README.rst", encoding="utf-8").read()
    except:
      return None
    
            
setup(
    name='botasaurus',
    packages=['botasaurus'],
    version='2.0.19',
    license='MIT',
    project_urls={
        "Documentation": "https://omkar.cloud/botasaurus/",
        "Source": "https://github.com/omkarcloud/botasaurus",
        "Tracker": "https://github.com/omkarcloud/botasaurus/issues",
    },

    description="The Ultimate Web Scraping Framework",
    long_description=get_description(),
    # long_description_content_type="text/markdown",
    author='Chetan Jain',
    author_email='chetan@omkar.cloud',
    maintainer="Chetan Jain",
    maintainer_email="chetan@omkar.cloud",

    keywords=["crawler", "framework", "scraping", "crawling", "web-scraping", "web-scraping-python", "cloudflare-bypass", "anti-detection", "bot-detection", "automation", "webdriver", "browser"],
    classifiers=[
        "Framework :: Scrapy",
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.7",
    install_requires=install_requires,
    extras_require=extras_require,
)