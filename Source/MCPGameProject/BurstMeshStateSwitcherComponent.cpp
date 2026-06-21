#include "BurstMeshStateSwitcherComponent.h"

#include "Components/BoxComponent.h"
#include "Components/InputComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
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

namespace
{
bool IsInitialDisplayMaterialUsable(UMaterialInterface* Material)
{
	if (!Material || Material->IsA<UMaterialInstanceDynamic>())
	{
		return false;
	}

	return true;
}

UMaterialInterface* LoadFallbackInitialDisplayMaterial(int32 StateIndex)
{
	const TCHAR* MaterialPaths[] = {
		TEXT("/Game/TransformationVFX/SM2SM/jude/BurstJade/MI_TYS_Jade_SSS.MI_TYS_Jade_SSS"),
		TEXT("/Game/TransformationVFX/SM2SM/jude/BurstJade/MI_YF_Jade_SSS.MI_YF_Jade_SSS"),
		TEXT("/Game/TransformationVFX/SM2SM/jude/BurstJade/MI_YZL_Jade_SSS.MI_YZL_Jade_SSS")
	};

	if (StateIndex < 0 || StateIndex >= UE_ARRAY_COUNT(MaterialPaths))
	{
		return nullptr;
	}

	return LoadObject<UMaterialInterface>(nullptr, MaterialPaths[StateIndex]);
}

UMaterialInterface* ResolveInitialDisplayMaterial(
	UStaticMeshComponent* MeshComponent, int32 MaterialIndex, int32 StateIndex)
{
	if (!MeshComponent)
	{
		return LoadFallbackInitialDisplayMaterial(StateIndex);
	}

	if (const UStaticMeshComponent* TemplateComponent =
		Cast<UStaticMeshComponent>(MeshComponent->GetArchetype()))
	{
		if (UMaterialInterface* TemplateMaterial = TemplateComponent->GetMaterial(MaterialIndex);
			IsInitialDisplayMaterialUsable(TemplateMaterial))
		{
			return TemplateMaterial;
		}
	}

	if (const UStaticMesh* StaticMesh = MeshComponent->GetStaticMesh())
	{
		if (UMaterialInterface* MeshMaterial = StaticMesh->GetMaterial(MaterialIndex);
			IsInitialDisplayMaterialUsable(MeshMaterial))
		{
			return MeshMaterial;
		}
	}

	if (UMaterialInterface* CurrentMaterial = MeshComponent->GetMaterial(MaterialIndex);
		IsInitialDisplayMaterialUsable(CurrentMaterial))
	{
		return CurrentMaterial;
	}

	return LoadFallbackInitialDisplayMaterial(StateIndex);
}
} // namespace

UBurstMeshStateSwitcherComponent::UBurstMeshStateSwitcherComponent()
{
	PrimaryComponentTick.bCanEverTick = true;

	static ConstructorHelpers::FObjectFinder<UNiagaraSystem> InhalationSystem(
		TEXT("/Game/TransformationVFX/Niagara/NS_Inhalation_SM.NS_Inhalation_SM"));
	static ConstructorHelpers::FObjectFinder<UNiagaraSystem> MorphSystem(
		TEXT("/Game/NiagaraMorphEffect/Niagara/P_Morph_5_SM.P_Morph_5_SM"));
	static ConstructorHelpers::FObjectFinder<UMaterialInterface> InhalationParticleMaterial(
		TEXT("/Game/TransformationVFX/Material/CharactorMaterial/MI_Manny_Particle.MI_Manny_Particle"));

	StateParticleMaterials = {
		InhalationParticleMaterial.Object,
		InhalationParticleMaterial.Object,
		InhalationParticleMaterial.Object
	};
	ParticleMaterial = InhalationParticleMaterial.Object;
	ParticleSystem = InhalationSystem.Object;
	// 缃戞牸鈫掔綉鏍肩矑瀛愬彉褰㈢郴缁燂紙P_Morph_5_SM锛夈€傛丁娴佺敱缂栬緫鍣ㄥ伐鍏峰線璇ョ郴缁熷姞 VortexForce 妯″潡瀹炵幇锛?
	// 鍘绘帀 spring 鐢?User.Spring Force=0锛堣 ApplyMorphParameters锛夈€傛柊灞炴€?BP 涓嶈鐩栥€?
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

	// 璁㈤槄 Leap 甯у箍鎾紱鐢ㄥ彞鏌勭簿纭Щ闄わ紝閬垮厤 Clear() 璇垹鍏跺畠鐩戝惉鑰呫€?
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

	// 妯″瀷鑷浆鐙珛浜庤緭鍏ワ細鏀惧湪 PlayerController 鍒ゅ畾涔嬪墠锛岀‘淇濅换浣曟椂鍊欓兘鑳借浆銆?
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

	// 1/2/3 閿姛鑳戒繚鐣欙紱棰濆鐢?Leap 鎸ユ墜鍋氭鍙嶅悜寰幆鍒囨崲銆?
	PollLeapSwipeGestures(DeltaTime);
}

void UBurstMeshStateSwitcherComponent::UpdateModelRotation(float DeltaTime)
{
	if (!bEnableModelRotation || FMath::IsNearlyZero(RotationSpeedDegreesPerSecond))
	{
		return;
	}

	// 浠呭湪娌℃湁鍒囨崲杩囨浮杩涜锛堝嵆妯″瀷宸插畬鏁存樉绀猴級鏃惰嚜杞€?
	if (IsTransitionInProgress())
	{
		return;
	}

	UStaticMeshComponent* CurrentMesh = StateMeshComponents.IsValidIndex(CurrentStateIndex)
		? StateMeshComponents[CurrentStateIndex]
		: nullptr;
	// 闅愯棌鐨勬ā鍨嬩笉鏃嬭浆銆?
	if (!CurrentMesh || !CurrentMesh->IsVisible())
	{
		return;
	}

	// 缁曚笘鐣岀珫鐩磋酱锛圸锛変粠褰撳墠瑙掑害澧為噺鏃嬭浆銆?
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
	// 浠呯紦瀛樺乏鍙虫墜鏈€鏂版暟鎹紱鍒ゅ畾閫昏緫鍦?Tick 涓寜甯ф椂闂磋蛋鍐峰嵈锛屼究浜庨槻鎶栥€?
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
	// 鍐峰嵈璁℃椂濮嬬粓閫掑噺锛岀‘淇濆嵆浣挎湰甯ф彁鍓嶈繑鍥烇紝鍐峰嵈涔熶細姝ｅ父鎭㈠銆?
	LeftHandSwipeCooldown = FMath::Max(0.0f, LeftHandSwipeCooldown - DeltaTime);
	RightHandSwipeCooldown = FMath::Max(0.0f, RightHandSwipeCooldown - DeltaTime);

	// 鏁版嵁鏂伴矞搴﹀厹搴曪細鑻?Leap 涓€娈垫椂闂存湭鎺ㄩ€佹柊甯э紙璁惧鏂紑/鎵嬬寮€瑙嗛噹锛夛紝
	// 瑙嗘墜閮ㄤ负涓嶅瓨鍦紝閬垮厤鐢ㄩ檲鏃ч€熷害鍦ㄥ喎鍗寸粨鏉熷悗鍙嶅璇Е鍙戝鑷撮棯鐑併€?
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

	// 闃查棯鐑佷箣涓€锛氳繃娓¤繘琛屼腑榛樿蹇界暐鏂版尌鎵嬶紝绛夋ā鍨嬪畬鏁存垚褰㈠悗鍐嶅搷搴斻€?
	if (!bAllowSwipeDuringTransition && IsTransitionInProgress())
	{
		return;
	}

	const float AxisSign = bInvertSwipeAxis ? -1.0f : 1.0f;

	// 鍙虫墜鍚戝乏鎽嗗姩锛?Y锛夆啋 妯″瀷 ID 鍙嶅悜鏇存柊銆?
	if (bRightHandPresent && RightHandSwipeCooldown <= 0.0f
		&& RightHandConfidence >= MinHandConfidence && IsLateralSwipe(RightPalmVelocity))
	{
		if (AxisSign * RightPalmVelocity.Y < 0.0f)
		{
			CycleModel(-1);
			// 闃查棯鐑佷箣鍥涳細姣忔墜鐙珛鍐峰嵈锛屽崟娆℃尌鍔ㄤ笉浼氬湪澶氬抚鍐呴噸澶嶈Е鍙戙€?
			RightHandSwipeCooldown = SwipeCooldownSeconds;
		}
	}

	// 宸︽墜鍚戝彸鎸ュ姩锛?Y锛夆啋 妯″瀷 ID 姝ｅ悜鏇存柊銆?
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
	// 闃查棯鐑佷箣浜?涓夛細閫熷害闃堝€艰繃婊ゅ井灏忔姈鍔紱瑕佹眰姘村钩(宸﹀彸 Y 杞?鍒嗛噺涓诲锛?
	// 閬垮厤涓婁笅/鍓嶅悗绉诲姩琚鍒や负鎸ユ墜銆?
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

	// 浠ユ湁鏁堝綋鍓嶆€侊紙杩囨浮涓互鐩爣鎬佷负鍑嗭級涓哄熀鍑嗗仛鐜粫寰幆銆?
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

	// 涓嶅啀瑕嗙洊 StaticMesh 缁勪欢涓婂凡鏈夌殑鏉愯川銆?
	// 鏋勯€犲嚱鏁帮紙BurstSMTestActor锛夊凡涓烘瘡涓?Mesh 璁剧疆浜嗘纭殑鐜夌煶鏉愯川
	// 锛圡I_TYS_Jade_SSS / MI_YF_Jade_SSS / MI_YZL_Jade_SSS锛夛紝
	CaptureInitialStateMaterials();
	for (int32 StateIndex = 0; StateIndex < StateMeshComponents.Num(); ++StateIndex)
	{
		RestoreStateInitialMaterials(StateIndex);
	}

	bInitialStateMaterialsApplied = true;
	SetRuntimeStateVisibility(CurrentStateIndex);
}

void UBurstMeshStateSwitcherComponent::CaptureInitialStateMaterials()
{
	InitialStateMaterials.Reset();
	InitialStateMaterialOffsets.Reset();
	InitialStateMaterialCounts.Reset();

	InitialStateMaterialOffsets.SetNum(StateMeshComponents.Num());
	InitialStateMaterialCounts.SetNum(StateMeshComponents.Num());

	for (int32 StateIndex = 0; StateIndex < StateMeshComponents.Num(); ++StateIndex)
	{
		UStaticMeshComponent* MeshComponent = StateMeshComponents[StateIndex];
		InitialStateMaterialOffsets[StateIndex] = InitialStateMaterials.Num();
		InitialStateMaterialCounts[StateIndex] = 0;
		if (!MeshComponent)
		{
			continue;
		}

		const int32 MaterialCount = FMath::Max(MeshComponent->GetNumMaterials(), 1);
		InitialStateMaterialCounts[StateIndex] = MaterialCount;
		for (int32 MaterialIndex = 0; MaterialIndex < MaterialCount; ++MaterialIndex)
		{
			InitialStateMaterials.Add(ResolveInitialDisplayMaterial(MeshComponent, MaterialIndex, StateIndex));
		}
	}
}

void UBurstMeshStateSwitcherComponent::RestoreStateInitialMaterials(int32 StateIndex)
{
	if (!StateMeshComponents.IsValidIndex(StateIndex) || !StateMeshComponents[StateIndex]
		|| !InitialStateMaterialOffsets.IsValidIndex(StateIndex)
		|| !InitialStateMaterialCounts.IsValidIndex(StateIndex))
	{
		return;
	}

	UStaticMeshComponent* MeshComponent = StateMeshComponents[StateIndex];
	const int32 Offset = InitialStateMaterialOffsets[StateIndex];
	const int32 Count = InitialStateMaterialCounts[StateIndex];
	MeshComponent->EmptyOverrideMaterials();
	for (int32 MaterialIndex = 0; MaterialIndex < Count; ++MaterialIndex)
	{
		if (InitialStateMaterials.IsValidIndex(Offset + MaterialIndex)
			&& InitialStateMaterials[Offset + MaterialIndex])
		{
			MeshComponent->SetMaterial(MaterialIndex, InitialStateMaterials[Offset + MaterialIndex]);
		}
	}
}

UMaterialInterface* UBurstMeshStateSwitcherComponent::GetStateInitialMaterial(int32 StateIndex, int32 MaterialIndex) const
{
	if (InitialStateMaterialOffsets.IsValidIndex(StateIndex)
		&& InitialStateMaterialCounts.IsValidIndex(StateIndex)
		&& MaterialIndex >= 0
		&& MaterialIndex < InitialStateMaterialCounts[StateIndex])
	{
		const int32 MaterialOffset = InitialStateMaterialOffsets[StateIndex] + MaterialIndex;
		if (InitialStateMaterials.IsValidIndex(MaterialOffset) && InitialStateMaterials[MaterialOffset])
		{
			return InitialStateMaterials[MaterialOffset];
		}
	}

	UStaticMeshComponent* MeshComponent = StateMeshComponents.IsValidIndex(StateIndex)
		? StateMeshComponents[StateIndex]
		: nullptr;
	return ResolveInitialDisplayMaterial(MeshComponent, MaterialIndex, StateIndex);
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
		// 濮嬬粓浣跨敤缃戞牸鍙樺舰绯荤粺锛圥_Morph_5_SM锛夈€侻orphParticleSystem 鏄柊灞炴€э紝BP 瀹炰緥涓嶄細瑕嗙洊銆?
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
			const bool bShouldBeVisible = (Index == VisibleStateIndex);
			MeshComponent->SetVisibility(bShouldBeVisible, true);
			MeshComponent->SetHiddenInGame(!bShouldBeVisible, true);
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

	// P_Morph_5_SM 鐢?User.Static Mesh0 浣滀负婧愬舰鐘躲€乁ser.Static Mesh1 浣滀负鐩爣褰㈢姸銆?
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
	// 鍘绘帀 Spring 鍔涳紙淇濈暀 Noise锛夛細璁╃矑瀛愭丁娴佸悜澶栨秷鏁ｈ€岄潪寮瑰洖鐩爣銆?
	TransformationNiagara->SetVariableFloat(TEXT("User.Spring Force"), 0.0f);
	// 绮掑瓙棰滆壊 = 鐩爣妯″瀷鐜夌煶鏉愯川锛氭妸鐩爣鐘舵€佺殑鐜夌煶鏉愯川璁惧埌 User.ParticleMaterial锛?
	// 锛堥渶鍦?Niagara 閲屾妸 Sprite Renderer 鐨?Material 缁戝畾鍒?User 鍙傛暟 ParticleMaterial锛夈€?
	const int32 TargetStateIdx = (PendingStateIndex != INDEX_NONE) ? PendingStateIndex : CurrentStateIndex;
	if (UMaterialInterface* TargetMaterial = GetStateInitialMaterial(TargetStateIdx))
	{
		TransformationNiagara->SetVariableMaterial(TEXT("User.ParticleMaterial"), TargetMaterial);
		TransformationNiagara->SetVariableMaterial(TEXT("User.Particle Material"), TargetMaterial);
	}
	ApplyMorphParameters();
}

void UBurstMeshStateSwitcherComponent::ApplyMorphParameters()
{
	// 浠呭湪鏄惧紡寮€鍚椂瑕嗙洊锛堜繚鐣欑粰 P_Morph 绯诲垪绯荤粺鐨勫彲閫夎皟鍙傦紝鍚稿叆绯荤粺涓嬫棤鍓綔鐢級銆?
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
	// 鏈夋晥褰撳墠鎬侊細杩囨浮涓互姝ｅ湪鍒囧線鐨勭洰鏍?PendingStateIndex)涓哄噯锛屽惁鍒欎负宸叉樉绀烘€?CurrentStateIndex)銆?
	// 闃叉杩囨浮涓啀鎸夊悓涓€涓洰鏍囬敭閲嶅瑙﹀彂銆?
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

	// 浠ョ湡姝ｇ殑褰撳墠鏄剧ず鎬佷负婧愶紱骞跺己鍒跺彧鏄剧ず瀹冿紙闅愯棌浠讳綍涓婁竴娆¤繃娓℃畫鐣欑殑缃戞牸锛夈€?
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
	// 鍏堣婧?鐩爣缃戞牸鍐嶉噸缃郴缁燂紝閲嶇疆鍚庡啀璁句竴娆★紝纭繚鏁版嵁鎺ュ彛鍦ㄩ噸鏂板垵濮嬪寲鍚庢嬁鍒版纭殑缃戞牸銆?
	ApplyParticleSettings();
	TransformationNiagara->ReinitializeSystem();
	ApplyParticleSettings();
	TransformationNiagara->SetHiddenInGame(false, true);
	TransformationNiagara->SetVisibility(true, true);
	TransformationNiagara->Activate(true);

	if (UWorld* World = GetWorld())
	{
		const float EffectiveDuration = FMath::Max(FrontHalfDuration, 0.1f);
		// 鍙樺舰绯荤粺鑷甫绮掑瓙杩愬姩锛屼笉闇€瑕侀€愬抚椹卞姩 Transformation Alpha銆?
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

	ActiveSourceFadeMaterials.Reset();
	RestoreStateInitialMaterials(CurrentStateIndex);
	SourceMeshComponent->SetVisibility(false, true);
	SourceMeshComponent->SetHiddenInGame(true, true);
	bSourceFadeOutActive = false;
	UE_LOG(LogTemp, Display, TEXT("BurstMeshStateSwitcher: source model hidden; particles carry the transition."));
}

void UBurstMeshStateSwitcherComponent::BeginModelReveal()
{
	if (!StateMeshComponents.IsValidIndex(PendingStateIndex) || !TargetMeshComponent)
	{
		return;
	}

	// 娉ㄦ剰锛欳urrentStateIndex 涓嶅湪杩欓噷鏇存柊锛屽繀椤荤瓑鐩爣鐪熸鏄剧ず鍚庯紙CompleteTransition锛夋墠鍒囨崲锛?
	// 鍚﹀垯蹇€熷垏鎹㈣鎵撴柇鏃朵細娈嬬暀涓婁竴涓洰鏍囩綉鏍硷紝瀵艰嚧涓や釜妯″瀷鍚屾椂鍑虹幇銆?
	bTransitionActive = false;

	TargetMeshComponent->EmptyOverrideMaterials();
	// 杩囨浮鏈熼棿鎵€鏈夌姸鎬佺綉鏍奸兘闅愯棌锛堢矑瀛愪唬琛ㄨ繃娓★級锛岀洰鏍囩瓑绮掑瓙娑堟暎鍚庡啀鎻ず銆?
	SetRuntimeStateVisibility(INDEX_NONE);

	// 鍋滄绮掑瓙缁х画鐢熸垚锛岃鐜版湁绮掑瓙鎸夎嚜韬敓鍛藉懆鏈熻嚜鐒舵秷鏁ｃ€?
	if (TransformationNiagara)
	{
		TransformationNiagara->Deactivate();
	}

	// 绮掑瓙瀹屽叏娑堟暎鍚庯紙ParticleFadeOutDuration锛夋墠鏄剧ず鏂版ā鍨嬪畬鏁存潗璐ㄣ€?
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
	// 绮掑瓙鍔ㄧ敾缁撴潫锛氬厛褰诲簳闅愯棌/娓呯悊绮掑瓙锛屽啀鎻ず鏂版ā鍨嬪畬鏁存潗璐ㄣ€?
	StopAndHideParticles();
	BeginTargetModelFadeIn();
}

void UBurstMeshStateSwitcherComponent::BeginTargetModelFadeIn()
{
	if (!TargetMeshComponent || PendingStateIndex == INDEX_NONE)
	{
		return;
	}

	UE_LOG(LogTemp, Display, TEXT("BurstMeshStateSwitcher: particle fade complete; revealing target model with initial material."));
	ActiveFadeMaterials.Reset();
	RestoreStateInitialMaterials(PendingStateIndex);
	bFadeInActive = false;
	bFadeRevealPending = false;
	SetRuntimeStateVisibility(PendingStateIndex);
	CompleteTransition();
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
		// 鐢?Deactivate锛堝仠姝㈢敓鎴愩€佷繚鐣欏凡瀛樺湪绮掑瓙鑷劧娑堟暎锛夎€屼笉鏄?DeactivateImmediate锛堢灛闂存竻绌猴級锛?
		// 淇濇寔鏌斿拰娣″嚭鐨勮鎰熴€?
		TransformationNiagara->Deactivate();
		TransformationNiagara->SetVisibility(false, true);
		TransformationNiagara->SetHiddenInGame(true, true);
	}
	bParticleFadeOutActive = false;
	ParticleFadeOutElapsed = 0.0f;
	ActiveParticleMaterial = nullptr;
}

void UBurstMeshStateSwitcherComponent::CompleteTransition()
{
	if (TargetMeshComponent)
	{
		// 杩囨浮鐪熸瀹屾垚锛氱幇鍦ㄦ墠鎶婂綋鍓嶇姸鎬佸垏鍒扮洰鏍囷紝骞跺己鍒跺彧鏄剧ず瀹冿紙闅愯棌鍏朵綑锛夛紝鏉滅粷涓や釜鍚屾椂鍑虹幇銆?		if (PendingStateIndex != INDEX_NONE)
		{
			CurrentStateIndex = PendingStateIndex;
		}
		// 杩囨浮瀹屾垚锛氭仮澶嶇洰鏍囨ā鍨嬪湪鍏冲崱瀹炰緥/钃濆浘妯℃澘涓殑鍒濆鏉愯川銆?		RestoreStateInitialMaterials(CurrentStateIndex);
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
