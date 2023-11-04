# apt2bom

apt2bom is a tool to generate software bill of material (SBOM) templates form apt metadata.

## Background

We want to enable building of customized embedded Linux distributions for industrial usage, based in Debian packages. In this context, it is necessary to know in detail what is part of the final solution, and to store everything which enables a frozen-version long term maintenance for decades.

## Usage

apt2bom gets as input the list of packages which shall be part of the solution and resolves, based on the apt metadata, the full tree of build-time and run-time dependencies.

The run-time dependencies will become part of the customized embedded solution. The build-time dependencies will become part of the SDK, to enable the frozen-version long term maintenance.
