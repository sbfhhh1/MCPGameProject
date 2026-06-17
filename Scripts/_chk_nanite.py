import unreal, json
out={}
for p in ["/Game/TransformationVFX/SM2SM/jude/20260613133607_ec021d65",
          "/Game/TransformationVFX/SM2SM/jude/20260613123723_f8ed59ab",
          "/Game/TransformationVFX/SM2SM/jude/20260613130638_a1276204"]:
    sm=unreal.load_asset(p)
    if sm:
        ns=sm.get_editor_property("nanite_settings")
        out[p.split('/')[-1]]=bool(ns.get_editor_property("enabled"))
open("C:/UE_Project/MCPGameProject/Scripts/_nan.json","w").write(json.dumps(out,ensure_ascii=False,indent=2))
