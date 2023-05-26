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
8. Install suite2p - (on our AMD servers or locally):
  1. On analysis servers ***Tatchu and Loki***: 
      1. make sure to be on forge: 
      
         `conda config --add channels conda-forge`
         
          `conda config --set channel_priority strict` 
      2. `conda install "libblas=*=*mkl"` this can take a while. Be patient.
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


Here a starting point of how to use the pipeline:
https://www.evernote.com/shard/s4/sh/6c2cffa0-466e-460b-9bbb-62641aa3ed04/7qwbz9PwX692sM7JBSgrAef0Syt0BM0CaPPxXFuTO53Kbt8Po6RMPFg4jA

Reason for the annoying AMD install:
https://github.com/MouseLand/suite2p/issues/725

Solution after too much invested time:
https://www.evernote.com/shard/s4/client/snv?isnewsnv=true&noteGuid=5b256de6-3809-f4f9-5a57-66e793917ecd&noteKey=R7Js0zFUBeFljkpcf7iI9AQvY62OtdV35qjyEvsxGZytjhL-yshPiiI1wg&sn=https%3A%2F%2Fwww.evernote.com%2Fshard%2Fs4%2Fsh%2F5b256de6-3809-f4f9-5a57-66e793917ecd%2FR7Js0zFUBeFljkpcf7iI9AQvY62OtdV35qjyEvsxGZytjhL-yshPiiI1wg&title=suite2p%2Binstallation%2B-%2Btorch.fft%2Band%2Bmultithreading%2Bon%2BAMD%2Bepyc
