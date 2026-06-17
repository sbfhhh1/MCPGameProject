import unreal
facs=[x for x in dir(unreal) if "ubsurface" in x.lower()]
unreal.log("[Probe3] "+str(facs))
p=unreal.load_asset("/Game/TransformationVFX/SM2SM/jude/BurstJade/M_Burst_JadeDissolve")
sp=p.get_editor_property("subsurface_profile")
unreal.log("[Probe3] cur profile="+(sp.get_name() if sp else "None(default)"))