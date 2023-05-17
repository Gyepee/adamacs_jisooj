# Architectures for Data Management and Computational Support

This is the central database architecture for the collaborative research center
of the [SFB1089](https://sfb1089.de/). It is based on
[datajoint](https://www.datajoint.org/).

The schemas present are organized as follows:
![adamacs_schemas](./images/adamacs_schemas.svg)

The above are linked to
[SFB's fork](https://github.com/SFB1089/element-calcium-imaging.git) of DataJoint's
calcium imaging Element:
![adamacs_calcium_imaging](./images/adamacs_calcium_imaging.svg)

# Installation
1. Install Anaconda and go to a command prompt. (miniconda preferred! Do not install in user roaming profile. Install under local directory.)
2. At the command prompot navigate to a directory where you want to download adamacs and type `git clone https://github.com/SFB1089/adamacs.git`
3. Enter the adamacs directory that was created with `cd adamacs`
4. Create an environment called `datajoint` with `conda create --name datajoint python=3.8 `
5. Activate the newly created environemnt with `conda activate datajoint`
6. Install the latest datajoint with dependencies with `conda install -c conda-forge datajoint`
7. Install adamacs with `pip install .`
8. TR: Install suite2p - (on our AMD servers or locally):
  1. On analysis servers ***Tatchu and Loki***: 
      1. make sure to be on forge: 
         `conda config --add channels conda-forge
          conda config --set channel_priority strict` 
      2. `conda install "libblas=*=*mkl"`
      3. `git clone https://github.com/SFB1089/suite2p.git`
      4. `cd suite2p'
      5. `pip install -e .`
      6. `conda install pytorch`
      7. `conda install numba`
      8. `conda install jupyter`
  2. Locally
      1. `git clone https://github.com/SFB1089/suite2p.git`
      2. `cd suite2p'
      5. `pip install -e .`
10. To get started right away open `jupyter notebook` and open a notebook you want to use.
11. I highly recommend to use VSCode with remotely SSH to work on the server:
  1. Install VS Code, then install the Remote Development extension pack. https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.vscode-remote-extensionpack   
  2. connect to datajoint server ***Tatchu*** with your credentials: ssh yourname@serverIP
  3. select your 'datajoint' environment as python environment
