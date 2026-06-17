#include "BurstMeshStateSwitcherComponent.h"

#include "Components/BoxComponent.h"
#include "Components/InputComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/WidgetComponent.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "NiagaraComponent.h"
#include "NiagaraFunctionLibrary.h"
#include "NiagaraSystem.h"
#include "TimerManager.h"
#include "UObject/ConstructorHelpers.h"
#include "LeapSubsystem.h"
#include "UltraleapTrackingData.h"

UBurstMeshStateSwitcherComponent::UBurstMeshStateSwitcherComponent()
{
	PrimaryComponentTick.bCanEverTick = true;

	static ConstructorHelpers::FObjectFinder<UNiagaraSystem> InhalationSystem(
		TEXT("/Game/TransformationVFX/Niagara/NS_Inhalation_SM.NS_Inhalation_SM"));
	static ConstructorHelpers::FObjectFinder<UNiagaraSystem> MorphSystem(
		TEXT("/Game/NiagaraMorphEffect/Niagara/P_Morph_5_SM.P_Morph_5_SM"));
	static ConstructorHelpers::FObjectFinder<UMaterialInterface> InhalationParticleMaterial(
		TEXT("/Game/TransformationVFX/Material/CharactorMaterial/MI_Manny_Particle.MI_Manny_Particle"));
	static ConstructorHelpers::FObjectFinder<UMaterialInterface> ChairFadeMaterial(
		TEXT("/Game/TransformationVFX/Material/ObjectMaterial/MI_Chair_UniversalDissolve.MI_Chair_UniversalDissolve"));
	static ConstructorHelpers::FObjectFinder<UMaterialInterface> TableFadeMaterial(
		TEXT("/Game/TransformationVFX/Material/ObjectMaterial/MI_TableRound_UniversalDissolve.MI_TableRound_UniversalDissolve"));

	StateParticleMaterials = {
		InhalationParticleMaterial.Object,
		InhalationParticleMaterial.Object,
		InhalationParticleMaterial.Object
	};
	StateFadeMaterials = {ChairFadeMaterial.Object, TableFadeMaterial.Object, nullptr};
	FallbackModelFadeMaterial = LoadObject<UMaterialInterface>(
		nullptr, TEXT("/Game/TransformationVFX/SM2SM/M_Generic_ModelFade.M_Generic_ModelFade"));
	ParticleMaterial = InhalationParticleMaterial.Object;
	ParticleSystem = InhalationSystem.Object;
	// 网格→网格粒子变形系统（P_Morph_5_SM）。涡流由编辑器工具往该系统加 VortexForce 模块实现，
	// 去掉 spring 用 User.Spring Force=0（见 ApplyMorphParameters）。新属性 BP 不覆盖。
	(void)InhalationSystem;
	MorphParticleSystem = MorphSystem.Object;
}

void UBurstMeshStateSwitcherComponent::OnRegister()
{
	Super::OnRegister();

	if (!IsTemplate())
	{
		CacheOwnerComponents();
		DisableLegacyTriggerAndUI();
		if (TransformationNiagara)
		{
			TransformationNiagara->SetAutoActivate(false);
			TransformationNiagara->DeactivateImmediate();
			TransformationNiagara->SetVisibility(false, true);
		}
	}
}

void UBurstMeshStateSwitcherComponent::BeginPlay()
{
	Super::BeginPlay();

	CacheOwnerComponents();
	DisableLegacyTriggerAndUI();
	PlayerController = UGameplayStatics::GetPlayerController(this, 0);

	// 订阅 Leap 帧广播；用句柄精确移除，避免 Clear() 误删其它监听者。
	if (ULeapSubsystem* LeapSubsystem = ULeapSubsystem::Get())
	{
		LeapFrameDelegateHandle =
			LeapSubsystem->OnLeapFrameMulti.AddUObject(this, &UBurstMeshStateSwitcherComponent::OnLeapTrackingData);
	}

	SetRuntimeStateVisibility(CurrentStateIndex);
	if (TransformationNiagara)
	{
		TransformationNiagara->SetAutoActivate(false);
		TransformationNiagara->DeactivateImmediate();
		TransformationNiagara->SetVisibility(false, true);
	}

	UE_LOG(LogTemp, Display, TEXT("BurstMeshStateSwitcher: initialized on %s; UI and overlap triggers disabled."),
		*GetNameSafe(GetOwner()));
	UE_LOG(LogTemp, Display, TEXT("BurstMeshStateSwitcher: morph system=%s, morph duration=%.2fs, particle linger=%.2fs."),
		*GetNameSafe(MorphParticleSystem), FrontHalfDuration, ParticleFadeOutDuration);
}

void UBurstMeshStateSwitcherComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().ClearTimer(HideSourceTimer);
		World->GetTimerManager().ClearTimer(BeginRevealTimer);
		World->GetTimerManager().ClearTimer(ParticleFadeOutTimer);
	}
	if (LeapFrameDelegateHandle.IsValid())
	{
		if (ULeapSubsystem* LeapSubsystem = ULeapSubsystem::Get())
		{
			LeapSubsystem->OnLeapFrameMulti.Remove(LeapFrameDelegateHandle);
		}
		LeapFrameDelegateHandle.Reset();
	}
	Super::EndPlay(EndPlayReason);
}

void UBurstMeshStateSwitcherComponent::TickComponent(
	float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	if (!bInitialStateMaterialsApplied)
	{
		ApplyInitialStateMaterials();
	}

	// 模型自转独立于输入：放在 PlayerController 判定之前，确保任何时候都能转。
	UpdateModelRotation(DeltaTime);

	if (!PlayerController)
	{
		PlayerController = UGameplayStatics::GetPlayerController(this, 0);
	}
	if (!PlayerController)
	{
		return;
	}

	if (bTransitionActive)
	{
		TransitionElapsed += DeltaTime;
		const float Progress = FMath::Clamp(
			TransitionElapsed / FMath::Max(ActiveTransitionDuration, 0.01f), 0.0f, 1.0f);
		const float EasedProgress = FMath::InterpEaseInOut(
			0.0f, 1.0f, Progress, FMath::Max(TransformationAlphaEaseExponent, 0.1f));
		SetTransformationAlpha(FMath::Lerp(
			InitialTransformationAlpha, FirstHalfEndTransformationAlpha, EasedProgress));
	}

	if (bParticleFadeOutActive && ActiveParticleMaterial)
	{
		ParticleFadeOutElapsed += DeltaTime;
		const float Progress = FMath::Clamp(
			ParticleFadeOutElapsed / FMath::Max(ParticleFadeOutDuration, 0.01f), 0.0f, 1.0f);
		const float FadeAlpha = 1.0f - FMath::InterpEaseIn(
			0.0f, 1.0f, Progress, FMath::Max(ParticleFadeOutEaseExponent, 0.1f));
		ActiveParticleMaterial->SetScalarParameterValue(ParticleFadeOpacityParameter, FadeAlpha);
		TransformationNiagara->SetVariableFloat(TEXT("User.Fade Opacity"), FadeAlpha);
		TransformationNiagara->SetVariableFloat(TEXT("User.FadeOpacity"), FadeAlpha);
		if (Progress >= 1.0f)
		{
			StopAndHideParticles();
		}
	}

	if (bFadeInActive && TargetMeshComponent)
	{
		FadeInElapsed += DeltaTime;
		const float Progress = FMath::Clamp(
			FadeInElapsed / FMath::Max(ModelFadeInDuration, 0.01f), 0.0f, 1.0f);
		const float SmoothedProgress = FMath::SmoothStep(0.0f, 1.0f, Progress);
		for (UMaterialInstanceDynamic* FadeMaterial : ActiveFadeMaterials)
		{
			if (FadeMaterial)
			{
				FadeMaterial->SetScalarParameterValue(
					TEXT("Dissolve Amount"),
					FMath::Lerp(ModelFadeStartDissolve, ModelFadeEndDissolve, SmoothedProgress));
			}
		}
		if (Progress >= 1.0f)
		{
			CompleteTransition();
		}
	}

	if (bSourceFadeOutActive && SourceMeshComponent)
	{
		SourceFadeOutElapsed += DeltaTime;
		const float Progress = FMath::Clamp(
			SourceFadeOutElapsed / FMath::Max(SourceFadeOutDuration, 0.01f), 0.0f, 1.0f);
		const float Smoothed = FMath::SmoothStep(0.0f, 1.0f, Progress);
		// 从 ModelFadeEndDissolve(1.0 完整) 溶解淡出到 ModelFadeStartDissolve(0.0 消散)
		const float DissolveValue = FMath::Lerp(ModelFadeEndDissolve, ModelFadeStartDissolve, Smoothed);
		for (UMaterialInstanceDynamic* FadeMaterial : ActiveSourceFadeMaterials)
		{
			if (FadeMaterial)
			{
				FadeMaterial->SetScalarParameterValue(TEXT("Dissolve Amount"), DissolveValue);
			}
		}
		if (Progress >= 1.0f)
		{
			SourceMeshComponent->SetVisibility(false, true);
			bSourceFadeOutActive = false;
			ActiveSourceFadeMaterials.Reset();
		}
	}

	if (PlayerController->WasInputKeyJustPressed(EKeys::One))
	{
		SwitchToStateOne();
	}
	else if (PlayerController->WasInputKeyJustPressed(EKeys::Two))
	{
		SwitchToStateTwo();
	}
	else if (PlayerController->WasInputKeyJustPressed(EKeys::Three))
	{
		SwitchToStateThree();
	}

	// 1/2/3 键功能保留；额外用 Leap 挥手做正反向循环切换。
	PollLeapSwipeGestures(DeltaTime);
}

void UBurstMeshStateSwitcherComponent::UpdateModelRotation(float DeltaTime)
{
	if (!bEnableModelRotation || FMath::IsNearlyZero(RotationSpeedDegreesPerSecond))
	{
		return;
	}

	// 仅在没有切换过渡进行（即模型已完整显示）时自转。
	if (IsTransitionInProgress())
	{
		return;
	}

	UStaticMeshComponent* CurrentMesh = StateMeshComponents.IsValidIndex(CurrentStateIndex)
		? StateMeshComponents[CurrentStateIndex]
		: nullptr;
	// 隐藏的模型不旋转。
	if (!CurrentMesh || !CurrentMesh->IsVisible())
	{
		return;
	}

	// 绕世界竖直轴（Z）从当前角度增量旋转。
	const float DeltaYaw = RotationSpeedDegreesPerSecond * DeltaTime;
	CurrentMesh->AddWorldRotation(FRotator(0.0f, DeltaYaw, 0.0f));
}

bool UBurstMeshStateSwitcherComponent::IsTransitionInProgress() const
{
	return bTransitionActive || bFadeInActive || bSourceFadeOutActive
		|| bParticleFadeOutActive || PendingStateIndex != INDEX_NONE;
}

void UBurstMeshStateSwitcherComponent::OnLeapTrackingData(const FLeapFrameData& Frame)
{
	// 仅缓存左右手最新数据；判定逻辑在 Tick 中按帧时间走冷却，便于防抖。
	TimeSinceLeapFrame = 0.0f;
	bLeftHandPresent = false;
	bRightHandPresent = false;
	for (const FLeapHandData& Hand : Frame.Hands)
	{
		if (Hand.HandType == LEAP_HAND_LEFT)
		{
			bLeftHandPresent = true;
			LeftPalmVelocity = Hand.Palm.Velocity;
			LeftHandConfidence = Hand.Confidence;
		}
		else if (Hand.HandType == LEAP_HAND_RIGHT)
		{
			bRightHandPresent = true;
			RightPalmVelocity = Hand.Palm.Velocity;
			RightHandConfidence = Hand.Confidence;
		}
	}
}

void UBurstMeshStateSwitcherComponent::PollLeapSwipeGestures(float DeltaTime)
{
	// 冷却计时始终递减，确保即使本帧提前返回，冷却也会正常恢复。
	LeftHandSwipeCooldown = FMath::Max(0.0f, LeftHandSwipeCooldown - DeltaTime);
	RightHandSwipeCooldown = FMath::Max(0.0f, RightHandSwipeCooldown - DeltaTime);

	// 数据新鲜度兜底：若 Leap 一段时间未推送新帧（设备断开/手离开视野），
	// 视手部为不存在，避免用陈旧速度在冷却结束后反复误触发导致闪烁。
	constexpr float LeapStaleTimeout = 0.25f;
	TimeSinceLeapFrame += DeltaTime;
	if (TimeSinceLeapFrame > LeapStaleTimeout)
	{
		bLeftHandPresent = false;
		bRightHandPresent = false;
	}

	if (!bEnableLeapSwipe)
	{
		return;
	}

	// 防闪烁之一：过渡进行中默认忽略新挥手，等模型完整成形后再响应。
	if (!bAllowSwipeDuringTransition && IsTransitionInProgress())
	{
		return;
	}

	const float AxisSign = bInvertSwipeAxis ? -1.0f : 1.0f;

	// 右手向左摆动（-Y）→ 模型 ID 反向更新。
	if (bRightHandPresent && RightHandSwipeCooldown <= 0.0f
		&& RightHandConfidence >= MinHandConfidence && IsLateralSwipe(RightPalmVelocity))
	{
		if (AxisSign * RightPalmVelocity.Y < 0.0f)
		{
			CycleModel(-1);
			// 防闪烁之四：每手独立冷却，单次挥动不会在多帧内重复触发。
			RightHandSwipeCooldown = SwipeCooldownSeconds;
		}
	}

	// 左手向右挥动（+Y）→ 模型 ID 正向更新。
	if (bLeftHandPresent && LeftHandSwipeCooldown <= 0.0f
		&& LeftHandConfidence >= MinHandConfidence && IsLateralSwipe(LeftPalmVelocity))
	{
		if (AxisSign * LeftPalmVelocity.Y > 0.0f)
		{
			CycleModel(1);
			LeftHandSwipeCooldown = SwipeCooldownSeconds;
		}
	}
}

bool UBurstMeshStateSwitcherComponent::IsLateralSwipe(const FVector& Velocity) const
{
	// 防闪烁之二/三：速度阈值过滤微小抖动；要求水平(左右 Y 轴)分量主导，
	// 避免上下/前后移动被误判为挥手。
	const float LateralAbs = FMath::Abs(Velocity.Y);
	if (LateralAbs < SwipeVelocityThreshold)
	{
		return false;
	}
	return LateralAbs > FMath::Abs(Velocity.X) && LateralAbs > FMath::Abs(Velocity.Z);
}

void UBurstMeshStateSwitcherComponent::CycleModel(int32 Direction)
{
	int32 StateCount = StateMeshComponents.Num();
	if (StateCount <= 0)
	{
		CacheOwnerComponents();
		StateCount = StateMeshComponents.Num();
	}
	if (StateCount <= 0 || Direction == 0)
	{
		return;
	}

	// 以有效当前态（过渡中以目标态为准）为基准做环绕循环。
	const int32 EffectiveCurrent = (PendingStateIndex != INDEX_NONE) ? PendingStateIndex : CurrentStateIndex;
	const int32 NextIndex = ((EffectiveCurrent + Direction) % StateCount + StateCount) % StateCount;
	UE_LOG(LogTemp, Display, TEXT("BurstMeshStateSwitcher: leap swipe cycle %s -> state %d."),
		Direction > 0 ? TEXT("forward") : TEXT("reverse"), NextIndex + 1);
	SwitchToState(NextIndex);
}

void UBurstMeshStateSwitcherComponent::ApplyInitialStateMaterials()
{
	if (StateMeshComponents.Num() < 3)
	{
		CacheOwnerComponents();
	}

	for (int32 StateIndex = 0; StateIndex < StateMeshComponents.Num(); ++StateIndex)
	{
		UStaticMeshComponent* MeshComponent = StateMeshComponents[StateIndex];
		UMaterialInterface* StateMaterial = StateFadeMaterials.IsValidIndex(StateIndex)
			? StateFadeMaterials[StateIndex]
			: nullptr;
		if (!MeshComponent || !StateMaterial)
		{
			continue;
		}

		const int32 MaterialCount = FMath::Max(MeshComponent->GetNumMaterials(), 1);
		for (int32 MaterialIndex = 0; MaterialIndex < MaterialCount; ++MaterialIndex)
		{
			MeshComponent->SetMaterial(MaterialIndex, StateMaterial);
		}
	}

	bInitialStateMaterialsApplied = true;
	SetRuntimeStateVisibility(CurrentStateIndex);
}

void UBurstMeshStateSwitcherComponent::CacheOwnerComponents()
{
	AActor* Owner = GetOwner();
	if (!Owner)
	{
		return;
	}

	StateMeshComponents.Reset();
	StateMeshComponents.SetNum(3);
	TArray<UStaticMeshComponent*> MeshComponents;
	Owner->GetComponents(MeshComponents);
	const TCHAR* StateComponentNames[] = {TEXT("StaticMeshA"), TEXT("StaticMeshB"), TEXT("StaticMeshC")};
	for (int32 StateIndex = 0; StateIndex < UE_ARRAY_COUNT(StateComponentNames); ++StateIndex)
	{
		for (UStaticMeshComponent* MeshComponent : MeshComponents)
		{
			if (!MeshComponent)
			{
				continue;
			}

			FString NormalizedName = MeshComponent->GetName();
			NormalizedName.ReplaceInline(TEXT(" "), TEXT(""));
			NormalizedName.ReplaceInline(TEXT("_"), TEXT(""));
			if (NormalizedName.Contains(StateComponentNames[StateIndex]))
			{
				StateMeshComponents[StateIndex] = MeshComponent;
				break;
			}
		}
	}
	SourceMeshComponent = StateMeshComponents.IsValidIndex(CurrentStateIndex)
		? StateMeshComponents[CurrentStateIndex]
		: nullptr;
	TargetMeshComponent = nullptr;

	TransformationNiagara = Owner->FindComponentByClass<UNiagaraComponent>();
	if (TransformationNiagara)
	{
		// 始终使用网格变形系统（P_Morph_5_SM）。MorphParticleSystem 是新属性，BP 实例不会覆盖。
		if (!MorphParticleSystem)
		{
			MorphParticleSystem = LoadObject<UNiagaraSystem>(
				nullptr, TEXT("/Game/NiagaraMorphEffect/Niagara/P_Morph_5_SM.P_Morph_5_SM"));
		}
		if (MorphParticleSystem)
		{
			TransformationNiagara->SetAutoActivate(false);
			TransformationNiagara->SetAsset(MorphParticleSystem);
		}
		NiagaraBaseLocation = TransformationNiagara->GetRelativeLocation();
		NiagaraBaseScale = TransformationNiagara->GetRelativeScale3D();
		NiagaraBaseRotation = TransformationNiagara->GetRelativeRotation();
	}
}

void UBurstMeshStateSwitcherComponent::SetRuntimeStateVisibility(int32 VisibleStateIndex)
{
	for (int32 Index = 0; Index < StateMeshComponents.Num(); ++Index)
	{
		if (UStaticMeshComponent* MeshComponent = StateMeshComponents[Index])
		{
			MeshComponent->SetVisibility(Index == VisibleStateIndex, true);
		}
	}
}

void UBurstMeshStateSwitcherComponent::DisableLegacyTriggerAndUI()
{
	AActor* Owner = GetOwner();
	if (!Owner)
	{
		return;
	}

	TArray<UBoxComponent*> BoxComponents;
	Owner->GetComponents(BoxComponents);
	for (UBoxComponent* BoxComponent : BoxComponents)
	{
		BoxComponent->SetGenerateOverlapEvents(false);
		BoxComponent->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	}

	TArray<UWidgetComponent*> WidgetComponents;
	Owner->GetComponents(WidgetComponents);
	for (UWidgetComponent* WidgetComponent : WidgetComponents)
	{
		WidgetComponent->SetVisibility(false, true);
		WidgetComponent->SetHiddenInGame(true, true);
		WidgetComponent->SetWidget(nullptr);
	}
}

void UBurstMeshStateSwitcherComponent::ApplyParticleSettings()
{
	if (!TransformationNiagara)
	{
		return;
	}

	// P_Morph_5_SM 用 User.Static Mesh0 作为源形状、User.Static Mesh1 作为目标形状。
	if (SourceMeshComponent)
	{
		UNiagaraFunctionLibrary::OverrideSystemUserVariableStaticMeshComponent(
			TransformationNiagara, TEXT("User.Static Mesh0"), SourceMeshComponent);
	}
	if (TargetMeshComponent)
	{
		UNiagaraFunctionLibrary::OverrideSystemUserVariableStaticMeshComponent(
			TransformationNiagara, TEXT("User.Static Mesh1"), TargetMeshComponent);
	}
	TransformationNiagara->SetRelativeLocation(NiagaraBaseLocation + ParticleLocationOffset);
	TransformationNiagara->SetRelativeRotation(NiagaraBaseRotation + ParticleRotationOffset);
	TransformationNiagara->SetRelativeScale3D(NiagaraBaseScale * ParticleNonUniformScale);
	// 去掉 Spring 力（保留 Noise）：让粒子涡流向外消散而非弹回目标。
	TransformationNiagara->SetVariableFloat(TEXT("User.Spring Force"), 0.0f);
	// 粒子颜色 = 目标模型玉石材质：把目标状态的玉石材质设到 User.ParticleMaterial，
	// （需在 Niagara 里把 Sprite Renderer 的 Material 绑定到 User 参数 ParticleMaterial）。
	const int32 TargetStateIdx = (PendingStateIndex != INDEX_NONE) ? PendingStateIndex : CurrentStateIndex;
	if (StateFadeMaterials.IsValidIndex(TargetStateIdx) && StateFadeMaterials[TargetStateIdx])
	{
		TransformationNiagara->SetVariableMaterial(
			TEXT("User.ParticleMaterial"), StateFadeMaterials[TargetStateIdx]);
	}
	ApplyMorphParameters();
}

void UBurstMeshStateSwitcherComponent::ApplyMorphParameters()
{
	// 仅在显式开启时覆盖（保留给 P_Morph 系列系统的可选调参，吸入系统下无副作用）。
	if (!TransformationNiagara || !bOverrideMorphParameters)
	{
		return;
	}

	TransformationNiagara->SetVariableLinearColor(TEXT("User.Emissive Color"), MorphEmissiveColor);
	TransformationNiagara->SetVariableFloat(TEXT("User.Noise Force"), MorphNoiseForce);
	TransformationNiagara->SetVariableFloat(TEXT("User.Spawn Rate"), MorphSpawnRate);
	TransformationNiagara->SetVariableFloat(TEXT("User.Spring Force"), MorphSpringForce);
}

void UBurstMeshStateSwitcherComponent::SetTransformationAlpha(float Alpha)
{
	if (!TransformationNiagara)
	{
		return;
	}

	TransformationNiagara->SetVariableFloat(TEXT("User.Transformation Alpha"), Alpha);
	TransformationNiagara->SetVariableFloat(TEXT("User.TransformationAlpha"), Alpha);
	TransformationNiagara->SetVariableFloat(TEXT("User.Morph Alpha"), Alpha);
}

UMaterialInterface* UBurstMeshStateSwitcherComponent::ResolveParticleMaterial() const
{
	if (bUseStateParticleMaterials && StateParticleMaterials.IsValidIndex(CurrentStateIndex))
	{
		return StateParticleMaterials[CurrentStateIndex];
	}
	return ParticleMaterial;
}

void UBurstMeshStateSwitcherComponent::SwitchToStateOne()
{
	SwitchToState(0);
}

void UBurstMeshStateSwitcherComponent::SwitchToStateTwo()
{
	SwitchToState(1);
}

void UBurstMeshStateSwitcherComponent::SwitchToStateThree()
{
	SwitchToState(2);
}

void UBurstMeshStateSwitcherComponent::SwitchToState(int32 StateIndex)
{
	// 有效当前态：过渡中以正在切往的目标(PendingStateIndex)为准，否则为已显示态(CurrentStateIndex)。
	// 防止过渡中再按同一个目标键重复触发。
	const int32 EffectiveCurrent = (PendingStateIndex != INDEX_NONE) ? PendingStateIndex : CurrentStateIndex;
	if (StateIndex == EffectiveCurrent)
	{
		return;
	}
	if (!StateMeshComponents.IsValidIndex(StateIndex) || !StateMeshComponents[StateIndex]
		|| !SourceMeshComponent || !TransformationNiagara)
	{
		CacheOwnerComponents();
	}
	if (!StateMeshComponents.IsValidIndex(StateIndex) || !StateMeshComponents[StateIndex]
		|| !SourceMeshComponent || !TransformationNiagara)
	{
		UE_LOG(LogTemp, Warning,
			TEXT("BurstMeshStateSwitcher: Static Mesh A/B/C components were not found on BP_Burst_SM."));
		return;
	}

	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().ClearTimer(HideSourceTimer);
		World->GetTimerManager().ClearTimer(BeginRevealTimer);
		World->GetTimerManager().ClearTimer(ParticleFadeOutTimer);
	}
	StopAndHideParticles();
	if (bFadeInActive)
	{
		CompleteTransition();
	}
	if (bSourceFadeOutActive)
	{
		if (SourceMeshComponent)
		{
			SourceMeshComponent->SetVisibility(false, true);
		}
		bSourceFadeOutActive = false;
		ActiveSourceFadeMaterials.Reset();
	}

	// 以真正的当前显示态为源；并强制只显示它（隐藏任何上一次过渡残留的网格）。
	SourceMeshComponent = StateMeshComponents.IsValidIndex(CurrentStateIndex)
		? StateMeshComponents[CurrentStateIndex]
		: SourceMeshComponent;
	SetRuntimeStateVisibility(CurrentStateIndex);

	PendingStateIndex = StateIndex;
	TargetMeshComponent = StateMeshComponents[PendingStateIndex];
	UE_LOG(LogTemp, Display, TEXT("BurstMeshStateSwitcher: switching from state %d to state %d."),
		CurrentStateIndex + 1, PendingStateIndex + 1);
	TargetMeshComponent->EmptyOverrideMaterials();

	if (MorphParticleSystem && TransformationNiagara->GetAsset() != MorphParticleSystem)
	{
		TransformationNiagara->SetAsset(MorphParticleSystem);
	}
	// 先设源/目标网格再重置系统，重置后再设一次，确保数据接口在重新初始化后拿到正确的网格。
	ApplyParticleSettings();
	TransformationNiagara->ReinitializeSystem();
	ApplyParticleSettings();
	TransformationNiagara->SetVisibility(true, true);
	TransformationNiagara->Activate(true);

	if (UWorld* World = GetWorld())
	{
		const float EffectiveDuration = FMath::Max(FrontHalfDuration, 0.1f);
		// 变形系统自带粒子运动，不需要逐帧驱动 Transformation Alpha。
		bTransitionActive = false;
		World->GetTimerManager().SetTimer(
			HideSourceTimer, this, &UBurstMeshStateSwitcherComponent::BeginSourceFadeOut, SourceHideDelay, false);
		World->GetTimerManager().SetTimer(
			BeginRevealTimer, this, &UBurstMeshStateSwitcherComponent::BeginModelReveal, EffectiveDuration, false);
	}
}

void UBurstMeshStateSwitcherComponent::HideSourceMesh()
{
	if (SourceMeshComponent)
	{
		SourceMeshComponent->SetVisibility(false, true);
	}
}

void UBurstMeshStateSwitcherComponent::BeginSourceFadeOut()
{
	if (!SourceMeshComponent)
	{
		return;
	}

	// 用旧模型当前状态的玉石溶解材质，做一个 Dissolve 1.0(完整)->0.0(消散) 的淡出。
	ActiveSourceFadeMaterials.Reset();
	UMaterialInterface* FadeMaterial =
		StateFadeMaterials.IsValidIndex(CurrentStateIndex) && StateFadeMaterials[CurrentStateIndex]
			? StateFadeMaterials[CurrentStateIndex]
			: FallbackModelFadeMaterial;
	if (FadeMaterial)
	{
		const int32 MaterialCount = FMath::Max(SourceMeshComponent->GetNumMaterials(), 1);
		for (int32 MaterialIndex = 0; MaterialIndex < MaterialCount; ++MaterialIndex)
		{
			if (UMaterialInstanceDynamic* FadeMID = SourceMeshComponent->CreateDynamicMaterialInstance(
				MaterialIndex, FadeMaterial))
			{
				FadeMID->SetScalarParameterValue(TEXT("Dissolve Amount"), ModelFadeEndDissolve);
				ActiveSourceFadeMaterials.Add(FadeMID);
			}
		}
	}

	if (ActiveSourceFadeMaterials.IsEmpty())
	{
		// 没有可用溶解材质就回退到直接隐藏，避免旧模型一直留在画面上。
		SourceMeshComponent->SetVisibility(false, true);
		return;
	}

	SourceFadeOutElapsed = 0.0f;
	bSourceFadeOutActive = true;
	UE_LOG(LogTemp, Display,
		TEXT("BurstMeshStateSwitcher: source model dissolving out over %.2fs."), SourceFadeOutDuration);
}

void UBurstMeshStateSwitcherComponent::BeginModelReveal()
{
	if (!StateMeshComponents.IsValidIndex(PendingStateIndex) || !TargetMeshComponent)
	{
		return;
	}

	// 注意：CurrentStateIndex 不在这里更新，必须等目标真正显示后（CompleteTransition）才切换，
	// 否则快速切换被打断时会残留上一个目标网格，导致两个模型同时出现。
	bTransitionActive = false;

	TargetMeshComponent->EmptyOverrideMaterials();
	// 过渡期间所有状态网格都隐藏（粒子代表过渡），目标等粒子消散后再揭示。
	SetRuntimeStateVisibility(INDEX_NONE);

	// 停止粒子继续生成，让现有粒子按自身生命周期自然消散。
	if (TransformationNiagara)
	{
		TransformationNiagara->Deactivate();
	}

	// 粒子完全消散后（ParticleFadeOutDuration）才显示新模型完整材质。
	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().SetTimer(
			ParticleFadeOutTimer,
			this,
			&UBurstMeshStateSwitcherComponent::FinishParticlesAndRevealTarget,
			FMath::Max(ParticleFadeOutDuration, 0.01f),
			false);
	}
}

void UBurstMeshStateSwitcherComponent::FinishParticlesAndRevealTarget()
{
	// 粒子动画结束：先彻底隐藏/清理粒子，再揭示新模型完整材质。
	StopAndHideParticles();
	BeginTargetModelFadeIn();
}

void UBurstMeshStateSwitcherComponent::BeginTargetModelFadeIn()
{
	if (!TargetMeshComponent)
	{
		return;
	}

	UE_LOG(LogTemp, Display, TEXT("BurstMeshStateSwitcher: particle fade complete; beginning target model fade in."));
	ActiveFadeMaterials.Reset();
	// 目标状态用 PendingStateIndex（CurrentStateIndex 此时还是源，未切换）。
	UMaterialInterface* ModelFadeMaterial =
		StateFadeMaterials.IsValidIndex(PendingStateIndex) && StateFadeMaterials[PendingStateIndex]
			? StateFadeMaterials[PendingStateIndex]
			: FallbackModelFadeMaterial;
	if (ModelFadeMaterial)
	{
		const int32 MaterialCount = FMath::Max(TargetMeshComponent->GetNumMaterials(), 1);
		for (int32 MaterialIndex = 0; MaterialIndex < MaterialCount; ++MaterialIndex)
		{
			if (UMaterialInstanceDynamic* FadeMaterial = TargetMeshComponent->CreateDynamicMaterialInstance(
				MaterialIndex, ModelFadeMaterial))
			{
				FadeMaterial->SetScalarParameterValue(TEXT("Dissolve Amount"), ModelFadeStartDissolve);
				ActiveFadeMaterials.Add(FadeMaterial);
			}
		}
	}
	if (ActiveFadeMaterials.IsEmpty())
	{
		UE_LOG(LogTemp, Warning,
			TEXT("BurstMeshStateSwitcher: state %d has no model fade material; target remains hidden."),
			PendingStateIndex + 1);
		return;
	}

	FadeInElapsed = 0.0f;
	bFadeInActive = true;
	bFadeRevealPending = false;
	// 只显示目标网格，强制隐藏其它所有状态网格，确保任何时刻只有一个模型可见。
	SetRuntimeStateVisibility(PendingStateIndex);
	UE_LOG(LogTemp, Display,
		TEXT("BurstMeshStateSwitcher: target revealed with dissolve %.2f; animating to %.2f over %.2fs."),
		ModelFadeStartDissolve, ModelFadeEndDissolve, ModelFadeInDuration);
}

void UBurstMeshStateSwitcherComponent::BeginParticleFadeOut()
{
	ParticleFadeOutElapsed = 0.0f;
	bParticleFadeOutActive = true;
	UE_LOG(LogTemp, Display, TEXT("BurstMeshStateSwitcher: beginning %.2fs particle fade out before target reveal."),
		ParticleFadeOutDuration);
	if (ActiveParticleMaterial)
	{
		ActiveParticleMaterial->SetScalarParameterValue(ParticleFadeOpacityParameter, 1.0f);
	}
}

void UBurstMeshStateSwitcherComponent::StopAndHideParticles()
{
	if (TransformationNiagara)
	{
		// 用 Deactivate（停止生成、保留已存在粒子自然消散）而不是 DeactivateImmediate（瞬间清空），
		// 保持柔和淡出的观感。
		TransformationNiagara->Deactivate();
		TransformationNiagara->SetVisibility(false, true);
	}
	bParticleFadeOutActive = false;
	ParticleFadeOutElapsed = 0.0f;
	ActiveParticleMaterial = nullptr;
}

void UBurstMeshStateSwitcherComponent::CompleteTransition()
{
	if (TargetMeshComponent)
	{
		for (UMaterialInstanceDynamic* FadeMaterial : ActiveFadeMaterials)
		{
			if (FadeMaterial)
			{
				FadeMaterial->SetScalarParameterValue(TEXT("Dissolve Amount"), ModelFadeEndDissolve);
			}
		}
		// 过渡真正完成：现在才把当前状态切到目标，并强制只显示它（隐藏其余），杜绝两个同时出现。
		if (PendingStateIndex != INDEX_NONE)
		{
			CurrentStateIndex = PendingStateIndex;
		}
		SourceMeshComponent = TargetMeshComponent;
		TargetMeshComponent = nullptr;
		SetRuntimeStateVisibility(CurrentStateIndex);
	}
	PendingStateIndex = INDEX_NONE;
	if (!bUseNaturalParticleFadeOut)
	{
		StopAndHideParticles();
	}
	ActiveFadeMaterials.Reset();
	bFadeInActive = false;
	bFadeRevealPending = false;

	UE_LOG(LogTemp, Display, TEXT("BurstMeshStateSwitcher: state %d transition complete."), CurrentStateIndex + 1);
}
