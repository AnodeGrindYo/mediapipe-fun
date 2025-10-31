import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent / "src"))
from inverter.app import InverterApp
from inverter.config import Config

def main() -> None:
    cfg = Config()
    app = InverterApp(cfg)
    app.run()

if __name__ == "__main__":
    main()
