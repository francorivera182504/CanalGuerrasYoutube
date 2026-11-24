"""Run the authorized full render independently and record its final status."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import traceback

HERE = Path(__file__).resolve().parent.parent
STATUS = HERE / "_review_v2" / "render_status.json"
state = {
    "started": datetime.now().astimezone().isoformat(),
    "command": [sys.executable, "-u", "build.py"],
    "build_sha256_before": hashlib.sha256((HERE / "build.py").read_bytes()).hexdigest(),
    "status": "running",
}
STATUS.write_text(json.dumps(state, indent=2), encoding="utf-8")
try:
    with (HERE / "_review_v2" / "render.log").open("w", encoding="utf-8") as log:
        result = subprocess.run(state["command"], cwd=HERE, stdout=log, stderr=subprocess.STDOUT)
    state.update(status="completed" if result.returncode == 0 else "failed", exit_code=result.returncode)
except BaseException:
    state.update(status="failed", traceback=traceback.format_exc())
finally:
    state.update(
        finished=datetime.now().astimezone().isoformat(),
        build_sha256_after=hashlib.sha256((HERE / "build.py").read_bytes()).hexdigest(),
    )
    STATUS.write_text(json.dumps(state, indent=2), encoding="utf-8")

if state.get("exit_code") == 0:
    with (HERE / "_review_v2" / "verify_runner.log").open("w", encoding="utf-8") as log:
        result = subprocess.run([sys.executable, "-u", str(HERE / "_review_v2" / "verify_runner.py")], cwd=HERE, stdout=log, stderr=subprocess.STDOUT)
    sys.exit(result.returncode)
sys.exit(state.get("exit_code", 1))
