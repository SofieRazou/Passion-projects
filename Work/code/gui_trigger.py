import sys
import time
import subprocess
import threading
from pathlib import Path

import matlab.engine


UDP_SCRIPT = Path("udp.py").resolve()
GUI_SCRIPT = Path("spring_sim.py").resolve()

MATLAB_SCRIPT = Path(
    r"C:\Users\javot\Documents\MATLAB\Bern\simulink\sofia_udp_test.m"
)

matlab_engine = None
matlab_error = None


def run_matlab_script() -> None:
    """Start MATLAB and run the MATLAB script without blocking the GUI."""
    global matlab_engine, matlab_error

    try:
        if not MATLAB_SCRIPT.exists():
            raise FileNotFoundError(
                f"MATLAB script not found: {MATLAB_SCRIPT}"
            )

        print("Starting MATLAB...")

        matlab_engine = matlab.engine.start_matlab()

        # Change MATLAB's current folder to the script folder.
        matlab_engine.cd(
            str(MATLAB_SCRIPT.parent),
            nargout=0,
        )

        print(f"Running MATLAB script: {MATLAB_SCRIPT.name}")

        # Call the script using its filename without ".m".
        matlab_engine.feval(
            MATLAB_SCRIPT.stem,
            nargout=0,
        )

        print("MATLAB script completed.")

    except Exception as error:
        matlab_error = error
        print(f"MATLAB error: {error}")


def terminate_process(process: subprocess.Popen | None) -> None:
    """Terminate a subprocess safely."""
    if process is None:
        return

    if process.poll() is None:
        process.terminate()

        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def main() -> None:
    global matlab_engine

    udp_process = None
    gui_process = None

    try:
        if not UDP_SCRIPT.exists():
            raise FileNotFoundError(
                f"UDP script not found: {UDP_SCRIPT}"
            )

        if not GUI_SCRIPT.exists():
            raise FileNotFoundError(
                f"GUI script not found: {GUI_SCRIPT}"
            )

        # Start MATLAB in a separate thread so it does not block Python.
        matlab_thread = threading.Thread(
            target=run_matlab_script,
            name="MATLABThread",
            daemon=True,
        )
        matlab_thread.start()

        # Start the UDP/shared-memory producer first.
        print("Starting UDP process...")

        udp_process = subprocess.Popen(
            [sys.executable, str(UDP_SCRIPT)]
        )

        # Give the UDP process time to create shared memory.
        time.sleep(2)

        # Start the PyQt GUI.
        print("Starting GUI...")

        gui_process = subprocess.Popen(
            [sys.executable, str(GUI_SCRIPT)]
        )

        # Keep launcher alive until the GUI closes.
        gui_process.wait()

    except KeyboardInterrupt:
        print("\nLauncher interrupted by user.")

    except Exception as error:
        print(f"Launcher error: {error}")

    finally:
        print("Closing processes...")

        terminate_process(gui_process)
        terminate_process(udp_process)

        if matlab_engine is not None:
            try:
                matlab_engine.quit()
            except Exception as error:
                print(f"Could not close MATLAB cleanly: {error}")

        print("GUI execution terminated.")


if __name__ == "__main__":
    main()
