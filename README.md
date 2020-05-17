# Run Checked

I ran into the struggle, that when running backups via cron I was never quite sure if they succeeded.
Sure, I could rely on the cron error mails, but those are not generated when host is down entirely.
On my journey to a solution I stumbled across a nice tool called [Healthchecks.io](https://healthchecks.io/docs/).
It does two things: Alerting when the cron job fails and when the corn job was not executed according to its schedule.

First, I tried wrapping my more complex backup scripts into bash scripts - monitoring the exit code of commands and piping stdout into a variable to maintain the log in Healthchecks.
However, this proved to be quite difficult. Thus I wrote a small Python script to wrap my commands, gather stdout and stderr, and finally report everything back the my Healthchecks instance.


## How to use

This is no ready-made script. It is rather intended to be used as a library, to provide quick utility functions.

```python
from runchecked import HealthCheckedContext

with HealthCheckedContext(
    "...Your Healthchecks ping-back url here...",
    working_dir=".",  # Optionally set the general working directory
    enable_tty_output=None,  # Explicitly activate or deactive the echo to stdout. When left to None, it tries auto-detecting if the shell session is interactive
) as ctx:
    # Log some infos
    ctx.log.info("Backup started")

    # Set some environment variables global to the context
    ctx.set_env("Hello", "World")

    # Get the environment variable
    ctx.log.debug("Hello %s", ctx.get_env("Hello"))

    # Run some commands
    return_code = ctx.run(
      ["ls", "-alh", "."],  # commands are passed in the same way as in Python's `subprocess` library
      allow_fail=False,  # When true the context is not terminated, if the program exits with anything but 0
      timeout=None,  # Optional time for the program in seconds
      pass_env=True,  # If False only the system environment variables are passed, but not the context ones
    )
```

## License

[MIT License](./LICENSE) (c) Martin Peters *aka* FreakyBytes
