import os
import sys
import logging
from io import StringIO
from pathlib import Path
from subprocess import Popen, PIPE, STDOUT
from typing import List, Optional, Dict
import time
from select import select
import urllib.request


class HealthCheckedContext(object):
    RUNNING = 1
    ERROR = 2
    DONE = 3
    FAILED = 4

    def __init__(
        self,
        healthckeck_url: str,
        working_dir: str = None,
        enable_tty_output: bool = None,
    ):
        self.healthckeck_url = healthckeck_url
        self.enable_tty_output = (
            enable_tty_output if enable_tty_output is not None else sys.stdout.isatty()
        )
        self.stdout_cache = StringIO()
        self.env: Dict[str, str] = {}
        self.working_dir = Path(working_dir) if working_dir else None

        self.status: Optional[int] = None

        self._setup_logging()
        self.log = logging.getLogger("HC")

    def __enter__(self):
        self.status = HealthCheckedContext.RUNNING
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            # context close due to exception
            self.log.error(
                "Error while context execution: %s",
                exc_value,
                exc_info=(exc_type, exc_value, traceback),
            )
            self.status = HealthCheckedContext.FAILED
        else:
            self.status = (
                HealthCheckedContext.DONE
                if self.status == HealthCheckedContext.RUNNING
                else HealthCheckedContext.FAILED
            )

        if self.status == HealthCheckedContext.DONE:
            self.log.info("Exit execution context successfully")
            self._report(True)
        else:
            self.log.error("Exit execution context unsuccessfully")
            self._report(False)
        self.stdout_cache.close()

    def run(
        self,
        args: List = [],
        allow_fail: bool = False,
        timeout: int = None,
        pass_env: bool = True,
    ) -> Optional[int]:

        if not self.status == HealthCheckedContext.RUNNING:
            self.log.error("Skip '%s' since the context failed", " ".join(args))
            return None

        try:
            start_time = time.time()
            with Popen(
                args,
                stdout=PIPE,
                stderr=STDOUT,
                universal_newlines=True,
                cwd=self.working_dir,
                env={**os.environ, **(self.env if pass_env else {})},
            ) as proc:
                while True:
                    # wait for the stdout to be ready
                    read_poll = select([proc.stdout], [], [], 100)[0]
                    if len(read_poll) > 0:
                        # there is something to read
                        buf = read_poll[0].read()
                        self.stdout_cache.write(buf)
                        if self.enable_tty_output:
                            sys.stdout.write(buf)

                    # check if program terminated
                    return_code = proc.poll()
                    if return_code == 0:
                        return return_code
                    elif return_code is not None:
                        self.log.warning("Exit %d", return_code)
                        if allow_fail is not True:
                            self.status = HealthCheckedContext.ERROR
                        return return_code

                    # check if timeout passed
                    if timeout is not None and timeout > 0:
                        if time.time() - start_time > timeout:
                            self.log.warning("Terminate program due to timeout")
                            proc.kill()
        except:
            self.log.exception(
                "Execution of '%s' failed with exception", " ".join(args), exc_info=True
            )
            self.status = HealthCheckedContext.ERROR
            return None

    def set_env(self, key: str, value: str) -> None:
        self.env[key] = value

    def get_env(self, key: str) -> str:
        return self.env[key]

    def _setup_logging(self, level=logging.INFO) -> None:
        log_root = logging.getLogger()
        log_root.setLevel(level)
        log_format = logging.Formatter("%(asctime)s %(levelname)-8s %(message)s")

        # setting up logging to stdout cache
        cache_stream_handler = logging.StreamHandler(self.stdout_cache)
        cache_stream_handler.setFormatter(log_format)
        log_root.addHandler(cache_stream_handler)

        if self.enable_tty_output:
            # enable logging to stdout
            stdout_stream_handler = logging.StreamHandler(sys.stdout)
            stdout_stream_handler.setFormatter(log_format)
            log_root.addHandler(stdout_stream_handler)

    def _report(self, success: bool):

        url = self.healthckeck_url
        if not success:
            url = f"{url}fail" if url[-1] == "/" else f"{url}/fail"

        for try_count in range(3):
            try:
                data = self.stdout_cache.getvalue().encode("utf-8")
                req = urllib.request.Request(
                    url,
                    method="POST",
                    data=data,
                    headers={"Content-Type": "text/plain"},
                )
                resp = urllib.request.urlopen(req)

                if resp is not None:
                    text = resp.read().decode("utf-8")
                    if text.lower().startswith("ok"):
                        # successfull report
                        return
            except:
                self.log.warning(
                    "Failed to report context results (try %d)",
                    try_count,
                    exc_info=True,
                )

            # wait a bit before re-trying
            time.sleep(2)

        # report failed multiple times
        self.log.error("Finally failed to report results")
