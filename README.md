# Draivcan App

This application is made for Udacity's FSND project 3. Note that this is not a
functional product ready for deployment. ONLY for learning purposes.


[Project Guide](https://docs.google.com/document/d/1jFjlq_f-hJoAZP8dYuo5H3xY62kGyziQmiv9EPIA7tM/pub?embedded=true)

## Table of Contents
* [Files](#files)
* [Required Dependencies](#required-dependencies-and-modules)
* [How To Run](#how-to-run)
* [JSON API](#json-api)

## Files

* **db_model.py** - This file contains the database models.

* **application.py** - This file is the main program used to create Draivcan.

* **templates/** - This directory contains the HTML templates used to render the app.

* **static/** - This directory contains contains a CSS file.

* **main.css** - This is the CSS file used to tweak the look of the app.

* **client_secrets.json** - JSON for filling with your JSON api ID from google.

[Back to Top](#draivcan-app)

## Required Dependencies and modules

* Python 2.7

* Python pip

* Python Flask

* SQLAlchemy

* SQLite

* Oauth2Client Module

* Requests Module

* Httplib2 Module

[Back to Top](#draivcan-app)

## How to Run

* Install required dependencies and modules on your machine or use udacity Vagrant VM

* Clone repository ```git clone http://github.com/carrharr/Item_Catalog_P3```

* Go to folder ```cd Item_Catalog_P3```

* Make a project and create api credentials at (https://console.developers.google.com)
  Remember to set javascript and redirect URI's to http://127.0.0.1:8000

* Download credentials JSON from google developer console and insert content
  in client_secrets.json

* In templates/login.html fill in line 15 your Google API client ID

* Setup database with ```python db_model.py```

* Start serving with ```python application.py```

* Access at 127.0.0.1:8000 and voila!

[Back to Top](#draivcan-app)

## JSON API

JSON can be retrieved at the following endpoints:
* ```127.0.0.1:8000/trips/json```
* ```127.0.0.1:8000/driver/{driver_id}/json```
* ```127.0.0.1:8000/driver/{driver_id}/{trip_id}/json```

[Back to Top](#draivcan-app)

## Questions and requests

Please send your questions and requests to danielcarrilloharis@gmail.com 
