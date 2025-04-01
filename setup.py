from setuptools import setup, find_packages

setup(
    name="sts_saml_driver",  # Change this to your project name
    version="1.0.3",
    py_modules=["sts_saml_driver"],
    install_requires=[
        "requests",
        "bottle",
        "boto3",
        "urllib3"
    ],
    entry_points={
        "console_scripts": [
            "stssamldriver=sts_saml_driver:main",  
        ],
    },
    author="Liam Wadman",
    author_email="liwadman@amazon.com",
    description="A utility to capture SAML assertions and use them to get AWS credentials without browser emulation",
    url="https://github.com/awslabs/StsSamlDriver",  #
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
)