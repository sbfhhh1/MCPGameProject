#include "CylinderMatrixField.h"

#include "Components/InstancedStaticMeshComponent.h"
#include "Components/SceneComponent.h"
#include "Curves/CurveFloat.h"
#include "Engine/StaticMesh.h"
#include "EngineUtils.h"
#include "MatrixTargetSpherePawn.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"

ACylinderMatrixField::ACylinderMatrixField()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.bStartWithTickEnabled = true;

	Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	RootComponent = Root;

	CylinderInstances = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("CylinderInstances"));
	CylinderInstances->SetupAttachment(Root);
	CylinderInstances->SetMobility(EComponentMobility::Movable);

	DirectionShaftInstances = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("DirectionShaftInstances"));
	DirectionShaftInstances->SetupAttachment(Root);
	DirectionShaftInstances->SetMobility(EComponentMobility::Movable);
	DirectionShaftInstances->SetCollisionEnabled(ECollisionEnabled::NoCollision);

	DirectionHeadInstances = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("DirectionHeadInstances"));
	DirectionHeadInstances->SetupAttachment(Root);
	DirectionHeadInstances->SetMobility(EComponentMobility::Movable);
	DirectionHeadInstances->SetCollisionEnabled(ECollisionEnabled::NoCollision);

	static ConstructorHelpers::FObjectFinder<UStaticMesh> CylinderAsset(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	if (CylinderAsset.Succeeded())
	{
		CylinderInstances->SetStaticMesh(CylinderAsset.Object);
	}

	static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeAsset(TEXT("/Engine/BasicShapes/Cube.Cube"));
	if (CubeAsset.Succeeded())
	{
		DirectionShaftInstances->SetStaticMesh(CubeAsset.Object);
		DirectionHeadInstances->SetStaticMesh(CubeAsset.Object);
	}

	static ConstructorHelpers::FObjectFinder<UMaterialInterface> DefaultMaterial(TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
	if (DefaultMaterial.Succeeded())
	{
		CylinderInstances->SetMaterial(0, DefaultMaterial.Object);
		DirectionShaftInstances->SetMaterial(0, DefaultMaterial.Object);
		DirectionHeadInstances->SetMaterial(0, DefaultMaterial.Object);
	}
}

void ACylinderMatrixField::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);
	RebuildMatrix();
}

void ACylinderMatrixField::BeginPlay()
{
	Super::BeginPlay();
	SetActorTickEnabled(true);
	ResolveTargetActor();
	RebuildMatrix();

	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().SetTimer(
			RuntimeUpdateTimerHandle,
			this,
			&ACylinderMatrixField::HandleRuntimeUpdate,
			FMath::Max(0.01, RuntimeUpdateInterval),
			true);
	}
}

void ACylinderMatrixField::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().ClearTimer(RuntimeUpdateTimerHandle);
	}

	Super::EndPlay(EndPlayReason);
}

#if WITH_EDITOR
bool ACylinderMatrixField::ShouldTickIfViewportsOnly() const
{
	return true;
}
#endif

void ACylinderMatrixField::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);
	UpdateInstanceTransforms(DeltaTime, false);
}

void ACylinderMatrixField::RebuildMatrix()
{
	Columns = FMath::Max(1, Columns);
	Rows = FMath::Max(1, Rows);
	Spacing = FMath::Max(1.0, Spacing);
	CylinderRadius = FMath::Max(1.0, CylinderRadius);
	PlaneHeight = FMath::Max(1.0, PlaneHeight);
	RestHeight = FMath::Max(PlaneHeight, RestHeight);
	FalloffRadius = FMath::Max(1.0, FalloffRadius);

	CylinderInstances->ClearInstances();
	DirectionShaftInstances->ClearInstances();
	DirectionHeadInstances->ClearInstances();
	InstancePositions.Reset(Columns * Rows);
	CurrentHeights.Reset(Columns * Rows);

	const double OffsetX = (Columns - 1) * Spacing * 0.5;
	const double OffsetY = (Rows - 1) * Spacing * 0.5;

	for (int32 Row = 0; Row < Rows; ++Row)
	{
		for (int32 Column = 0; Column < Columns; ++Column)
		{
			const FVector LocalPosition((Column * Spacing) - OffsetX, (Row * Spacing) - OffsetY, 0.0);
			InstancePositions.Add(LocalPosition);
			CurrentHeights.Add(RestHeight);

			CylinderInstances->AddInstance(FTransform::Identity);
			DirectionShaftInstances->AddInstance(FTransform::Identity);
			DirectionHeadInstances->AddInstance(FTransform::Identity);
		}
	}

	ApplyTargetBounds();
	UpdateInstanceTransforms(0.0f, true);
}

void ACylinderMatrixField::RefreshMatrixField(bool bSnapToTarget)
{
	ResolveTargetActor();
	ApplyTargetBounds();
	UpdateInstanceTransforms(0.0f, bSnapToTarget);
}

void ACylinderMatrixField::RefreshMatrixFieldDelta(float DeltaTime, bool bSnapToTarget)
{
	ResolveTargetActor();
	ApplyTargetBounds();
	UpdateInstanceTransforms(DeltaTime, bSnapToTarget);
}

void ACylinderMatrixField::HandleRuntimeUpdate()
{
	RefreshMatrixFieldDelta(static_cast<float>(FMath::Max(0.01, RuntimeUpdateInterval)), false);
}

double ACylinderMatrixField::EvaluateFalloff(double NormalizedDistance) const
{
	const double ClampedDistance = FMath::Clamp(NormalizedDistance, 0.0, 1.0);
	const bool bHasCurveKeys = FalloffCurve && FalloffCurve->FloatCurve.GetNumKeys() > 0;
	const double CurveValue = bHasCurveKeys ? FalloffCurve->GetFloatValue(static_cast<float>(ClampedDistance)) : FMath::SmoothStep(0.0, 1.0, ClampedDistance);
	return FMath::Pow(FMath::Clamp(CurveValue, 0.0, 1.0), FalloffPower);
}

AActor* ACylinderMatrixField::ResolveTargetActor()
{
	if (IsValid(TargetActor) && TargetActor->GetWorld() == GetWorld())
	{
		return TargetActor;
	}

	TargetActor = nullptr;

	if (!bAutoFindTargetActor || !GetWorld())
	{
		return nullptr;
	}

	if (!TargetTag.IsNone())
	{
		for (TActorIterator<AActor> It(GetWorld()); It; ++It)
		{
			AActor* Candidate = *It;
			if (IsValid(Candidate) && Candidate->ActorHasTag(TargetTag))
			{
				TargetActor = Candidate;
				return TargetActor;
			}
		}
	}

	for (TActorIterator<AMatrixTargetSpherePawn> It(GetWorld()); It; ++It)
	{
		AMatrixTargetSpherePawn* Candidate = *It;
		if (IsValid(Candidate))
		{
			TargetActor = Candidate;
			return TargetActor;
		}
	}

	return nullptr;
}

double ACylinderMatrixField::ComputeHeightForPosition(const FVector& LocalPosition, const AActor* ActiveTarget) const
{
	if (!IsValid(ActiveTarget))
	{
		return RestHeight;
	}

	const FVector TargetLocal = GetActorTransform().InverseTransformPosition(ActiveTarget->GetActorLocation());
	const double Distance2D = FVector::Dist2D(LocalPosition, TargetLocal);
	const double NormalizedDistance = Distance2D / FalloffRadius;
	const double Alpha = EvaluateFalloff(NormalizedDistance);
	return FMath::Lerp(PlaneHeight, RestHeight, Alpha);
}

void ACylinderMatrixField::ApplyTargetBounds()
{
	AMatrixTargetSpherePawn* TargetSphere = Cast<AMatrixTargetSpherePawn>(ResolveTargetActor());
	if (!bApplyBoundsToTarget || !IsValid(TargetSphere))
	{
		return;
	}

	const double HalfX = FMath::Max(0.0, (Columns - 1) * Spacing * 0.5 - TargetBoundsPadding);
	const double HalfY = FMath::Max(0.0, (Rows - 1) * Spacing * 0.5 - TargetBoundsPadding);
	const FVector Origin = GetActorLocation();
	TargetSphere->SetMovementBounds(
		FVector2D(Origin.X - HalfX, Origin.Y - HalfY),
		FVector2D(Origin.X + HalfX, Origin.Y + HalfY));
}

void ACylinderMatrixField::UpdateInstanceTransforms(float DeltaTime, bool bSnap)
{
	const int32 InstanceCount = InstancePositions.Num();
	if (InstanceCount == 0 || CylinderInstances->GetInstanceCount() != InstanceCount)
	{
		return;
	}

	AActor* ActiveTarget = ResolveTargetActor();
	const double CylinderScaleXY = CylinderRadius / 50.0;
	const double ShaftScaleX = MarkerLength / 100.0;
	const double ShaftScaleY = MarkerWidth / 100.0;
	const double MarkerScaleZ = 1.8 / 100.0;
	const double HeadScaleX = MarkerHeadLength / 100.0;
	const double HeadScaleY = MarkerHeadWidth / 100.0;
	const double InterpSpeed = FMath::Max(0.0, HeightInterpSpeed);

	for (int32 Index = 0; Index < InstanceCount; ++Index)
	{
		const double DesiredHeight = ComputeHeightForPosition(InstancePositions[Index], ActiveTarget);
		double& CurrentHeight = CurrentHeights[Index];
		CurrentHeight = bSnap || InterpSpeed <= 0.0
			? DesiredHeight
			: FMath::FInterpTo(CurrentHeight, DesiredHeight, DeltaTime, InterpSpeed);

		const FVector CylinderLocation = InstancePositions[Index] + FVector(0.0, 0.0, CurrentHeight * 0.5);
		const FVector CylinderScale(CylinderScaleXY, CylinderScaleXY, CurrentHeight / 100.0);
		const bool bLastCylinder = Index == InstanceCount - 1;
		CylinderInstances->UpdateInstanceTransform(Index, FTransform(FRotator::ZeroRotator, CylinderLocation, CylinderScale), false, bLastCylinder, true);

		const bool bUpdateMarkerRenderState = Index == InstanceCount - 1;
		if (!bShowDirectionMarkers || !IsValid(ActiveTarget))
		{
			const FTransform HiddenTransform(FRotator::ZeroRotator, InstancePositions[Index], FVector::ZeroVector);
			DirectionShaftInstances->UpdateInstanceTransform(Index, HiddenTransform, false, bUpdateMarkerRenderState, true);
			DirectionHeadInstances->UpdateInstanceTransform(Index, HiddenTransform, false, bUpdateMarkerRenderState, true);
			continue;
		}

		const FVector TargetLocal = GetActorTransform().InverseTransformPosition(ActiveTarget->GetActorLocation());
		const FVector ToTarget = TargetLocal - InstancePositions[Index];
		const double YawDegrees = FMath::RadiansToDegrees(FMath::Atan2(ToTarget.Y, ToTarget.X));
		const FRotator MarkerRotation(0.0, YawDegrees, 0.0);
		const FVector MarkerLocation = InstancePositions[Index] + FVector(0.0, 0.0, CurrentHeight + MarkerLift);
		const FVector HeadLocation = MarkerLocation + MarkerRotation.RotateVector(FVector(MarkerLength * 0.65, 0.0, 0.0));

		DirectionShaftInstances->UpdateInstanceTransform(
			Index,
			FTransform(MarkerRotation, MarkerLocation, FVector(ShaftScaleX, ShaftScaleY, MarkerScaleZ)),
			false,
			bUpdateMarkerRenderState,
			true);

		DirectionHeadInstances->UpdateInstanceTransform(
			Index,
			FTransform(MarkerRotation, HeadLocation, FVector(HeadScaleX, HeadScaleY, MarkerScaleZ)),
			false,
			bUpdateMarkerRenderState,
			true);
	}
}
