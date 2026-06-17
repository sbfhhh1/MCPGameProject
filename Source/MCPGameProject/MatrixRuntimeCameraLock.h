#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MatrixRuntimeCameraLock.generated.h"

class APlayerController;

UCLASS(Blueprintable)
class MCPGAMEPROJECT_API AMatrixRuntimeCameraLock : public AActor
{
	GENERATED_BODY()

public:
	AMatrixRuntimeCameraLock();

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaTime) override;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Camera")
	TObjectPtr<AActor> CameraActor;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Camera")
	FName CameraTag = TEXT("Matrix_OverviewCamera");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Camera", meta = (ClampMin = "0.0", UIMin = "0.0"))
	float BlendTime = 0.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Camera")
	bool bReapplyEveryTick = true;

private:
	AActor* ResolveCameraActor();
	void ApplyViewTarget();
};
