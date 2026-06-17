"""Import the dark-matte bronze PNGs (white bg removed) into /Game/BronzeExhibit/Visual.
Run from the UE Python console:
    C:/UE_Project/MCPGameProject/Scripts/import_dark_artifacts.py
"""
import os, unreal

SRC = r"C:\UE_Project\MCPGameProject\Content\BronzeExhibit\SourceArt"
DEST = "/Game/BronzeExhibit/Visual"

names = ["T_Bronze_Ding_Dark", "T_Bronze_Zun_Dark", "T_Bronze_Gui_Dark"]
tools = unreal.AssetToolsHelpers.get_asset_tools()
for n in names:
    src = os.path.join(SRC, n + ".png")
    if not os.path.isfile(src):
        unreal.log_error("[ImportDark] missing " + src); continue
    ap = "%s/%s" % (DEST, n)
    if unreal.EditorAssetLibrary.does_asset_exist(ap):
        unreal.EditorAssetLibrary.delete_asset(ap)
    t = unreal.AssetImportTask()
    t.filename = src; t.destination_path = DEST; t.destination_name = n
    t.automated = True; t.replace_existing = True; t.save = True
    tools.import_asset_tasks([t])
    unreal.log("[ImportDark] imported " + ap if unreal.EditorAssetLibrary.does_asset_exist(ap) else "[ImportDark] FAILED " + ap)
unreal.EditorAssetLibrary.save_directory(DEST, only_if_is_dirty=False)
unreal.log("[ImportDark] done")
