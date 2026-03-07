import os

os.environ["LOGFIRE_DISABLE_PLUGINS"] = "true"
os.environ["LOGFIRE_PYDANTIC_RECORD"] = "off"

from lazypr import main

if __name__ == "__main__":
    main()
