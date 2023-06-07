# ACID Android App Collusion Potential Detector

This tool is detecting app collusion potential. The tool uses androguard to extract facts about
app communication and used permissions. Extracted facts and a set of Prolog rules can be used later to detect the collusion
potential between the apps in the analysed set. The tool is split in three components: the fact generator, the Prolog generator and the detection tool (that executed the Prolog program). These programs should be run in sequence.

## Requirements
####  Pyhton 
Requires Python 2.7. As there might be a Python 3 version already present on the laptop, it is recommended to explicitly mention the Python 2 version when running the scripts.

#### Androguard 
This project relies on Androguard to execute most of the analysis tasks. Specifically, we use Androguard 2.0. That version has a minor bug in 
function call inside the `dvm.py`. This project links directly (using git submodules) to a version with that bug fixed so you don't need to change anything

####  Prolog 
Additionally, the tool uses the command line SWI-Prolog implementation.

## Installation


### Install packages

```
sudo apt install git python-setuptools swi-prolog
```

### Clone git repository

We clone the git repository with the `--recursive` option to clone the main repository along with submodules.


If you don't use `--recursive`, then you can clone the androguard sub-module manually:

```
cd ~/Desktop/collusion_potential_detector/androguard-acid

git submodule init

git submodule update
```

### Install patched version of Androguard

```
cd ~/Desktop/collusion_potential_detector/androguard-acid

sudo python2 setup.py install
```

### Install to system directory

```
sudo mv ~/Desktop/collusion_potential_detector /usr/local/

sudo chown -R root:root /usr/local/collusion_potential_detector

sudo ln -s /usr/local/collusion_potential_detector/generate_facts.py /usr/local/bin/generate_facts

sudo ln -s /usr/local/collusion_potential_detector/generate_prolog.py /usr/local/bin/generate_prolog

sudo ln -s /usr/local/collusion_potential_detector/detect_collusion.py /usr/local/bin/detect_collusion
```

## Running the tools

### Step 1: Generation of collusion facts
The first step is to generate the collusion facts for a set of apps. The tool will extract the facts and write them to a directory per analysed app.

For exact usage of the tool run:

```
python2 generate_facts.py --help
```

This tool generates various output files per analysed apk file:
- `packages.pl.partial`: Prolog facts about the apk package name.
- `uses.pl.partial`: Prolog facts about permissions used by the apps.
- `trans.pl.partial`: Prolog facts about the communication channels used by the apps to send information to other apps.
- `recv.pl.partial`: Prolog facts about the communication channels used by the apps to receive information from other apps.


### Step 2: Generation of Prolog program
The Prolog progam is generated after the collusion fact directories have been created in Step 1.

For exact usage of the tool run:

```
python2 generate_prolog.py --help
```

### Step 3: Detection of collusion 
The final step is to execute the Prolog program generated in Step 2. A python program controls the execution of the Prolog progam and acts as a wrapper.

For exact usage of the tool run:

```
python2 detect_collusion.py --help
```

This tool outputs a list of all collusion app sets found in the `prolog_file`. It includes the apps in the set, and the channels used to communicate.
 
## Testing

To test the fact extraction process you can use py.test

```
pip install py.test
```

