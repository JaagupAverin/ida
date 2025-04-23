from textwrap import dedent


class HelpStrings:
    class JsonFields:
        HOST_URL: str = dedent("""
            [u]url[/u]*: https/git URL of a git server that hosts required projects.

            HTTPS example:
            [code]"hosts: {
                "google": {
                    "url": "https://github.com/google",
                    ...
                }
            }[/code]
        """)

        PROJECT_HOST: str = dedent("""
            [u]host[/u]*: Name of the host that has this project.

            The final project URL is resolved as: <host.url>/<project.name>.

            Basic example:
            [code]"hosts": {
                "libs-provider": {
                    "url": "https://bitbucket.org/libs-provider",
                    ...
                }
            },
            "projects": {
                "lib-a": {
                    // Resolves to 'https://bitbucket.org/libs-provider/lib-a'
                    "host": "libs-provider",
                    ...
                },
                "lib-b": {
                    // Resolves to 'https://bitbucket.org/libs-provider/lib-b'
                    "host": "libs-provider",
                    ...
                }
            }[/code]
        """)


class ErrorStrings:
    INVALID_WORKSPACE_JSON: str = "Failed to parse workspace.json."
