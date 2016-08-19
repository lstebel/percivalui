Instructions for using the Ubuntu Virtual Machine
=================================================

You should have received the following information by email:

* Link to download `Percival_Ubuntu_14.04_64-bit.zip`
* Ubuntu username
* Password

Installing VMWare and booting Ubuntu Linux
------------------------------------------

On your Windows Host system (i.e. your desktop) first download and install the free
[VMware Player for Windows 64-bit operating systems]
(https://my.vmware.com/en/web/vmware/free#desktop_end_user_computing/vmware_player/7_0|PLAYER-713|product_downloads) version 7. 

Download the `Percival_Ubuntu_14.04_64-bit.zip` file and unzip to a suitable location on your Windows PC. Recommendation
is to use a local harddisk.

Start up the VMWare Player application, configure it to load the Percival Ubuntu Virtual Machine (VM) and start up the VM:

* In VMWare Player click "Open a Virtual Machine"
 * Browse to the unzipped VM and select the `Percival Ubuntu 14.04 64-bit.vmx` file.
 * The VM should appear in the list on the lefthand side of VMWare Player with the title "Percival Ubuntu 14.04 64-bit"
* Select the VM in the VMWare player list
* Click the green triangle "play" button to start the VM.
* In the pop-up select that you've copied the VM (rather than moved it...)
* The VM should boot the Ubuntu operating system.

Logging in to the Ubuntu OS
---------------------------

Once the Ubuntu OS has booted up you should be left with a log-in screen. Click the "Percival User" and enter the 
supplied password.

The desktop is fairly empty. The "Activities" button in the top-left corner is equivalent to a Windows "Start" menu and
will bring up a left-hand pane with a few applications: Chromium, a Terminal and a couple of other things. The 3x3 square
dot matrix will bring up a browser of all of the installed applications. Mostly we will be using the terminal.

Open the Terminal. You should be left with a prompt like this:

```
percival@ubuntu:~$
```

The Percival code will live in the `Percival` folder. So far it only has the `percivalui` code checked out - that is the 
python code to control the Carrier board.

Updating the Python code
-----------------------

Before running any python code you should make sure you have the very latest version from Diamond. The software is hosted
on github and the update process is straight forward - just pull down the latest on the "master" branch. 

Run the following commands in the Terminal window:

```
cd Percival/percivalui
source venv27/bin/activate

python setup.py develop --uninstall

git pull origin master

pip install -r requirements.txt --upgrade

python setup.py develop
```

Running the Python code
-----------------------

In order to setup an appropriate Python environment in your open Terminal session, start by activating the supplied 
python virtual environment and setting the Carrier Board (XPort) IP address. 
This only need to be done once for the open Terminal session:

```
# If you are not already in the percivalui dir:
cd Percival/percivalui 

source venv27/bin/activate

# Set an environment variable with the IP address of your Carrier Board Xport
export PERCIVAL_CARRIER_IP=xxx.xxx.xxx.xxx
```

Then you are ready to run the scripts. 

Sandbox scripts
---------------

The "sandbox" scripts are found in the sandbox/ dir. This is a development/staging area for command-line scripts that
have not yet fully matured into usable applications. However, they can be useful in testing and development.

For example run the `readdevice.py` script which will read the temperature sensor
(channel #18) in a loop and record the data into a hdf5 file:
 
```
python sandbox/readdevice.py
```

The `readdevice.py` script will run forever. Stop it with the key combination: `Ctrl-c` (Control and c)

You can open the output hdf5 file with the command `hdfview readdevice.h5`

Installed scripts
-----------------

The ```python setup.py develop``` (or eventually for end-users ```python setup.py install```) will install mature scripts
into the (virtual) python environment so that the full/relative path to the script need not be specified. Installed
scripts will have the 'percival-' prefix so they can be easily listed and TAB-completed on the Linux shell when typing 
the first few letters like perc - followed by one or two hits on the TAB key.

```
(venv27)(carrier_board_dev) [up45@pc0009 percivalui]$ perc<TAB>
(venv27)(carrier_board_dev) [up45@pc0009 percivalui]$ percival-<TAB><TAB>
percival-client        percival-control       percival-scan-devices  
(venv27)(carrier_board_dev) [up45@pc0009 percivalui]$ percival-co<TAB>
(venv27)(carrier_board_dev) [up45@pc0009 percivalui]$ percival-control
```

percival-control
----------------

This is a wrapper of all the Percival Control classes into one service application. Open a new Terminal window (or tab)
and start the application with the following commands:

```
# If you are not already in the percivalui dir:
cd Percival/percivalui 

source venv27/bin/activate

# Set an environment variable with the IP address of your Carrier Board Xport
export PERCIVAL_CARRIER_IP=xxx.xxx.xxx.xxx

percival-control --init 
....
.... lots of applications logs coming out here...

```

To interact with the application/carrier board use the ```percival-client``` application (see below).

To quit the application use the ```CTRL-c```.
 
percival-client
---------------

This is a terminal text based user interface which allow for sending a number of commands to the carrier board through
the percival-control service. 

Start the application in a new Terminal window (or tab) with the following commands:

```
# If you are not already in the percivalui dir:
cd Percival/percivalui 

source venv27/bin/activate

percival-client 
```

From this screen you can change the control and status endpoints before starting the client and connecting to the 
standalone application. Hit enter-enter-enter to accept the default (local) channel settings.

![alt text](images/standalone_client_intro.png "Standalone Client Introduction")

Once the control and status endpoints have been confirmed you are presented with the main screen.  From the left-hand
pane it is possible to send commands/queries to the percival-control application (and thereby the Percival carrier board). 
It is also possible to start and stop the status loop; starting it will result in the response box periodically updating 
with new status.

![alt text](images/standalone_client_main1.png "Standalone Client Main")

It is also possible to request execution of system commands from the client application.

![alt text](images/standalone_client_main2.png "Standalone Client System Command")

To quit the application use "Exit" option in the left-hand Main Menu panel.

Shutdown the Ubuntu VM
----------------------

Always shut down the VM as if it was a real machine (to avoid corrupting HDD state): close applications first. Click on
the power button icon on the top-right corner, click on the power icon in the drop-down menu and finally select 
"Power Off" in the pop-up.
