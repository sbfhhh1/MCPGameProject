# -*- coding: utf-8 -*-
import json
import unreal

OUT = r"C:/UE_Project/MCPGameProject/Scripts/_save_all_and_close_editor.json"


def main():
    result = {
        "save_dirty_packages": False,
        "save_current_level": False,
        "exit_requested": False,
    }

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

    unreal.log("[SaveAllAndClose] " + json.dumps(result, ensure_ascii=False))
    unreal.SystemLibrary.quit_editor()
    result["exit_requested"] = True
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
