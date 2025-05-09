# run_app.py (in root directory)
import streamlit.web.cli as stcli
import sys
import os

if __name__ == '__main__':
    sys.argv = ["streamlit", "run", "src/app/app.py"]
    sys.exit(stcli.main())