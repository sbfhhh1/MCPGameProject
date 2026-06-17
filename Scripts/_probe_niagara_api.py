import unreal
LOG="[NIAGAPI]"
def log(m): unreal.log_warning("{} {}".format(LOG,m))

# 1. 相关类是否存在
for cname in ["NiagaraEditorLibrary","NiagaraSystem","NiagaraEmitter","NiagaraScript",
              "NiagaraSystemFactoryNew","NiagaraEmitterFactoryNew","NiagaraEmitterHandle",
              "NiagaraStackEditorData","NiagaraClipboard","NiagaraMeshRendererProperties",
              "NiagaraStackFunctionInput","NiagaraStackModuleData","AssetToolsHelpers"]:
    log("class {} = {}".format(cname, hasattr(unreal, cname)))

# 2. NiagaraEditorLibrary 函数
if hasattr(unreal,"NiagaraEditorLibrary"):
    fns=[x for x in dir(unreal.NiagaraEditorLibrary) if not x.startswith("_")]
    log("NiagaraEditorLibrary fns: {}".format(fns))

# 3. NiagaraSystem 方法
if hasattr(unreal,"NiagaraSystem"):
    fns=[x for x in dir(unreal.NiagaraSystem) if not x.startswith("_") and ("emitter" in x.lower() or "param" in x.lower() or "override" in x.lower())]
    log("NiagaraSystem fns(subset): {}".format(fns))

# 4. 现有 NS_Return_SM 的发射器/数据接口
ns=unreal.EditorAssetLibrary.load_asset("/Game/TransformationVFX/Niagara/NS_Return_SM")
log("NS_Return_SM type={}".format(type(ns).__name__))
if hasattr(unreal,"NiagaraEditorLibrary"):
    try:
        eh=unreal.NiagaraEditorLibrary.get_emitter_handles(ns) if hasattr(unreal.NiagaraEditorLibrary,"get_emitter_handles") else None
        log("emitter_handles via lib = {}".format(eh))
    except Exception as e:
        log("get_emitter_handles err {}".format(e))
log("DONE")
