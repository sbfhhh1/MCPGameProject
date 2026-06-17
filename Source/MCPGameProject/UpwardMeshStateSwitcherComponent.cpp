#include "UpwardMeshStateSwitcherComponent.h"

#include "Components/BoxComponent.h"
#include "Components/InputComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "NiagaraComponent.h"
#include "TimerManager.h"
#include "UObject/ConstructorHelpers.h"

UUpwardMeshStateSwitcherComponent::UUpwardMeshStateSwitcherComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.bStartWithTickEnabled = false;

	static ConstructorHelpers::FObjectFinder<UStaticMesh> ChairMesh(
		TEXT("/Game/TransformationVFX/Demo/StaticMesh/SM_Chair.SM_Chair"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> TableMesh(
		TEXT("/Game/TransformationVFX/Demo/StaticMesh/SM_TableRound.SM_TableRound"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> SphereMesh(
		TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	static ConstructorHelpers::FObjectFinder<UMaterialInterface> ChairFadeMaterial(
		TEXT("/Game/TransformationVFX/Material/ObjectMaterial/MI_Chair_UniversalDissolve.MI_Chair_UniversalDissolve"));
	static ConstructorHelpers::FObjectFinder<UMaterialInterface> TableFadeMaterial(
		TEXT("/Game/TransformationVFX/Material/ObjectMaterial/MI_TableRound_UniversalDissolve.MI_TableRound_UniversalDissolve"));

	StateMeshes = {ChairMesh.Object, TableMesh.Object, SphereMesh.Object};
	StateFadeMaterials = {ChairFadeMaterial.Object, TableFadeMaterial.Object, nullptr};
}

void UUpwardMeshStateSwitcherComponent::BeginPlay()
{
	Super::BeginPlay();

	CacheOwnerComponents();
	DisableLegacyOverlapTrigger();
	BindNumberKeys();

	if (SourceMeshComponent && StateMeshes.IsValidIndex(CurrentStateIndex))
	{
		SourceMeshComponent->SetStaticMesh(StateMeshes[CurrentStateIndex]);
		SourceMeshComponent->SetVisibility(true, true);
	}
	if (TargetMeshComponent)
	{
		TargetMeshComponent->SetVisibility(false, true);
	}
	if (TransformationNiagara)
	{
		TransformationNiagara->DeactivateImmediate();
	}
	SetComponentTickEnabled(false);
}

void UUpwardMeshStateSwitcherComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().ClearTimer(HideSourceTimer);
		World->GetTimerManager().ClearTimer(StopParticleSpawningTimer);
		World->GetTimerManager().ClearTimer(FinishTransitionTimer);
	}
	Super::EndPlay(EndPlayReason);
}

void UUpwardMeshStateSwitcherComponent::TickComponent(
	float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	if (!bFadeInActive || !SourceMeshComponent)
	{
		return;
	}

	if (bFadeRevealPending)
	{
		// The dissolve material and its start value were prepared while hidden.
		// Reveal on the following frame so the untouched material never flashes.
		bFadeRevealPending = false;
		SourceMeshComponent->SetVisibility(true, true);
		return;
	}

	FadeInElapsed += DeltaTime;
	const float Alpha = FMath::Clamp(FadeInElapsed / FMath::Max(FadeInDuration, 0.01f), 0.0f, 1.0f);
	const float SmoothedAlpha = FMath::SmoothStep(0.0f, 1.0f, Alpha);

	if (ActiveFadeMaterial)
	{
		ActiveFadeMaterial->SetScalarParameterValue(TEXT("Dissolve Amount"), FMath::Lerp(0.65f, 0.0f, SmoothedAlpha));
	}
	SourceMeshComponent->SetRelativeScale3D(
		FMath::Lerp(ModelFullScale * 0.94f, ModelFullScale, SmoothedAlpha));

	if (Alpha >= 1.0f)
	{
		CompleteModelFadeIn();
	}
}

void UUpwardMeshStateSwitcherComponent::CacheOwnerComponents()
{
	AActor* Owner = GetOwner();
	if (!Owner)
	{
		return;
	}

	TArray<UStaticMeshComponent*> MeshComponents;
	Owner->GetComponents(MeshComponents);
	for (UStaticMeshComponent* MeshComponent : MeshComponents)
	{
		const FString Name = MeshComponent->GetName();
		if (Name.Contains(TEXT("Static Mesh A")))
		{
			SourceMeshComponent = MeshComponent;
		}
		else if (Name.Contains(TEXT("Static Mesh B")))
		{
			TargetMeshComponent = MeshComponent;
		}
	}

	TransformationNiagara = Owner->FindComponentByClass<UNiagaraComponent>();
}

void UUpwardMeshStateSwitcherComponent::DisableLegacyOverlapTrigger()
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
}

void UUpwardMeshStateSwitcherComponent::BindNumberKeys()
{
	AActor* Owner = GetOwner();
	APlayerController* PlayerController = UGameplayStatics::GetPlayerController(this, 0);
	if (!Owner || !PlayerController)
	{
		return;
	}

	Owner->EnableInput(PlayerController);
	if (!Owner->InputComponent)
	{
		return;
	}

	Owner->InputComponent->BindKey(EKeys::One, IE_Pressed, this, &UUpwardMeshStateSwitcherComponent::SwitchToStateOne);
	Owner->InputComponent->BindKey(EKeys::Two, IE_Pressed, this, &UUpwardMeshStateSwitcherComponent::SwitchToStateTwo);
	Owner->InputComponent->BindKey(EKeys::Three, IE_Pressed, this, &UUpwardMeshStateSwitcherComponent::SwitchToStateThree);
}

void UUpwardMeshStateSwitcherComponent::SwitchToStateOne()
{
	SwitchToState(0);
}

void UUpwardMeshStateSwitcherComponent::SwitchToStateTwo()
{
	SwitchToState(1);
}

void UUpwardMeshStateSwitcherComponent::SwitchToStateThree()
{
	SwitchToState(2);
}

void UUpwardMeshStateSwitcherComponent::SwitchToState(int32 StateIndex)
{
	if (!StateMeshes.IsValidIndex(StateIndex) || !StateMeshes[StateIndex] || StateIndex == CurrentStateIndex)
	{
		return;
	}
	if (bFadeInActive)
	{
		CompleteModelFadeIn();
	}
	if (!SourceMeshComponent || !TargetMeshComponent || !TransformationNiagara)
	{
		CacheOwnerComponents();
	}
	if (!SourceMeshComponent || !TargetMeshComponent || !TransformationNiagara)
	{
		UE_LOG(LogTemp, Warning, TEXT("UpwardMeshStateSwitcher: BP_Upward_SM components were not found."));
		return;
	}

	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().ClearTimer(HideSourceTimer);
		World->GetTimerManager().ClearTimer(StopParticleSpawningTimer);
		World->GetTimerManager().ClearTimer(FinishTransitionTimer);
	}

	PendingStateIndex = StateIndex;
	UE_LOG(LogTemp, Display, TEXT("UpwardMeshStateSwitcher: switching from state %d to state %d."),
		CurrentStateIndex + 1, PendingStateIndex + 1);
	SourceMeshComponent->SetStaticMesh(StateMeshes[CurrentStateIndex]);
	TargetMeshComponent->SetStaticMesh(StateMeshes[PendingStateIndex]);
	SourceMeshComponent->EmptyOverrideMaterials();
	TargetMeshComponent->EmptyOverrideMaterials();
	SourceMeshComponent->SetVisibility(true, true);
	TargetMeshComponent->SetVisibility(false, true);

	TransformationNiagara->SetVariableInt(TEXT("User.CurrentMode"), 0);
	TransformationNiagara->ReinitializeSystem();
	TransformationNiagara->SetEmitterEnable(TEXT("Morph_Particle"), true);
	TransformationNiagara->SetEmitterEnable(TEXT("Morph_Particle001"), false);
	TransformationNiagara->Activate(true);

	if (UWorld* World = GetWorld())
	{
		constexpr float StopSpawningBeforeSecondBurstTime = 1.0f;
		constexpr float FirstUpwardBurstLandingTime = 2.0f;
		World->GetTimerManager().SetTimer(
			HideSourceTimer, this, &UUpwardMeshStateSwitcherComponent::HideSourceMesh, SourceHideDelay, false);
		World->GetTimerManager().SetTimer(
			StopParticleSpawningTimer, this, &UUpwardMeshStateSwitcherComponent::StopParticleSpawning,
			StopSpawningBeforeSecondBurstTime, false);
		World->GetTimerManager().SetTimer(
			FinishTransitionTimer, this, &UUpwardMeshStateSwitcherComponent::FinishTransition,
			FirstUpwardBurstLandingTime, false);
	}
}

void UUpwardMeshStateSwitcherComponent::HideSourceMesh()
{
	if (SourceMeshComponent)
	{
		SourceMeshComponent->SetVisibility(false, true);
	}
}

void UUpwardMeshStateSwitcherComponent::StopParticleSpawning()
{
	if (TransformationNiagara)
	{
		// Stop new particles and the second loop while allowing the first burst
		// particles already in flight to finish falling.
		TransformationNiagara->Deactivate();
	}
}

void UUpwardMeshStateSwitcherComponent::FinishTransition()
{
	if (!StateMeshes.IsValidIndex(PendingStateIndex))
	{
		return;
	}

	CurrentStateIndex = PendingStateIndex;
	PendingStateIndex = INDEX_NONE;
	UE_LOG(LogTemp, Display, TEXT("UpwardMeshStateSwitcher: state %d transition complete."), CurrentStateIndex + 1);

	SourceMeshComponent->SetStaticMesh(StateMeshes[CurrentStateIndex]);
	TargetMeshComponent->SetVisibility(false, true);
	TransformationNiagara->DeactivateImmediate();
	BeginModelFadeIn();
}

void UUpwardMeshStateSwitcherComponent::BeginModelFadeIn()
{
	if (!SourceMeshComponent)
	{
		return;
	}

	SourceMeshComponent->EmptyOverrideMaterials();
	SourceMeshComponent->SetVisibility(false, true);
	ModelFullScale = SourceMeshComponent->GetRelativeScale3D();
	FadeInElapsed = 0.0f;
	bFadeInActive = true;
	bFadeRevealPending = true;
	ActiveFadeMaterial = nullptr;

	if (StateFadeMaterials.IsValidIndex(CurrentStateIndex) && StateFadeMaterials[CurrentStateIndex])
	{
		ActiveFadeMaterial = SourceMeshComponent->CreateDynamicMaterialInstance(0, StateFadeMaterials[CurrentStateIndex]);
		if (ActiveFadeMaterial)
		{
			ActiveFadeMaterial->SetScalarParameterValue(TEXT("Dissolve Amount"), 0.65f);
		}
	}

	SourceMeshComponent->SetRelativeScale3D(ModelFullScale * 0.94f);
	SetComponentTickEnabled(true);
}

void UUpwardMeshStateSwitcherComponent::CompleteModelFadeIn()
{
	if (SourceMeshComponent)
	{
		SourceMeshComponent->SetRelativeScale3D(ModelFullScale);
		SourceMeshComponent->EmptyOverrideMaterials();
	}
	ActiveFadeMaterial = nullptr;
	bFadeInActive = false;
	bFadeRevealPending = false;
	SetComponentTickEnabled(false);
}
