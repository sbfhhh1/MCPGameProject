#include "JadeShatterSwitcherComponent.h"

#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/AssetManager.h"
#include "Engine/ObjectLibrary.h"
#include "GameFramework/Actor.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInterface.h"
#include "Math/RandomStream.h"

UJadeShatterSwitcherComponent::UJadeShatterSwitcherComponent()
{
	PrimaryComponentTick.bCanEverTick = true;

	ShardFolders = {
		TEXT("/Game/TransformationVFX/SM2SM/jude/Shards/jadeA"),
		TEXT("/Game/TransformationVFX/SM2SM/jude/Shards/jadeB"),
		TEXT("/Game/TransformationVFX/SM2SM/jude/Shards/jadeC")
	};
	JadeMaterial = LoadObject<UMaterialInterface>(
		nullptr, TEXT("/Game/TransformationVFX/SM2SM/jude/M_YZL_ProceduralJade_SSS.M_YZL_ProceduralJade_SSS"));

	// 复现用户设定的玉石显示朝向 (Roll, Pitch, Yaw)：A(90,0,0) B(90,0,180) C(90,0,0)
	StateRotations = {
		FRotator(0.0f, 0.0f, 90.0f),
		FRotator(0.0f, 180.0f, 90.0f),
		FRotator(0.0f, 0.0f, 90.0f)
	};
}

void UJadeShatterSwitcherComponent::BeginPlay()
{
	Super::BeginPlay();
	CurrentState = FMath::Clamp(InitialState, 0, FMath::Max(ShardFolders.Num() - 1, 0));
	PlayerController = UGameplayStatics::GetPlayerController(this, 0);
	BuildShardSets();
}

void UJadeShatterSwitcherComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	Super::EndPlay(EndPlayReason);
}

void UJadeShatterSwitcherComponent::BuildShardSets()
{
	if (bShardsBuilt)
	{
		return;
	}
	AActor* Owner = GetOwner();
	USceneComponent* Root = Owner ? Owner->GetRootComponent() : nullptr;
	if (!Owner || !Root)
	{
		return;
	}

	StateSets.Reset();
	StateSets.SetNum(ShardFolders.Num());

	for (int32 State = 0; State < ShardFolders.Num(); ++State)
	{
		const FString& Folder = ShardFolders[State];

		// 每状态朝向 pivot：碎块挂在它下面，复现原版玉石的 roll90+yaw 朝向与位置
		USceneComponent* Pivot = NewObject<USceneComponent>(Owner);
		Pivot->SetupAttachment(Root);
		Pivot->RegisterComponent();
		Pivot->SetRelativeRotation(StateRotations.IsValidIndex(State) ? StateRotations[State] : FRotator::ZeroRotator);
		StateSets[State].Pivot = Pivot;

		UObjectLibrary* Lib = UObjectLibrary::CreateLibrary(UStaticMesh::StaticClass(), false, false);
		Lib->AddToRoot();
		Lib->LoadAssetDataFromPath(Folder);
		Lib->LoadAssetsFromAssetData();
		TArray<FAssetData> AssetDatas;
		Lib->GetAssetDataList(AssetDatas);

		// Pass 1：收集碎块网格 + 合并本地包围盒（用于归一化，消除 FBX 往返的任意缩放/偏移）
		TArray<UStaticMesh*> Meshes;
		FBox Combined(ForceInit);
		for (const FAssetData& AD : AssetDatas)
		{
			UStaticMesh* Mesh = Cast<UStaticMesh>(AD.GetAsset());
			if (Mesh)
			{
				Meshes.Add(Mesh);
				Combined += Mesh->GetBoundingBox();
			}
		}
		const FVector Cc = Combined.GetCenter();
		const FVector CombinedSize = Combined.GetSize();
		const float MaxDim = FMath::Max3(CombinedSize.X, CombinedSize.Y, CombinedSize.Z);
		const float StateScale = (MaxDim > KINDA_SMALL_NUMBER) ? (TargetHeight / MaxDim) : 1.0f;

		// Pass 2：归一化缩放 + 居中创建碎块组件
		int32 Index = 0;
		for (UStaticMesh* Mesh : Meshes)
		{
			UStaticMeshComponent* SMC = NewObject<UStaticMeshComponent>(Owner);
			SMC->SetupAttachment(Pivot);
			SMC->RegisterComponent();
			SMC->SetStaticMesh(Mesh);
			SMC->SetRelativeScale3D(FVector(StateScale));
			SMC->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			SMC->SetCastShadow(true);
			if (JadeMaterial)
			{
				const int32 MatCount = FMath::Max(SMC->GetNumMaterials(), 1);
				for (int32 m = 0; m < MatCount; ++m)
				{
					SMC->SetMaterial(m, JadeMaterial);
				}
			}
			SMC->SetVisibility(State == CurrentState, true);

			FJadeShardRuntime Shard;
			Shard.Comp = SMC;
			const FVector MeshCenter = Mesh->GetBoundingBox().GetCenter();
			Shard.GeomOffset = MeshCenter * StateScale;
			Shard.RestCentroid = (MeshCenter - Cc) * StateScale;

			FRandomStream Stream(GetTypeHash(Mesh->GetFName()) ^ (State * 7919 + Index * 31));
			Shard.TurbulenceDir = FVector(
				Stream.FRandRange(-1.f, 1.f), Stream.FRandRange(-1.f, 1.f), Stream.FRandRange(-1.f, 1.f)).GetSafeNormal();

			SMC->SetRelativeLocationAndRotation(Shard.RestCentroid - Shard.GeomOffset, FRotator::ZeroRotator);

			StateSets[State].Shards.Add(Shard);
			++Index;
		}

		Lib->RemoveFromRoot();
		UE_LOG(LogTemp, Display, TEXT("JadeShatter: state %d loaded %d shards from %s"),
			State, StateSets[State].Shards.Num(), *Folder);
	}

	// 初始：当前状态拼合可见，其余隐藏
	for (int32 State = 0; State < StateSets.Num(); ++State)
	{
		UpdateStatePose(State, 0.0f);
		SetStateVisible(State, State == CurrentState);
	}
	bShardsBuilt = true;
}

void UJadeShatterSwitcherComponent::SetStateVisible(int32 StateIndex, bool bVisible)
{
	if (!StateSets.IsValidIndex(StateIndex))
	{
		return;
	}
	for (const FJadeShardRuntime& Shard : StateSets[StateIndex].Shards)
	{
		if (Shard.Comp)
		{
			Shard.Comp->SetVisibility(bVisible, true);
		}
	}
}

void UJadeShatterSwitcherComponent::ApplyShardPose(
	const FJadeShardRuntime& Shard, float Disperse, FVector& OutRelLoc, FRotator& OutRelRot) const
{
	FVector Axis = VortexAxis.GetSafeNormal();
	if (Axis.IsNearlyZero())
	{
		Axis = FVector(0, 0, 1);
	}
	const FVector C = Shard.RestCentroid;

	const float H0 = FVector::DotProduct(C, Axis);
	FVector RadialVec = C - H0 * Axis;
	float R0 = RadialVec.Size();
	FVector RadialDir = (R0 > 1.0f) ? (RadialVec / R0) : FVector::CrossProduct(Axis, FVector(1, 0, 0)).GetSafeNormal();
	if (RadialDir.IsNearlyZero())
	{
		RadialDir = FVector(1, 0, 0);
	}
	const FVector TangentDir = FVector::CrossProduct(Axis, RadialDir).GetSafeNormal();

	const float Theta = Disperse * SwirlTurns * 2.0f * PI;
	const float R = R0 + Disperse * OutwardDistance;
	const float H = H0 + Disperse * LiftHeight;

	const FVector NewRadial = (RadialDir * FMath::Cos(Theta) + TangentDir * FMath::Sin(Theta)) * R;
	const FVector NewCentroid = NewRadial + Axis * H + Shard.TurbulenceDir * (Disperse * Turbulence);

	// SMC 相对位置 = 涡流目标质心 - 几何偏移（几何偏移 = stateScale×mesh本地质心）
	OutRelLoc = NewCentroid - Shard.GeomOffset;
	OutRelRot = FRotator::ZeroRotator;
}

void UJadeShatterSwitcherComponent::UpdateStatePose(int32 StateIndex, float Disperse)
{
	if (!StateSets.IsValidIndex(StateIndex))
	{
		return;
	}
	for (const FJadeShardRuntime& Shard : StateSets[StateIndex].Shards)
	{
		if (!Shard.Comp)
		{
			continue;
		}
		FVector RelLoc; FRotator RelRot;
		ApplyShardPose(Shard, Disperse, RelLoc, RelRot);
		Shard.Comp->SetRelativeLocationAndRotation(RelLoc, RelRot);
	}
}

void UJadeShatterSwitcherComponent::SwitchToState(int32 StateIndex)
{
	if (!bShardsBuilt || StateIndex == CurrentState || !StateSets.IsValidIndex(StateIndex))
	{
		return;
	}
	// 打断进行中的过渡：把当前/待定状态收尾到稳定态
	if (bAssembling && StateSets.IsValidIndex(PendingState))
	{
		UpdateStatePose(PendingState, 0.0f);
		SetStateVisible(PendingState, true);
		CurrentState = PendingState;
	}
	if (bDispersing)
	{
		SetStateVisible(CurrentState, false);
		bDispersing = false;
	}

	PendingState = StateIndex;
	bDispersing = true;
	DisperseElapsed = 0.0f;
	bAssembling = false;
	AssembleElapsed = 0.0f;
	SetStateVisible(CurrentState, true);
	UE_LOG(LogTemp, Display, TEXT("JadeShatter: switch state %d -> %d (shatter+vortex)"), CurrentState + 1, PendingState + 1);
}

void UJadeShatterSwitcherComponent::TickComponent(
	float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	if (!bShardsBuilt)
	{
		return;
	}
	if (!PlayerController)
	{
		PlayerController = UGameplayStatics::GetPlayerController(this, 0);
	}

	// 旧玉石飞散
	if (bDispersing)
	{
		DisperseElapsed += DeltaTime;
		const float P = FMath::Clamp(DisperseElapsed / FMath::Max(DisperseDuration, 0.01f), 0.0f, 1.0f);
		const float Eased = FMath::Pow(P, FMath::Max(EaseExponent, 0.1f));
		UpdateStatePose(CurrentState, Eased);

		// 重叠：提前启动新玉石聚拢
		if (!bAssembling && DisperseElapsed >= FMath::Max(DisperseDuration - OverlapDuration, 0.0f))
		{
			bAssembling = true;
			AssembleElapsed = 0.0f;
			UpdateStatePose(PendingState, 1.0f);
			SetStateVisible(PendingState, true);
		}
		if (P >= 1.0f)
		{
			SetStateVisible(CurrentState, false);
			bDispersing = false;
		}
	}

	// 新玉石从飞散态聚拢重组
	if (bAssembling)
	{
		AssembleElapsed += DeltaTime;
		const float A = FMath::Clamp(AssembleElapsed / FMath::Max(AssembleDuration, 0.01f), 0.0f, 1.0f);
		// 1->0 的飞散度，用 ease-out（先快后慢，归位更稳）
		const float Disperse = 1.0f - FMath::Pow(A, 1.0f / FMath::Max(EaseExponent, 0.1f));
		UpdateStatePose(PendingState, Disperse);
		if (A >= 1.0f)
		{
			UpdateStatePose(PendingState, 0.0f);
			CurrentState = PendingState;
			PendingState = INDEX_NONE;
			bAssembling = false;
			UE_LOG(LogTemp, Display, TEXT("JadeShatter: reassembled into state %d"), CurrentState + 1);
		}
	}

	if (PlayerController)
	{
		if (PlayerController->WasInputKeyJustPressed(EKeys::One))
		{
			SwitchToState(0);
		}
		else if (PlayerController->WasInputKeyJustPressed(EKeys::Two))
		{
			SwitchToState(1);
		}
		else if (PlayerController->WasInputKeyJustPressed(EKeys::Three))
		{
			SwitchToState(2);
		}
	}
}
