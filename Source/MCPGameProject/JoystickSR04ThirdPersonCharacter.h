#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "JoystickSR04ReceiverComponent.h"
#include "JoystickSR04ThirdPersonCharacter.generated.h"

class ACameraActor;

UCLASS(Blueprintable)
class MCPGAMEPROJECT_API AJoystickSR04ThirdPersonCharacter : public ACharacter
{
	GENERATED_BODY()

public:
	AJoystickSR04ThirdPersonCharacter();

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;
	virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "JoystickSR04|Source")
	TObjectPtr<AActor> ReceiverActor;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "JoystickSR04|Source")
	FName ReceiverActorTag = TEXT("JoystickSR04Receiver");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "JoystickSR04|Camera")
	TObjectPtr<ACameraActor> FixedCamera;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "JoystickSR04|Camera")
	FName FixedCameraTag = TEXT("JoystickFixedCamera");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "JoystickSR04|Movement", meta = (ClampMin = "0.0", UIMin = "0.0"))
	float MoveInputScale = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "JoystickSR04|Movement")
	bool bRotateTowardMovement = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "JoystickSR04|Distance", meta = (ClampMin = "0.0", UIMin = "0.0"))
	float ControlDistanceThreshold = 40.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "JoystickSR04|Patrol", meta = (ClampMin = "0.0", UIMin = "0.0"))
	float AutoPatrolSpeed = 220.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "JoystickSR04|Patrol", meta = (ClampMin = "1.0", UIMin = "1.0"))
	float PatrolAcceptanceRadius = 80.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "JoystickSR04|Patrol", meta = (ClampMin = "0.0", UIMin = "0.0"))
	float PatrolPointMinInterval = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "JoystickSR04|Patrol", meta = (ClampMin = "0.1", UIMin = "0.1"))
	float PatrolTargetTimeout = 6.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "JoystickSR04|Patrol", meta = (ClampMin = "0.0", ClampMax = "0.45", UIMin = "0.0", UIMax = "0.45"))
	float PatrolViewportPadding = 0.12f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "JoystickSR04|Patrol", meta = (ClampMin = "100.0", UIMin = "100.0"))
	float PatrolFallbackExtent = 1400.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "JoystickSR04|Patrol")
	FVector PatrolNavProjectionExtent = FVector(800.0f, 800.0f, 500.0f);

private:
	UPROPERTY(Transient)
	TObjectPtr<UJoystickSR04ReceiverComponent> Receiver;

	FVector InitialLocation = FVector::ZeroVector;
	FVector PatrolTargetLocation = FVector::ZeroVector;
	TArray<FVector> PatrolPathPoints;
	float JoystickWalkSpeed = 500.0f;
	float TimeSinceLastPatrolTarget = 0.0f;
	int32 PatrolPathPointIndex = 0;
	bool bHasPatrolTarget = false;

	void ResolveReceiver();
	void ResolveFixedCamera();
	void HandleJoystickControl();
	void HandleAutoPatrol(float DeltaSeconds);
	void ClearPatrolTarget();
	bool PickPatrolTarget(FVector& OutTarget) const;
	bool BuildPatrolPath(const FVector& Destination);
	FVector GetCurrentPatrolMoveTarget() const;
	bool DeprojectViewportPointToGround(float ScreenX, float ScreenY, FVector& OutPoint) const;
	bool IsSensorFrameValid() const;
	void MoveInDirection(const FVector& MoveDirection, float Scale);
	FVector GetCameraRelativeMoveDirection() const;
	FVector GetRawJoystickDirection() const;
};
