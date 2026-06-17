"""
Force-compile the MCPGameProject editor module from inside the UE Python console,
without needing a separate terminal. Runs Build.bat and streams the result to the
UE Output Log. Note: if the editor currently holds the DLL lock, the LINK step may
fail, but the COMPILE step will still refresh the .obj so a later restart-rebuild is clean.
"""
import subprocess
import os
import unreal

BUILD_BAT = r"C:\Program Files\Epic Games\UE_5.7\Engine\Build\BatchFiles\Build.bat"
UPROJECT  = r"C:\UE_Project\MCPGameProject\MCPGameProject.uproject"

cmd = [
    BUILD_BAT,
    "MCPGameProjectEditor", "Win64", "Development",
    "-Project=" + UPROJECT,
    "-WaitMutex", "-FromMsBuild",
]

unreal.log("[ForceBuild] launching: " + " ".join(cmd))

try:
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=600,
        shell=False,
    )
    out = proc.stdout or ""
    # Print the tail of the build output to the UE log
    tail = "\n".join(out.splitlines()[-40:])
    unreal.log("[ForceBuild] ===== BUILD OUTPUT TAIL =====\n" + tail)
    unreal.log("[ForceBuild] return code = %d" % proc.returncode)
    if proc.returncode == 0:
        unreal.log("[ForceBuild] SUCCESS")
    else:
        unreal.log_error("[ForceBuild] FAILED rc=%d" % proc.returncode)
except Exception as e:
    unreal.log_error("[ForceBuild] EXCEPTION: %s" % e)
