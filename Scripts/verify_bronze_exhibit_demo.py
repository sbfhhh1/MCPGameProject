import unreal


MAP_PATH = "/Game/TobiiEyeTracker5/Examples/ScreenBasedPrefabDemo"
BRONZE_TAG_PREFIX = "BronzeExhibit."
PRESERVE_TAG_PREFIX = "BronzeExhibit.Preserve."
LEGACY_GEOMETRY_LABELS = {
    "Tobii_Floor",
    "CubeLeft",
    "CubeMiddle",
    "CubeRight",
    "Sphere",
    "Capsule",
}


def fail(message):
    raise RuntimeError(f"[BronzeExhibitVerify] {message}")


def get_all_actors():
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if subsystem:
        return list(subsystem.get_all_level_actors())
    return list(unreal.EditorLevelLibrary.get_all_level_actors())


def has_tag(actor, tag):
    return any(str(existing) == tag for existing in actor.tags)


def components_are_hidden(actor):
    components = list(actor.get_components_by_class(unreal.SceneComponent))
    return all(
        not component.get_editor_property("visible")
        and component.get_editor_property("hidden_in_game")
        for component in components
    )


world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
if not world:
    fail(f"Could not load {MAP_PATH}")

actors = get_all_actors()
labels = {actor.get_actor_label(): actor for actor in actors}
names = {actor.get_name() for actor in actors}

host_class = unreal.load_class(None, "/Script/MCPGameProject.BronzeExhibitHost")
stage_class = unreal.load_class(None, "/Script/MCPGameProject.BronzeArtifactStage")
if not host_class or not stage_class:
    fail("MCPGameProject Bronze Exhibit classes are not loaded")

host_matches = [actor for actor in actors if has_tag(actor, f"{BRONZE_TAG_PREFIX}Host")]
stage_matches = [actor for actor in actors if has_tag(actor, f"{BRONZE_TAG_PREFIX}ArtifactStage")]
if len(host_matches) != 1:
    fail(f"Expected one Bronze Exhibit Host, found {len(host_matches)}")
if len(stage_matches) != 1:
    fail(f"Expected one Bronze Exhibit ArtifactStage, found {len(stage_matches)}")
if host_matches[0].get_class() != host_class:
    fail(f"Bronze Exhibit Host has unexpected class {host_matches[0].get_class().get_name()}")
if stage_matches[0].get_class() != stage_class:
    fail(f"Bronze Exhibit ArtifactStage has unexpected class {stage_matches[0].get_class().get_name()}")
if host_matches[0].get_editor_property("artifact_stage") != stage_matches[0]:
    fail("Bronze Exhibit Host is not bound to the ArtifactStage")
chapters = list(host_matches[0].get_editor_property("chapters"))
page_count = sum(len(list(chapter.get_editor_property("pages"))) for chapter in chapters)
if len(chapters) != 7 or page_count != 16:
    fail(f"Expected 7 chapters and 16 pages, found {len(chapters)} chapters and {page_count} pages")
artifact_component = stage_matches[0].get_editor_property("artifact_mesh")
if not artifact_component or not artifact_component.get_editor_property("visible"):
    fail("Bronze Exhibit ArtifactStage is hidden")

missing_legacy = sorted(LEGACY_GEOMETRY_LABELS - set(labels))
if missing_legacy:
    fail(f"Legacy geometry was removed instead of hidden: {missing_legacy}")
visible_legacy = sorted(
    label for label in LEGACY_GEOMETRY_LABELS if not components_are_hidden(labels[label])
)
if visible_legacy:
    fail(f"Legacy test geometry is still visible: {visible_legacy}")

text_actors = [actor for actor in actors if isinstance(actor, unreal.TextRenderActor)]
if not text_actors:
    fail("Expected the legacy TextRenderActor to remain in the level")
visible_text = [actor.get_actor_label() for actor in text_actors if not components_are_hidden(actor)]
if visible_text:
    fail(f"Legacy TextRender actors are still visible: {visible_text}")

tobii_actors = [actor for actor in actors if actor.get_class().get_name() == "TobiiScreenBasedDemoActor"]
active_tobii = [
    actor.get_actor_label()
    for actor in tobii_actors
    if actor.is_actor_tick_enabled() or not actor.is_hidden() or not components_are_hidden(actor)
]
if active_tobii:
    fail(f"Legacy Tobii demo actors are not disabled and hidden: {active_tobii}")

legacy_hud = [
    actor
    for actor in actors
    if "hud" in actor.get_actor_label().lower() or "hud" in actor.get_class().get_name().lower()
]
active_hud = [
    actor.get_actor_label()
    for actor in legacy_hud
    if actor.is_actor_tick_enabled() or not actor.is_hidden() or not components_are_hidden(actor)
]
if active_hud:
    fail(f"Legacy HUD actors are still active: {active_hud}")

preserve_tags = [
    str(tag)
    for tag in host_matches[0].tags
    if str(tag).startswith(PRESERVE_TAG_PREFIX)
]
if not preserve_tags:
    fail("Host does not record any key unknown actors for preservation")
preserved_names = {tag[len(PRESERVE_TAG_PREFIX):] for tag in preserve_tags}
missing_preserved = sorted(preserved_names - names)
if missing_preserved:
    fail(f"Key unknown actors were not preserved: {missing_preserved}")

unreal.log(
    f"[BronzeExhibitVerify] Passed: {len(chapters)} chapters/{page_count} pages, "
    "Host/Stage present, legacy visuals and HUD disabled, "
    f"preserved context actors={sorted(preserved_names)}"
)
