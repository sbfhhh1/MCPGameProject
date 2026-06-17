import unreal
LOG="[SHARDGEOM]"
def log(m): unreal.log_warning("{} {}".format(LOG,m))

orig=unreal.EditorAssetLibrary.load_asset("/Game/TransformationVFX/SM2SM/jude/20260613133607_ec021d65")
if orig:
    b=orig.get_bounding_box()
    log("ORIG ec021d65 min=({:.3f},{:.3f},{:.3f}) max=({:.3f},{:.3f},{:.3f}) center=({:.3f},{:.3f},{:.3f}) size=({:.3f},{:.3f},{:.3f})".format(
        b.min.x,b.min.y,b.min.z, b.max.x,b.max.y,b.max.z,
        (b.min.x+b.max.x)/2,(b.min.y+b.max.y)/2,(b.min.z+b.max.z)/2,
        b.max.x-b.min.x,b.max.y-b.min.y,b.max.z-b.min.z))

shards=unreal.EditorAssetLibrary.list_assets("/Game/TransformationVFX/SM2SM/jude/Shards/jadeA", recursive=True, include_folder=False)
mn=[1e9,1e9,1e9]; mx=[-1e9,-1e9,-1e9]; n=0
for a in shards:
    o=unreal.EditorAssetLibrary.load_asset(a)
    if isinstance(o, unreal.StaticMesh):
        b=o.get_bounding_box()
        for i,(lo,hi) in enumerate([(b.min.x,b.max.x),(b.min.y,b.max.y),(b.min.z,b.max.z)]):
            mn[i]=min(mn[i],lo); mx[i]=max(mx[i],hi)
        n+=1
log("SHARDS jadeA n={} assembled min=({:.3f},{:.3f},{:.3f}) max=({:.3f},{:.3f},{:.3f}) center=({:.3f},{:.3f},{:.3f}) size=({:.3f},{:.3f},{:.3f})".format(
    n, mn[0],mn[1],mn[2], mx[0],mx[1],mx[2],
    (mn[0]+mx[0])/2,(mn[1]+mx[1])/2,(mn[2]+mx[2])/2, mx[0]-mn[0],mx[1]-mn[1],mx[2]-mn[2]))
log("DONE")
