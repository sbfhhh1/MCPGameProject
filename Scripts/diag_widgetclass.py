import unreal

def get_all_actors():
    s = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    return list(s.get_all_level_actors())

host_cls = unreal.load_class(None, "/Script/MCPGameProject.BronzeExhibitHost")
widget_cls = unreal.load_class(None, "/Script/MCPGameProject.BronzeExhibitWidget")

hosts = [a for a in get_all_actors() if a.get_class() == host_cls]
unreal.log("[DIAG] host count = %d" % len(hosts))
if hosts:
    h = hosts[0]
    wc = h.get_editor_property("widget_class")
    unreal.log("[DIAG] Host.WidgetClass = %s" % (wc.get_name() if wc else "None"))
    unreal.log("[DIAG] Host.WidgetClass path = %s" % (wc.get_path_name() if wc else "None"))
    unreal.log("[DIAG] C++ widget class path = %s" % widget_cls.get_path_name())
    unreal.log("[DIAG] Is C++ class itself? %s" % (wc == widget_cls))

# Check whether the C++ class now has ArtifactImage property (proves new code loaded)
props = [p.get_name() for p in unreal.BronzeExhibitWidget.__dict__] if hasattr(unreal, "BronzeExhibitWidget") else []
unreal.log("[DIAG] unreal.BronzeExhibitWidget exposed = %s" % hasattr(unreal, "BronzeExhibitWidget"))
