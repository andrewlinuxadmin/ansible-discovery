# ansible-discovery
Ansible playbook for performing process discovery on Linux servers

### Create development environment:
1) Download and install the latest release of the UV package manager: https://github.com/astral-sh/uv/releases

2) Make a clone of this repository.

3) Use uv to download Python 3.9 standalone:<br/>
`uv python install -i ./ansible-discovery python3.9`

3) Create a virtualenv using python 3.9:<br/>
`./ansible-discovery/cpython-3.9.23-linux-x86_64-gnu/bin/python3 -m venv ./ansible-discovery/python-3.9-ansible-2.14`

4) Activate this virtualenv:<br/>
`./ansible-discovery/python-3.9-ansible-2.14/bin/activate`

5) Install python packages:<br/>
`pip install -r pip-venv-requirements.txt`

6) Install python packages:<br/>
`pip install -r pip-venv-requirements.txt`

7) Install Ansible Collections:<br/>
`cd ./ansible-discovery/playbooks`<br/>
`mkdir collections`<br/>
`ansible-galaxy collection install -r galaxy-requirements.yaml`

### VSCode:
Required VSCode Extensions

- https://marketplace.visualstudio.com/items?itemName=redhat.ansible
- https://marketplace.visualstudio.com/items?itemName=redhat.ansible

With virtualenv activated, and inside the playbooks folder, open VSCode::<br/>
`code .`

