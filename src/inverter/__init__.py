# Expose a convenient main if needed: `python -m inverter`
from .app import InverterApp
from .config import Config
def main() -> None:
    app = InverterApp(Config())
    app.run()
