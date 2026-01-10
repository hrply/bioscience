"""
AI科研助手安装脚本
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="ai-researcher",
    version="1.0.0",
    author="AI Research Team",
    author_email="research@example.com",
    description="AI科研助手 - 智能实验方案生成和管理系统",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/example/ai-researcher",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "ai-researcher=ai_researcher.cli:cli",
        ],
    },
    include_package_data=True,
    package_data={
        "ai_researcher": ["templates/*.yaml"],
    },
)
