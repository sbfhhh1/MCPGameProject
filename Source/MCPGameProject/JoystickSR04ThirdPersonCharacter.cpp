#include "JoystickSR04ThirdPersonCharacter.h"

#include "Camera/CameraActor.h"
#include "Components/CapsuleComponent.h"
#include "Animation/AnimInstance.h"
#include "Engine/SkeletalMesh.h"
#include "EngineUtils.h"
#include "Engine/World.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "NavigationPath.h"
#include "NavigationSystem.h"
#include "UObject/ConstructorHelpers.h"

AJoystickSR04ThirdPersonCharacter::AJoystickSR04ThirdPersonCharacter()
{
	PrimaryActorTick.bCanEverTick = true;

	bUseControllerRotationPitch = false;
	bUseControllerRotationYaw = false;
	bUseControllerRotationRoll = false;

	GetCapsuleComponent()->InitCapsuleSize(42.0f, 96.0f);

	UCharacterMovementComponent* Movement = GetCharacterMovement();
	Movement->bOrientRotationToMovement = true;
	Movement->RotationRate = FRotator(0.0f, 500.0f, 0.0f);
	Movement->MaxWalkSpeed = 500.0f;
	Movement->BrakingDecelerationWalking = 2000.0f;

	static ConstructorHelpers::FObjectFinder<USkeletalMesh> MannyMesh(
		TEXT("/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple.SKM_Manny_Simple"));
	if (MannyMesh.Succeeded())
	{
		GetMesh()->SetSkeletalMesh(MannyMesh.Object);
		GetMesh()->SetRelativeLocation(FVector(0.0f, 0.0f, -89.0f));
		GetMesh()->SetRelativeRotation(FRotator(0.0f, -90.0f, 0.0f));
	}

	static ConstructorHelpers::FClassFinder<UAnimInstance> UnarmedAnimBlueprint(
		TEXT("/Game/Characters/Mannequins/Anims/Unarmed/ABP_Unarmed"));
	if (UnarmedAnimBlueprint.Succeeded())
	{
		GetMesh()->SetAnimInstanceClass(UnarmedAnimBlueprint.Class);
	}
}

void AJoystickSR04ThirdPersonCharacter::BeginPlay()
{
	Super::BeginPlay();

	InitialLocation = GetActorLocation();
	JoystickWalkSpeed = GetCharacterMovement() ? GetCharacterMovement()->MaxWalkSpeed : JoystickWalkSpeed;
	ResolveReceiver();
	ResolveFixedCamera();
}

void AJoystickSR04ThirdPersonCharacter::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	if (!Receiver)
	{
		ResolveReceiver();
	}

	if (!FixedCamera)
	{
		ResolveFixedCamera();
	}

	if (!IsSensorFrameValid())
	{
		ClearPatrolTarget();
		return;
	}

	if (Receiver->Distance < ControlDistanceThreshold)
	{
		HandleJoystickControl();
	}
	else
	{
		HandleAutoPatrol(DeltaSeconds);
	}
}

void AJoystickSR04ThirdPersonCharacter::HandleJoystickControl()
{
	ClearPatrolTarget();
	if (UCharacterMovementComponent* Movement = GetCharacterMovement())
	{
		Movement->MaxWalkSpeed = JoystickWalkSpeed;
	}

	const FVector MoveDirection = GetCameraRelativeMoveDirection();
	if (!MoveDirection.IsNearlyZero())
	{
		MoveInDirection(MoveDirection, MoveInputScale);
	}
}

void AJoystickSR04ThirdPersonCharacter::HandleAutoPatrol(float DeltaSeconds)
{
	TimeSinceLastPatrolTarget += DeltaSeconds;
	if (UCharacterMovementComponent* Movement = GetCharacterMovement())
	{
		Movement->MaxWalkSpeed = AutoPatrolSpeed;
	}

	const float DistanceToTarget = bHasPatrolTarget
		? FVector::Dist2D(GetActorLocation(), GetCurrentPatrolMoveTarget())
		: TNumericLimits<float>::Max();

	if (bHasPatrolTarget && DistanceToTarget <= PatrolAcceptanceRadius)
	{
		if (PatrolPathPoints.IsValidIndex(PatrolPathPointIndex + 1))
		{
			++PatrolPathPointIndex;
		}
		else if (TimeSinceLastPatrolTarget >= PatrolPointMinInterval)
		{
			ClearPatrolTarget();
		}
	}

	if (!bHasPatrolTarget || TimeSinceLastPatrolTarget >= PatrolTargetTimeout)
	{
		FVector NewTarget = FVector::ZeroVector;
		if (PickPatrolTarget(NewTarget) && BuildPatrolPath(NewTarget))
		{
			PatrolTargetLocation = NewTarget;
			bHasPatrolTarget = true;
			TimeSinceLastPatrolTarget = 0.0f;
		}
	}

	if (!bHasPatrolTarget)
	{
		return;
	}

	FVector MoveDirection = GetCurrentPatrolMoveTarget() - GetActorLocation();
	MoveDirection.Z = 0.0f;
	MoveInDirection(MoveDirection.GetSafeNormal(), 1.0f);
}

void AJoystickSR04ThirdPersonCharacter::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	Super::SetupPlayerInputComponent(PlayerInputComponent);
	// Intentionally no Enhanced Input or mouse-look bindings; movement comes from JoystickSR04 UDP data.
}

void AJoystickSR04ThirdPersonCharacter::ClearPatrolTarget()
{
	bHasPatrolTarget = false;
	PatrolPathPoints.Reset();
	PatrolPathPointIndex = 0;
	TimeSinceLastPatrolTarget = 0.0f;
}

bool AJoystickSR04ThirdPersonCharacter::PickPatrolTarget(FVector& OutTarget) const
{
	UNavigationSystemV1* NavSystem = UNavigationSystemV1::GetCurrent(GetWorld());
	if (!NavSystem)
	{
		return false;
	}

	APlayerController* PlayerController = UGameplayStatics::GetPlayerController(this, 0);
	int32 ViewportSizeX = 0;
	int32 ViewportSizeY = 0;
	if (PlayerController)
	{
		PlayerController->GetViewportSize(ViewportSizeX, ViewportSizeY);
	}

	if (ViewportSizeX > 0 && ViewportSizeY > 0)
	{
		const float PaddingX = FMath::Clamp(PatrolViewportPadding, 0.0f, 0.45f) * static_cast<float>(ViewportSizeX);
		const float PaddingY = FMath::Clamp(PatrolViewportPadding, 0.0f, 0.45f) * static_cast<float>(ViewportSizeY);
		const float MinX = PaddingX;
		const float MaxX = FMath::Max(PaddingX, static_cast<float>(ViewportSizeX) - PaddingX);
		const float MinY = PaddingY;
		const float MaxY = FMath::Max(PaddingY, static_cast<float>(ViewportSizeY) - PaddingY);

		for (int32 Attempt = 0; Attempt < 12; ++Attempt)
		{
			const float ScreenX = FMath::FRandRange(MinX, MaxX);
			const float ScreenY = FMath::FRandRange(MinY, MaxY);
			FVector GroundPoint = FVector::ZeroVector;
			FNavLocation ProjectedPoint;
			if (DeprojectViewportPointToGround(ScreenX, ScreenY, GroundPoint) &&
				NavSystem->ProjectPointToNavigation(GroundPoint, ProjectedPoint, PatrolNavProjectionExtent))
			{
				OutTarget = ProjectedPoint.Location;
				return true;
			}
		}
	}

	FNavLocation RandomPoint;
	if (NavSystem->GetRandomReachablePointInRadius(InitialLocation, PatrolFallbackExtent, RandomPoint))
	{
		OutTarget = RandomPoint.Location;
		return true;
	}

	return false;
}

bool AJoystickSR04ThirdPersonCharacter::BuildPatrolPath(const FVector& Destination)
{
	UNavigationPath* Path = UNavigationSystemV1::FindPathToLocationSynchronously(this, GetActorLocation(), Destination, this);
	if (!Path || !Path->IsValid() || Path->PathPoints.Num() == 0)
	{
		return false;
	}

	PatrolPathPoints = Path->PathPoints;
	PatrolPathPointIndex = PatrolPathPoints.Num() > 1 ? 1 : 0;
	return PatrolPathPoints.IsValidIndex(PatrolPathPointIndex);
}

FVector AJoystickSR04ThirdPersonCharacter::GetCurrentPatrolMoveTarget() const
{
	return PatrolPathPoints.IsValidIndex(PatrolPathPointIndex) ? PatrolPathPoints[PatrolPathPointIndex] : PatrolTargetLocation;
}

bool AJoystickSR04ThirdPersonCharacter::DeprojectViewportPointToGround(float ScreenX, float ScreenY, FVector& OutPoint) const
{
	APlayerController* PlayerController = UGameplayStatics::GetPlayerController(this, 0);
	if (!PlayerController)
	{
		return false;
	}

	FVector WorldOrigin = FVector::ZeroVector;
	FVector WorldDirection = FVector::ZeroVector;
	if (!PlayerController->DeprojectScreenPositionToWorld(ScreenX, ScreenY, WorldOrigin, WorldDirection))
	{
		return false;
	}

	if (FMath::IsNearlyZero(WorldDirection.Z))
	{
		return false;
	}

	const float GroundZ = GetActorLocation().Z;
	const float T = (GroundZ - WorldOrigin.Z) / WorldDirection.Z;
	if (T <= 0.0f)
	{
		return false;
	}

	OutPoint = WorldOrigin + WorldDirection * T;
	OutPoint.Z = GroundZ;
	return true;
}

bool AJoystickSR04ThirdPersonCharacter::IsSensorFrameValid() const
{
	return Receiver && Receiver->bIsConnected && Receiver->bDistanceValid;
}

void AJoystickSR04ThirdPersonCharacter::MoveInDirection(const FVector& MoveDirection, float Scale)
{
	if (MoveDirection.IsNearlyZero())
	{
		return;
	}

	AddMovementInput(MoveDirection, Scale);

	if (bRotateTowardMovement)
	{
		const FRotator TargetRotation = MoveDirection.Rotation();
		SetActorRotation(FRotator(0.0f, TargetRotation.Yaw, 0.0f));
	}
}

void AJoystickSR04ThirdPersonCharacter::ResolveReceiver()
{
	Receiver = nullptr;

	if (ReceiverActor)
	{
		Receiver = ReceiverActor->FindComponentByClass<UJoystickSR04ReceiverComponent>();
		if (Receiver)
		{
			return;
		}
	}

	TArray<AActor*> TaggedActors;
	if (!ReceiverActorTag.IsNone())
	{
		UGameplayStatics::GetAllActorsWithTag(this, ReceiverActorTag, TaggedActors);
		for (AActor* Actor : TaggedActors)
		{
			if (!IsValid(Actor))
			{
				continue;
			}

			Receiver = Actor->FindComponentByClass<UJoystickSR04ReceiverComponent>();
			if (Receiver)
			{
				ReceiverActor = Actor;
				return;
			}
		}
	}

	for (TActorIterator<AActor> It(GetWorld()); It; ++It)
	{
		AActor* Actor = *It;
		if (!IsValid(Actor))
		{
			continue;
		}

		Receiver = Actor->FindComponentByClass<UJoystickSR04ReceiverComponent>();
		if (Receiver)
		{
			ReceiverActor = Actor;
			return;
		}
	}
}

void AJoystickSR04ThirdPersonCharacter::ResolveFixedCamera()
{
	if (FixedCamera)
	{
		return;
	}

	TArray<AActor*> TaggedActors;
	if (!FixedCameraTag.IsNone())
	{
		UGameplayStatics::GetAllActorsWithTag(this, FixedCameraTag, TaggedActors);
		for (AActor* Actor : TaggedActors)
		{
			if (ACameraActor* CameraActor = Cast<ACameraActor>(Actor))
			{
				FixedCamera = CameraActor;
				return;
			}
		}
	}

	FixedCamera = Cast<ACameraActor>(UGameplayStatics::GetActorOfClass(this, ACameraActor::StaticClass()));
}

FVector AJoystickSR04ThirdPersonCharacter::GetCameraRelativeMoveDirection() const
{
	const FVector RawDirection = GetRawJoystickDirection();
	if (RawDirection.IsNearlyZero())
	{
		return FVector::ZeroVector;
	}

	const FRotator CameraRotation = FixedCamera ? FixedCamera->GetActorRotation() : FRotator(0.0f, 0.0f, 0.0f);
	FVector CameraForward = CameraRotation.Vector();
	CameraForward.Z = 0.0f;
	CameraForward.Normalize();

	FVector CameraRight = FRotationMatrix(CameraRotation).GetScaledAxis(EAxis::Y);
	CameraRight.Z = 0.0f;
	CameraRight.Normalize();

	if (CameraForward.IsNearlyZero())
	{
		CameraForward = FVector::ForwardVector;
	}
	if (CameraRight.IsNearlyZero())
	{
		CameraRight = FVector::RightVector;
	}

	return (CameraForward * RawDirection.X + CameraRight * RawDirection.Y).GetSafeNormal();
}

FVector AJoystickSR04ThirdPersonCharacter::GetRawJoystickDirection() const
{
	if (!Receiver || !Receiver->bIsConnected)
	{
		return FVector::ZeroVector;
	}

	switch (Receiver->JoyDirection)
	{
	case EJoystickDir::Up:        return FVector(1.0f, 0.0f, 0.0f);
	case EJoystickDir::UpRight:   return FVector(1.0f, 1.0f, 0.0f).GetSafeNormal();
	case EJoystickDir::Right:     return FVector(0.0f, 1.0f, 0.0f);
	case EJoystickDir::DownRight: return FVector(-1.0f, 1.0f, 0.0f).GetSafeNormal();
	case EJoystickDir::Down:      return FVector(-1.0f, 0.0f, 0.0f);
	case EJoystickDir::DownLeft:  return FVector(-1.0f, -1.0f, 0.0f).GetSafeNormal();
	case EJoystickDir::Left:      return FVector(0.0f, -1.0f, 0.0f);
	case EJoystickDir::UpLeft:    return FVector(1.0f, -1.0f, 0.0f).GetSafeNormal();
	default:                      return FVector::ZeroVector;
	}
}
