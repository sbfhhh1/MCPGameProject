import unreal

paths = [
    "/Game/TransformationVFX/SM2SM/jude/20260613133607_ec021d65",
    "/Game/TransformationVFX/SM2SM/jude/20260613123723_f8ed59ab",
    "/Game/TransformationVFX/SM2SM/jude/20260613130638_a1276204",
]
for p in paths:
    sm = unreal.load_asset(p)
    if not sm:
        unreal.log_warning(f"[Nanite] missing {p}")
        continue
    try:
        ns = sm.get_editor_property("nanite_settings")
        enabled = ns.get_editor_property("enabled") if ns else None
        unreal.log(f"[Nanite] {sm.get_name()} nanite_enabled={enabled}")
    except Exception as e:
        unreal.log_warning(f"[Nanite] {sm.get_name()} err {e}")

# also check the burst actor's runtime mesh components nanite override
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
a = next((x for x in actors if x.get_actor_label() == "BP_Burst_SM_Test"), None)
if a:
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        n = c.get_name().replace(" ", "").replace("_", "")
        if any(e in n for e in ["StaticMeshA", "StaticMeshB", "StaticMeshC"]):
            sm = c.get_editor_property("static_mesh")
            try:
                ns = sm.get_editor_property("nanite_settings") if sm else None
                en = ns.get_editor_property("enabled") if ns else None
                unreal.log(f"[Nanite] comp {c.get_name()} mesh={sm.get_name() if sm else None} nanite={en}")
            except Exception as e:
                unreal.log_warning(f"[Nanite] comp err {e}")

unreal.log("[Nanite] DONE")
