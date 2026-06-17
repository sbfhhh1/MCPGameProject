#include "CylinderMatrixNode.h"

#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Curves/CurveFloat.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"

ACylinderMatrixNode::ACylinderMatrixNode()
{
	PrimaryActorTick.bCanEverTick = true;

	Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	RootComponent = Root;

	CylinderMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Cylinder"));
	CylinderMesh->SetupAttachment(Root);
	CylinderMesh->SetRelativeScale3D(FVector(0.5, 0.5, 1.2));
	CylinderMesh->SetRelativeLocation(FVector(0.0, 0.0, 60.0));
	CylinderMesh->SetMobility(EComponentMobility::Movable);

	static ConstructorHelpers::FObjectFinder<UStaticMesh> CylinderAsset(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	if (CylinderAsset.Succeeded())
	{
		CylinderMesh->SetStaticMesh(CylinderAsset.Object);
	}

	static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeAsset(TEXT("/Engine/BasicShapes/Cube.Cube"));
	DirectionShaftMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("DirectionShaft"));
	DirectionShaftMesh->SetupAttachment(Root);
	DirectionShaftMesh->SetRelativeScale3D(FVector(0.28, 0.045, 0.018));
	DirectionShaftMesh->SetRelativeLocation(FVector(0.0, 0.0, 128.0));
	DirectionShaftMesh->SetMobility(EComponentMobility::Movable);
	DirectionShaftMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	if (CubeAsset.Succeeded())
	{
		DirectionShaftMesh->SetStaticMesh(CubeAsset.Object);
	}

	DirectionHeadMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("DirectionHead"));
	DirectionHeadMesh->SetupAttachment(Root);
	DirectionHeadMesh->SetRelativeScale3D(FVector(0.08, 0.15, 0.018));
	DirectionHeadMesh->SetRelativeLocation(FVector(18.0, 0.0, 128.0));
	DirectionHeadMesh->SetMobility(EComponentMobility::Movable);
	DirectionHeadMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	if (CubeAsset.Succeeded())
	{
		DirectionHeadMesh->SetStaticMesh(CubeAsset.Object);
	}

	static ConstructorHelpers::FObjectFinder<UMaterialInterface> DefaultMaterial(TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
	if (DefaultMaterial.Succeeded())
	{
		CylinderMesh->SetMaterial(0, DefaultMaterial.Object);
		DirectionShaftMesh->SetMaterial(0, DefaultMaterial.Object);
		DirectionHeadMesh->SetMaterial(0, DefaultMaterial.Object);
	}
}

void ACylinderMatrixNode::BeginPlay()
{
	Super::BeginPlay();
}

#if WITH_EDITOR
bool ACylinderMatrixNode::ShouldTickIfViewportsOnly() const
{
	return true;
}
#endif

void ACylinderMatrixNode::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);

	if (!IsValid(TargetActor) || MaxDistance <= 0.0)
	{
		return;
	}

	const double Dist = FVector::Dist(GetActorLocation(), TargetActor->GetActorLocation());
	const double NormalizedTime = FMath::Clamp(
		FMath::GetMappedRangeValueClamped(FVector2D(0.0, MaxDistance), FVector2D(0.0, 1.0), Dist),
		0.0,
		1.0);

	const bool bHasCurveKeys = CurveAsset && CurveAsset->FloatCurve.GetNumKeys() > 0;
	const double RawCurveValue = bHasCurveKeys ? CurveAsset->GetFloatValue(static_cast<float>(NormalizedTime)) : EvaluateBellCurve(NormalizedTime);
	const double ContrastedValue = FMath::Pow(FMath::Clamp(RawCurveValue, 0.0, 1.0), PowerExp);
	const double TargetHeight = FMath::GetMappedRangeValueClamped(FVector2D(0.0, 1.0), FVector2D(24.0, 520.0), ContrastedValue);

	CylinderMesh->SetRelativeScale3D(FVector(0.5, 0.5, TargetHeight / 100.0));
	CylinderMesh->SetRelativeLocation(FVector(0.0, 0.0, TargetHeight * 0.5));
	UpdateDirectionMarker(TargetHeight);
}

double ACylinderMatrixNode::EvaluateBellCurve(double NormalizedTime) const
{
	const double ClampedTime = FMath::Clamp(NormalizedTime, 0.0, 1.0);
	const double Triangle = 1.0 - FMath::Abs((ClampedTime * 2.0) - 1.0);
	return FMath::SmoothStep(0.0, 1.0, Triangle);
}

void ACylinderMatrixNode::UpdateDirectionMarker(double CylinderHeight)
{
	if (!IsValid(TargetActor))
	{
		return;
	}

	const FVector ToTarget = TargetActor->GetActorLocation() - GetActorLocation();
	const double YawDegrees = FMath::RadiansToDegrees(FMath::Atan2(ToTarget.Y, ToTarget.X));
	const FRotator DirectionRotation(0.0, YawDegrees, 0.0);
	const FVector MarkerLocation(0.0, 0.0, CylinderHeight + 8.0);

	DirectionShaftMesh->SetRelativeLocation(MarkerLocation);
	DirectionShaftMesh->SetRelativeRotation(DirectionRotation);
	DirectionHeadMesh->SetRelativeLocation(MarkerLocation + DirectionRotation.RotateVector(FVector(18.0, 0.0, 0.0)));
	DirectionHeadMesh->SetRelativeRotation(DirectionRotation);
}
