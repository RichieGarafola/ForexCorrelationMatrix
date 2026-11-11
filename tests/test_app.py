"""Exercise the Streamlit entry point without external market-data access."""

from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_synthetic_demo_renders_without_network():
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    app = AppTest.from_file(app_path, default_timeout=45).run()

    assert not app.exception
    assert app.title[0].value == "Forex Correlation Explorer"
    assert len(app.metric) == 3
    assert app.metric[0].value == "180"
    assert app.metric[1].value == "6"
