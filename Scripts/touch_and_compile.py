"""
Run from the UE Python console. This runs on Windows, so rewriting the source files
here produces a REAL Windows filesystem change event that Live Coding's watcher detects
(unlike edits made via the sandbox mount). Then it triggers a Live Coding compile.
"""
import os, time, unreal

FILES = [
    r"C:\UE_Project\MCPGameProject\Source\MCPGameProject\BronzeExhibit\BronzeExhibitWidget.cpp",
    r"C:\UE_Project\MCPGameProject\Source\MCPGameProject\BronzeExhibit\BronzeExhibitWidget.h",
]

for f in FILES:
    try:
        with open(f, "r", encoding="utf-8") as fh:
            data = fh.read()
        # Append + remove a harmless newline to force a real write/modify event.
        with open(f, "w", encoding="utf-8") as fh:
            fh.write(data)
        # bump mtime explicitly too
        os.utime(f, None)
        unreal.log("[TouchCompile] rewrote %s (%d bytes)" % (os.path.basename(f), len(data)))
    except Exception as e:
        unreal.log_error("[TouchCompile] failed on %s: %s" % (f, e))

# Give the watcher a moment to register the change.
time.sleep(1.5)
unreal.log("[TouchCompile] triggering LiveCoding.Compile ...")
unreal.SystemLibrary.execute_console_command(None, "LiveCoding.Compile")
unreal.log("[TouchCompile] compile requested. Watch the Live Coding console window.")
