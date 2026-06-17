#include "MatrixTargetSpherePawn.h"

#include "Components/StaticMeshComponent.h"
#include "CylinderMatrixField.h"
#include "Engine/StaticMesh.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "InputCoreTypes.h"
#include "UObject/ConstructorHelpers.h"

AMatrixTargetSpherePawn::AMatrixTargetSpherePawn()
{
	PrimaryActorTick.bCanEverTick = true;
	AutoPossessPlayer = EAutoReceiveInput::Disabled;

	SphereMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Sphere"));
	RootComponent = SphereMesh;
	SphereMesh->SetMobility(EComponentMobility::Movable);
	SphereMesh->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	SphereMesh->SetCollisionObjectType(ECC_Pawn);
	SphereMesh->SetCollisionResponseToAllChannels(ECR_Ignore);
	SphereMesh->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
	SphereMesh->SetGenerateOverlapEvents(false);

	static ConstructorHelpers::FObjectFinder<UStaticMesh> SphereAsset(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	if (SphereAsset.Succeeded())
	{
		SphereMesh->SetStaticMesh(SphereAsset.Object);
	}
}

void AMatrixTargetSpherePawn::BeginPlay()
{
	Super::BeginPlay();
}

void AMatrixTargetSpherePawn::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);

	const FVector2D Input = ReadMovementInput();
	const FVector2D DesiredVelocity = Input * MoveSpeed;
	CurrentVelocity = InputSmoothing <= 0.0
		? DesiredVelocity
		: FMath::Vector2DInterpTo(CurrentVelocity, DesiredVelocity, DeltaTime, InputSmoothing);

	if (CurrentVelocity.IsNearlyZero(0.01))
	{
		return;
	}

	FVector NewLocation = GetActorLocation() + FVector(CurrentVelocity.Y, CurrentVelocity.X, 0.0) * static_cast<double>(DeltaTime);
	if (bClampToMovementBounds)
	{
		NewLocation.X = FMath::Clamp(NewLocation.X, static_cast<double>(MovementBoundsMin.X), static_cast<double>(MovementBoundsMax.X));
		NewLocation.Y = FMath::Clamp(NewLocation.Y, static_cast<double>(MovementBoundsMin.Y), static_cast<double>(MovementBoundsMax.Y));
	}
	SetActorLocation(NewLocation);
	NotifyMatrixFields(DeltaTime);
}

void AMatrixTargetSpherePawn::SetMovementBounds(FVector2D BoundsMin, FVector2D BoundsMax)
{
	MovementBoundsMin = BoundsMin;
	MovementBoundsMax = BoundsMax;
}

FVector2D AMatrixTargetSpherePawn::ReadMovementInput() const
{
	const APlayerController* PlayerController = Cast<APlayerController>(GetController());
	if (!PlayerController && GetWorld())
	{
		PlayerController = GetWorld()->GetFirstPlayerController();
	}
	if (!PlayerController)
	{
		return FVector2D::ZeroVector;
	}

	const double StickX = PlayerController->GetInputAnalogKeyState(EKeys::Gamepad_LeftX);
	const double StickY = PlayerController->GetInputAnalogKeyState(EKeys::Gamepad_LeftY);
	double X = FMath::Abs(StickX) > 0.12 ? StickX : 0.0;
	double Y = FMath::Abs(StickY) > 0.12 ? StickY : 0.0;

	X += PlayerController->IsInputKeyDown(EKeys::D) || PlayerController->IsInputKeyDown(EKeys::Right) ? 1.0 : 0.0;
	X -= PlayerController->IsInputKeyDown(EKeys::A) || PlayerController->IsInputKeyDown(EKeys::Left) ? 1.0 : 0.0;
	Y += PlayerController->IsInputKeyDown(EKeys::W) || PlayerController->IsInputKeyDown(EKeys::Up) ? 1.0 : 0.0;
	Y -= PlayerController->IsInputKeyDown(EKeys::S) || PlayerController->IsInputKeyDown(EKeys::Down) ? 1.0 : 0.0;

	FVector2D Movement(X, Y);
	return Movement.GetSafeNormal();
}

void AMatrixTargetSpherePawn::NotifyMatrixFields(float DeltaTime) const
{
	if (!bNotifyMatrixFieldsOnMove || !GetWorld())
	{
		return;
	}

	for (TActorIterator<ACylinderMatrixField> It(GetWorld()); It; ++It)
	{
		ACylinderMatrixField* Field = *It;
		if (IsValid(Field))
		{
			Field->RefreshMatrixFieldDelta(DeltaTime, false);
		}
	}
}
