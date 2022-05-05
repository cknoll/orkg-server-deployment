# orkg-server-deployment


This repo contains tools and data to facilitate the deployment of your own instance of the [Open Research Knowledge Graph (ORKG)](https://www.orkg.org/) (backend and frontend). It does not contain any ORKG-data.


**Note:** This repo is an experimental project. It is not supported by the ORKG-team, but a third-party project by a curious ORKG user. It is based on the official ORKG docs (see below) plus some individual experiences. If you have questions regarding the deployment process defined by *this repo* please contact its maintainer.

The content of this repo comes without any warrenty. Use it at your own risk. Make backups. Something might be broken.


## Usage

Assumptions:
- Local machine running Linux with python>=3.8. (Other setups might work but are not tested).
- Debian based remote machine to which you have ssh access (tested with Ubuntu 20.04.04)


### Installation
- Run `pip install deploymentutils`
- Copy `config-example.ini` to `config-production.ini`, adapt this file with your data

### Usage

Ideally it should suffice to run the script once, but adaptions are probably necessary. The basic idea is to run commands on the remote machine and to upload files (generated from templates) with rsync as needed.

- Inspect the content of `deploy.py` to get an idea what it does.
- Enable ssh key for 10 minutes:
- Run `eval $(ssh-agent); ssh-add -t 10m`
- Run `python deploy.py remote`


## Relevant Docs


- https://gitlab.com/TIBHannover/orkg/orkg-frontend/-/wikis/Run-ORKG-locally
- https://gitlab.com/TIBHannover/orkg/orkg-frontend
- https://gitlab.com/TIBHannover/orkg/orkg-backend
