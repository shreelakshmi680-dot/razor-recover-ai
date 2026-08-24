import os
from streamlit.testing.v1 import AppTest

# Construct the absolute path to dashboard/app.py
APP_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../dashboard/app.py"))

def test_dashboard_renders_without_crashing():
    """Simulates loading dashboard/app.py and ensures zero unhandled exceptions."""
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()
    assert not at.exception

def test_batch_benchmark_button_flow():
    """Simulates clicking the 50-record batch execution button."""
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()
    if len(at.button) > 0:
        at.button[0].click().run()
        assert not at.exception