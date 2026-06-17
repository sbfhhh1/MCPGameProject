#include "MatrixRuntimeCameraLock.h"

#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"

AMatrixRuntimeCameraLock::AMatrixRuntimeCameraLock()
{
	PrimaryActorTick.bCanEverTick = true;
}

void AMatrixRuntimeCameraLock::BeginPlay()
{
	Super::BeginPlay();
	ApplyViewTarget();
}

void AMatrixRuntimeCameraLock::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);

	if (bReapplyEveryTick)
	{
		ApplyViewTarget();
	}
}

AActor* AMatrixRuntimeCameraLock::ResolveCameraActor()
{
	if (IsValid(CameraActor))
	{
		return CameraActor;
	}

	if (CameraTag.IsNone())
	{
		return nullptr;
	}

	TArray<AActor*> TaggedActors;
	UGameplayStatics::GetAllActorsWithTag(this, CameraTag, TaggedActors);
	if (TaggedActors.Num() > 0)
	{
		CameraActor = TaggedActors[0];
		return CameraActor;
	}

	return nullptr;
}

void AMatrixRuntimeCameraLock::ApplyViewTarget()
{
	AActor* TargetCamera = ResolveCameraActor();
	APlayerController* PlayerController = UGameplayStatics::GetPlayerController(this, 0);
	if (!IsValid(TargetCamera) || !IsValid(PlayerController) || PlayerController->GetViewTarget() == TargetCamera)
	{
		return;
	}

	if (BlendTime <= 0.0f)
	{
		PlayerController->SetViewTarget(TargetCamera);
	}
	else
	{
		PlayerController->SetViewTargetWithBlend(TargetCamera, BlendTime);
	}
}
