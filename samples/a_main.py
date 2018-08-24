from argdeco import main
import logging
logging.basicConfig()

log = logging.getLogger()

@main
def main():
    log.debug("debug")
    log.info("info")
    log.warning("warning")
    log.error("error")


main(verbosity=True)
