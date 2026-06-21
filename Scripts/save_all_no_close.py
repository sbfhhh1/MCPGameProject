# -*- coding: utf-8 -*-
import json
import unreal

OUT = r"C:/UE_Project/MCPGameProject/Scripts/_save_all_no_close.json"


result = {}
try:
    result["save_current_level"] = bool(unreal.EditorLevelLibrary.save_current_level())
except Exception as exc:
    result["save_current_level_error"] = str(exc)

try:
    result["save_dirty_packages"] = bool(
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    )
except Exception as exc:
    result["save_dirty_packages_error"] = str(exc)

with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(result, fh, ensure_ascii=False, indent=2)

unreal.log("[SaveAllNoClose] " + json.dumps(result, ensure_ascii=False))
