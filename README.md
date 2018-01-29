# PROJECT: isilonAssistantApp

## DESCRIPTION:

A proof-of-concept to demonstrate that Isilon deployment can be automated without human interactions.

1. Emulate console keyboard/mouse to initialize the first Isilon node based on a JSON config template.
2. Then, call Isilon RestAPI to join the remaining nodes to the Isilon cluster
3. Once the cluster is form, use Isilon RestAPI to configure one NFS export without root squash at path /ifs/data

## PREREQUISITES:

Required software components:
* Python 3.6.4
* pip 9.0.1
* Python Flask 0.12.2
* Isilon OneFS Simulator 8.1.0.2

Optional software components:
* cURL 7.57.0
* Flask-MySQL 1.4.0
* MySQL 5.7.21

PATH environment variable: Python, cURL, MySQL

## ASSUMPTION:

1. Console to Isilon node is available

## INSTRUCTIONS:

* Execute application via CLI
	1. Edit the JSON config template
	```
	type templateAppA.json
	type templateAppB.json
	```
	2. Run the Python application
	`python isilonAssistant.py`

* Execute application via Web GUI
	1. Edit the JSON config template
	```
	type templateAppA.json
	type templateAppB.json
	```
	2. Launch the Python Flask web application
	`python isilonAssistantApp.py`
	3. Open web browser and direct to the application URL
	`http://localhost:5000`

## VERSION:

01/26/2018 v0.1.0

## AUTHORS:

**Paul Nguyen**
*paul.nguyen@emc.com*

## ACKNOWLEDGEMENTS:

Special thanks to many public forums, blogs, and books for inspiration in developing and debuging this project. Sample codes were adapted/rewritten to fit the framework of this application.

1. EMC Community Forum: Isilon SDK Info Hub (https://community.emc.com/docs/DOC-48273)
2. Automate the Boring Stuff with Python (https://automatetheboringstuff.com/chapter18/)
3. Creating a Web App From Scratch Using Python Flask and MySQL (https://code.tutsplus.com/tutorials/creating-a-web-app-from-scratch-using-python-flask-and-mysql--cms-22972)
4. Learning Python 5th Edition - Mark Lutz - O'Reilly
5. Introduction to Programing Using Python - Y Liang - Pearson