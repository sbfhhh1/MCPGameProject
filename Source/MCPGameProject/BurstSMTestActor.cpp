#include "BurstSMTestActor.h"

#include "BurstMeshStateSwitcherComponent.h"
#include "Components/StaticMeshComponent.h"
#include "NiagaraComponent.h"
#include "NiagaraSystem.h"
#include "UObject/ConstructorHelpers.h"

ABurstSMTestActor::ABurstSMTestActor()
{
	PrimaryActorTick.bCanEverTick = false;

	// ---- 根组件 ----
	USceneComponent* DefaultRoot = CreateDefaultSubobject<USceneComponent>(TEXT("DefaultSceneRoot"));
	SetRootComponent(DefaultRoot);

	// ---- Static Mesh A ----
	StaticMeshA = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("StaticMeshA"));
	StaticMeshA->SetupAttachment(RootComponent);

	// ---- Static Mesh B ----
	StaticMeshB = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("StaticMeshB"));
	StaticMeshB->SetupAttachment(RootComponent);

	// ---- Static Mesh C ----
	StaticMeshC = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("StaticMeshC"));
	StaticMeshC->SetupAttachment(RootComponent);

	// ---- Niagara 组件 ----
	TransformationNiagara = CreateDefaultSubobject<UNiagaraComponent>(TEXT("TransformationNiagara"));
	TransformationNiagara->SetupAttachment(RootComponent);
	TransformationNiagara->SetAutoActivate(false);
	TransformationNiagara->SetVisibility(false, true);

	// ---- 状态切换逻辑组件 ----
	StateSwitcher = CreateDefaultSubobject<UBurstMeshStateSwitcherComponent>(TEXT("BurstMeshStateSwitcher"));

	// ---- 在构造函数中加载资产并赋值 ----

	// 网格资产
	static ConstructorHelpers::FObjectFinder<UStaticMesh> MeshA(
		TEXT("/Game/TransformationVFX/SM2SM/jude/20260613133607_ec021d65.20260613133607_ec021d65"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> MeshB(
		TEXT("/Game/TransformationVFX/SM2SM/jude/20260613123723_f8ed59ab.20260613123723_f8ed59ab"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> MeshC(
		TEXT("/Game/TransformationVFX/SM2SM/jude/20260613130638_a1276204.20260613130638_a1276204"));

	if (MeshA.Succeeded()) { StaticMeshA->SetStaticMesh(MeshA.Object); }
	if (MeshB.Succeeded()) { StaticMeshB->SetStaticMesh(MeshB.Object); }
	if (MeshC.Succeeded()) { StaticMeshC->SetStaticMesh(MeshC.Object); }

	// 玉石材质
	static ConstructorHelpers::FObjectFinder<UMaterialInterface> MatTYS(
		TEXT("/Game/TransformationVFX/SM2SM/jude/BurstJade/MI_TYS_Jade_SSS.MI_TYS_Jade_SSS"));
	static ConstructorHelpers::FObjectFinder<UMaterialInterface> MatYF(
		TEXT("/Game/TransformationVFX/SM2SM/jude/BurstJade/MI_YF_Jade_SSS.MI_YF_Jade_SSS"));
	static ConstructorHelpers::FObjectFinder<UMaterialInterface> MatYZL(
		TEXT("/Game/TransformationVFX/SM2SM/jude/BurstJade/MI_YZL_Jade_SSS.MI_YZL_Jade_SSS"));

	if (MatTYS.Succeeded()) { StaticMeshA->SetMaterial(0, MatTYS.Object); }
	if (MatYF.Succeeded())  { StaticMeshB->SetMaterial(0, MatYF.Object); }
	if (MatYZL.Succeeded()) { StaticMeshC->SetMaterial(0, MatYZL.Object); }

	// Niagara 粒子系统
	static ConstructorHelpers::FObjectFinder<UNiagaraSystem> VortexSystem(
		TEXT("/Game/TransformationVFX/SM2SM/jude/P_Morph_5_SM_Vortex.P_Morph_5_SM_Vortex"));
	if (VortexSystem.Succeeded())
	{
		TransformationNiagara->SetAsset(VortexSystem.Object);
	}

	// 默认只显示状态 0（Mesh A）
	StaticMeshA->SetVisibility(true, true);
	StaticMeshB->SetVisibility(false, true);
	StaticMeshC->SetVisibility(false, true);
}

void ABurstSMTestActor::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);
}
