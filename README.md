# Releases e-mail

A simple script for generating a nicely formatted email from github/jenkins
release information.

## Quickstart

1. Install [Python 2.7](http://www.python.org/download/releases/2.7/), [pip](http://www.pip-installer.org/en/latest/installing.html) and [virtualenv](http://www.virtualenv.org/en/latest/virtualenv.html#installation).
2. Create a virtualenv and install the dependencies:

    ```shell
    $ virtualen env
    $ source env/bin/activate
    $ pip install -r requirements/development.txt
    ```

3. Run tests

    ```
    $ py.test test
    ```

4. Or run the program. Inside a git repo:

    ```
    $ export MANODERECHA_USER=<your manoderecha user>
    $ export MANODERECHA_PASSWORD=<your manoderecha password>
    $ ./release-email.py <Jenkins server URL> <Project's URL> <Jenkins job name>
    ```
