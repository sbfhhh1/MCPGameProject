#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "MorphVortexEditorLibrary.generated.h"

class UNiagaraSystem;

/**
 * 编辑器专用工具：用 Niagara 编辑器 API 给粒子系统的发射器 Update 堆栈添加内置力模块。
 * 用于给 P_Morph_5_SM 程序化加 VortexForce（脚本/MCP 无法直接增删 Niagara 模块，需用编辑器 C++ API）。
 */
UCLASS()
class UMorphVortexEditorLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	/**
	 * 给 Niagara 系统所有发射器的「粒子 Update」堆栈添加一个内置模块（按模块资产路径）。
	 * @param System          目标 Niagara 系统（会被修改并保存）
	 * @param ModuleAssetPath 模块脚本资产路径，如 /Niagara/Modules/Update/Forces/VortexForce.VortexForce
	 * @return 成功添加的发射器数量（0 表示失败/没改动）
	 */
	UFUNCTION(BlueprintCallable, Category="MorphVortex|Editor")
	static int32 AddModuleToParticleUpdate(UNiagaraSystem* System, const FString& ModuleAssetPath);
};
