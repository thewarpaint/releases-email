# Plugins

For some third-party plugins, you'll need to configure some environmental variables if you don't want to pass
them at runtime.

## manoderecha

    ```bash
    $ export MANODERECHA_USER=<your manoderecha user>
    $ export MANODERECHA_PASSWORD=<your manoderecha password>
    ```

## JIRA

Note: for the JIRA API base, be sure to use HTTPS. Otherwise, basic authentication will not work.

    ```bash
    $ export JIRA_API_BASE=<your JIRA API base>
    $ export JIRA_USERNAME=<your JIRA username>
    $ export JIRA_PASSWORD=<your JIRA password>
    ```