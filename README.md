Instructions for running this social media mock-up:

- In order to run the site, firstly you must enter the test folder, then the bin folder, and type 'source activate' to start flask.

- Then, enter the folder containing the files and type the following commands to set up flask.
- export FLASK_ENV=development to set the environment.
- export FLASK_APP=server.py to set the file flask should boot from.
- python init_db.py to initialize the database.
- python -m flask run --host=0.0.0.0 to boot the web app.

- Finally, go to http://webtech-46.napier.ac.uk:5000/ to play with the website!
