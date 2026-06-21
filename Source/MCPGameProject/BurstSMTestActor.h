#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "BurstSMTestActor.generated.h"

class UStaticMeshComponent;
class UNiagaraComponent;
class UBurstMeshStateSwitcherComponent;
class UMaterialInterface;
class UStaticMesh;

/**
 * BP_Burst_SM_Test 的 C++ 实现。
 * 在构造函数中完成三个 StaticMesh 组件（A/B/C）的网格与玉石材质赋值，
 * 以及 Niagara 组件的粒子系统绑定，无需在蓝图里手动设置。
 */
UCLASS(BlueprintType, Blueprintable, Category="TransformationVFX")
class MCPGAMEPROJECT_API ABurstSMTestActor : public AActor
{
	GENERATED_BODY()

public:
	ABurstSMTestActor();

protected:
	virtual void OnConstruction(const FTransform& Transform) override;

	// ---- 三个状态网格组件 ----
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Burst Test|Meshes")
	TObjectPtr<UStaticMeshComponent> StaticMeshA;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Burst Test|Meshes")
	TObjectPtr<UStaticMeshComponent> StaticMeshB;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Burst Test|Meshes")
	TObjectPtr<UStaticMeshComponent> StaticMeshC;

	// ---- Niagara 粒子组件 ----
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Burst Test|Particles")
	TObjectPtr<UNiagaraComponent> TransformationNiagara;

	// ---- 状态切换逻辑组件 ----
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Burst Test|Logic")
	TObjectPtr<UBurstMeshStateSwitcherComponent> StateSwitcher;

private:
	// 初始化网格资产和材质
	void InitMeshAssets();
};
