from setuptools import setup, find_packages

setup(
    name='claude-dev-assistant',
    version='0.1.0',
    description='Claude Dev Assistant - 全流程自动化开发工具',
    author='Claude',
    packages=find_packages(),
    install_requires=[
        'pyyaml>=6.0',
        'click>=8.0',
    ],
    entry_points={
        'console_scripts': [
            'claude-dev=claude_dev_assistant.driver:main',
        ],
    },
    python_requires='>=3.10',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
    ],
)
