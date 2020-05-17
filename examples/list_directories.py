
from runchecked import HealthCheckedContext

with HealthCheckedContext(
    "http://localhost/1234",
    working_dir=".",
) as ctx:
    ctx.set_env("Hello", "World")
    ctx.log.info("Start")
    ctx.run(["ls", "-alh", "."])
    ctx.run(["restic", "help"])
    ctx.run(['env'])
    # ctx.run(["/bin/false"])
    ctx.log.info("Done")
