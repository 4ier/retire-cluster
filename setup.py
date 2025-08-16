"""
Setup script for Retire-Cluster
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README file
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements = [
    "psutil>=5.8.0",
]

# Optional requirements
optional_requirements = {
    "mcp": ["mcp>=0.1.0"],
    "dev": [
        "pytest>=7.0.0",
        "pytest-cov>=4.0.0",
        "black>=22.0.0",
        "flake8>=5.0.0",
        "mypy>=1.0.0",
    ]
}

setup(
    name="retire-cluster",
    version="1.0.0",
    author="Retire-Cluster Team",
    author_email="team@retire-cluster.com",
    description="A distributed system for repurposing idle devices into a unified AI work cluster",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/retire-cluster/retire-cluster",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: System :: Distributed Computing",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Systems Administration",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    extras_require=optional_requirements,
    entry_points={
        "console_scripts": [
            "retire-cluster-main=retire_cluster.main_node:main",
            "retire-cluster-worker=retire_cluster.worker_node:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="cluster, distributed, devices, iot, automation, monitoring",
    project_urls={
        "Bug Reports": "https://github.com/retire-cluster/retire-cluster/issues",
        "Source": "https://github.com/retire-cluster/retire-cluster",
        "Documentation": "https://retire-cluster.readthedocs.io/",
    },
)