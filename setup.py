from setuptools import setup, find_packages

setup(
    name="aws_saml_driver",  # Change this to your project name
    version="1.0.0",
    py_modules=["saml_driver"],
    install_requires=[
        "requests",
        "bottle",
        "boto3",
        "urllib3"
    ],
    entry_points={
        "console_scripts": [
            "stssamldriver=saml_driver:main",  
        ],
    },
    author="Liam Wadman",
    author_email="liwadman@amazon.com",
    description="A utility to capture SAML assertions and use them to get AWS credentials without browser emulation",
    url="https://github.com/yourusername/my_project",  #
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
)