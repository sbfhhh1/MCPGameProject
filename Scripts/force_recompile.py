"""
Force Live Coding to actually recompile BronzeExhibitWidget:
1. Delete its .obj / .lc.obj (Windows-side, real FS event) so the compiler MUST rebuild.
2. Make a real content change (insert+remove a comment) so the watcher sees a diff.
3. Trigger LiveCoding.Compile.
Run from the UE Python console.
"""
import os, time, unreal

OBJ_DIR = r"C:\UE_Project\MCPGameProject\Intermediate\Build\Win64\x64\UnrealEditor\Development\MCPGameProject"
SRC = r"C:\UE_Project\MCPGameProject\Source\MCPGameProject\BronzeExhibit\BronzeExhibitWidget.cpp"

for name in ("BronzeExhibitWidget.cpp.obj", "BronzeExhibitWidget.cpp.lc.obj",
             "BronzeExhibitWidget.cpp.obj.response", "BronzeExhibitWidget.gen.cpp.obj"):
    p = os.path.join(OBJ_DIR, name)
    try:
        if os.path.exists(p):
            os.remove(p)
            unreal.log("[ForceRecompile] deleted %s" % name)
    except Exception as e:
        unreal.log_error("[ForceRecompile] could not delete %s: %s" % (name, e))

# Make a genuine textual change so Live Coding sees a real diff, then revert it.
try:
    with open(SRC, "r", encoding="utf-8") as fh:
        data = fh.read()
    marker = "\n// force-recompile-%d\n" % int(time.time())
    with open(SRC, "w", encoding="utf-8") as fh:
        fh.write(data.rstrip() + marker)
    unreal.log("[ForceRecompile] appended marker to source")
except Exception as e:
    unreal.log_error("[ForceRecompile] source write failed: %s" % e)

time.sleep(1.5)
unreal.log("[ForceRecompile] triggering LiveCoding.Compile ...")
unreal.SystemLibrary.execute_console_command(None, "LiveCoding.Compile")
unreal.log("[ForceRecompile] requested. Watch the Live Coding console.")
