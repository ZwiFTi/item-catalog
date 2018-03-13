# Catalog App

## Table of Contents

* [Description](#description)
* [Installation](#installation)
* [JSON Endpoints](#REST)
* [Contributing](#contributing)
* [Known issues](#known)
* [License](#known)

## Description

This is a Udacity fullstack nanodegree project. The application demonstrates
a couple of interesting methods of web applications. In its core, its an Item Catalog,
but behind the scenes are these techniques:

- Implementation of Python Flask framework
- Mapping of HTTP methods to CRUD operations
- User registration and authentication system (third-party OAuth authentication)
- RESTful web application with JSON endpoints

Registered users will have the ability to post, edit and delete their own items.

## Installation

1. Make sure you have Vagrant, VirtualBox
2. Make sure you have the Udacity repo
`git clone https://github.com/udacity/fullstack-nanodegree-vm.git`
3. cd into the vagrant directory, then:

**In terminal:**

    git clone https://github.com/ZwiFTi/item-catalog.git
    vagrant up && vagrant ssh

    cd /vagrant/item-catalog/

    python populate_db.py
    python project.py

    Go to localhost:5000

## RESTful (JSON Endpoints)

For individual items:
    /catalog/<catalog_name>/<catalog_item_name>/JSON

For entire catalogs:
    /JSON


## Contributing

This project is a practice project, and is therefor not open for contribution.


## Known issues

There is no known issues to date.


## License

The contents of this repository are covered under the [MIT License](LICENSE).
