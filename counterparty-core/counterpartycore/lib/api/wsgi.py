import logging
import multiprocessing
import os
import signal
import sys
import threading

import gunicorn.app.base
import waitress
import waitress.server
from counterpartycore.lib import config, database, ledger, log, util
from counterpartycore.lib.api import api_watcher
from counterpartycore.lib.api.util import BackendHeight
from gunicorn import util as gunicorn_util
from gunicorn.arbiter import Arbiter
from gunicorn.errors import AppImportError
from werkzeug.serving import make_server

multiprocessing.set_start_method("spawn", force=True)

logger = logging.getLogger(config.LOGGER_NAME)


def refresh_current_state(ledger_db, state_db):
    util.CURRENT_BLOCK_INDEX = api_watcher.get_last_block_parsed(state_db)
    util.CURRENT_BACKEND_HEIGHT = BackendHeight().get()
    if util.CURRENT_BLOCK_INDEX:
        last_block = ledger.get_block(ledger_db, util.CURRENT_BLOCK_INDEX)
        if last_block:
            util.CURRENT_BLOCK_TIME = last_block["block_time"]
        else:
            util.CURRENT_BLOCK_TIME = 0
    else:
        util.CURRENT_BLOCK_TIME = 0
        util.CURRENT_BLOCK_INDEX = 0

    if util.CURRENT_BACKEND_HEIGHT > util.CURRENT_BLOCK_INDEX:
        logger.debug(
            f"Counterparty is currently behind Bitcoin Core. ({util.CURRENT_BLOCK_INDEX} < {util.CURRENT_BACKEND_HEIGHT})"
        )
    elif util.CURRENT_BACKEND_HEIGHT < util.CURRENT_BLOCK_INDEX:
        logger.debug(
            f"Bitcoin Core is currently behind the network. ({util.CURRENT_BLOCK_INDEX} > {util.CURRENT_BACKEND_HEIGHT})"
        )


class NodeStatusCheckerThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self, name="NodeStatusChecker")
        self.state_db = database.get_db_connection(config.STATE_DATABASE)
        self.ledger_db = database.get_db_connection(config.DATABASE)
        self.stop_event = threading.Event()

    def run(self):
        logger.debug("Starting NodeStatusChecker thread...")
        try:
            while not self.stop_event.is_set():
                refresh_current_state(self.ledger_db, self.state_db)
                self.stop_event.wait(timeout=1)
        finally:
            self.state_db.close()
            self.ledger_db.close()

    def stop(self):
        self.stop_event.set()
        if self.is_alive():
            self.join()


class GunicornArbiter(Arbiter):
    def __init__(self, app):
        super().__init__(app)
        self.app = app

    def handle_winch(self):
        pass

    def spawn_worker(self):
        self.worker_age += 1
        worker = self.worker_class(
            self.worker_age,
            self.pid,
            self.LISTENERS,
            self.app,
            self.timeout / 2.0,
            self.cfg,
            self.log,
        )
        self.cfg.pre_fork(self, worker)
        pid = os.fork()
        if pid != 0:
            worker.pid = pid
            self.WORKERS[pid] = worker
            return pid

        # Child process
        global logger  # noqa F811
        worker.pid = os.getpid()
        logger = log.re_set_up(f".gunicorn.{worker.pid}", api=True)
        try:
            gunicorn_util._setproctitle(f"worker [{self.proc_name}]")
            logger.trace("Booting Gunicorn worker with pid: %s", worker.pid)
            self.cfg.post_fork(self, worker)
            worker.init_process()
            sys.exit(0)
        except SystemExit:
            raise
        except AppImportError:
            self.log.warning("Exception while loading the application", exc_info=True)
            sys.stderr.flush()
            sys.exit(self.APP_LOAD_ERROR)
        except Exception:
            self.log.exception("Exception in worker process")
            if not worker.booted:
                sys.exit(self.WORKER_BOOT_ERROR)
            sys.exit(-1)
        finally:
            logger.info("Worker exiting (pid: %s)", worker.pid)
            try:
                worker.tmp.close()
                self.cfg.worker_exit(self, worker)
            except Exception:
                logger.warning("Exception during worker exit")

    def kill_all_workers(self):
        for pid in list(self.WORKERS.keys()):
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass


class GunicornApplication(gunicorn.app.base.BaseApplication):
    def __init__(self, app, args=None):
        self.options = {
            "bind": "%s:%s" % (config.API_HOST, config.API_PORT),
            "timeout": 10,
            "graceful_timeout": 10,
            "max_requests": 1000,
            "max_requests_jitter": 250,
            "workers": config.GUNICORN_WORKERS,
            "worker_class": "gthread",
            "daemon": True,
            "threads": config.GUNICORN_THREADS_PER_WORKER,
            "loglevel": "trace",
            "access-logfile": "-",
            "errorlog": "-",
            "capture_output": True,
        }
        self.application = app
        self.args = args
        self.arbiter = None
        self.ledger_db = None
        self.state_db = None
        self.current_state_thread = NodeStatusCheckerThread()
        super().__init__()

    def load_config(self):
        gunicorn_config = {
            key: value
            for key, value in self.options.items()
            if key in self.cfg.settings and value is not None
        }
        for key, value in gunicorn_config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        self.current_state_thread.start()
        return self.application

    def run(self):
        try:
            self.arbiter = GunicornArbiter(self)
            self.arbiter.run()
        except RuntimeError as e:
            logger.error("Error in GUnicorn: %s", e)
            sys.stderr.flush()
            sys.exit(1)

    def stop(self):
        logger.warning("Stopping Gunicorn")
        self.current_state_thread.stop()
        if self.arbiter:
            self.arbiter.kill_all_workers()


class WerkzeugApplication:
    def __init__(self, app, args=None):
        self.app = app
        self.args = args
        self.current_state_thread = NodeStatusCheckerThread()
        self.server = make_server(config.API_HOST, config.API_PORT, self.app, threaded=True)

    def run(self):
        self.current_state_thread.start()
        self.server.serve_forever()

    def stop(self):
        self.current_state_thread.stop()
        self.server.shutdown()
        self.server.server_close()


class WaitressApplication:
    def __init__(self, app, args=None):
        self.app = app
        self.args = args
        self.current_state_thread = NodeStatusCheckerThread()
        self.server = waitress.server.create_server(
            self.app, host=config.API_HOST, port=config.API_PORT, threads=config.WAITRESS_THREADS
        )

    def run(self):
        self.current_state_thread.start()
        self.server.run()

    def stop(self):
        self.current_state_thread.stop()
        self.server.close()


class WSGIApplication:
    def __init__(self, app, args=None):
        self.app = app
        self.args = args
        logger.info(f"Starting WSGI Server: {config.WSGI_SERVER}")
        if config.WSGI_SERVER == "gunicorn":
            self.server = GunicornApplication(self.app, self.args)
        elif config.WSGI_SERVER == "werkzeug":
            self.server = WerkzeugApplication(self.app, self.args)
        else:
            self.server = WaitressApplication(self.app, self.args)

    def run(self):
        logger.info("Starting WSGI Server thread...")
        self.server.run()

    def stop(self):
        logger.info("Stopping WSGI Server thread...")
        self.server.stop()
