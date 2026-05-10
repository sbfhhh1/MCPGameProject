#include "BlenderGNWallNoiseMotionComponent.h"

#include "BlenderGeometryNodesComponent.h"
#include "BlenderGeometryNodesTypes.h"
#include "BlenderGNProceduralMeshUtils.h"
#include "ProceduralMeshComponent.h"

UBlenderGNWallNoiseMotionComponent::UBlenderGNWallNoiseMotionComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.bStartWithTickEnabled = true;
}

void UBlenderGNWallNoiseMotionComponent::SetLiveMotion(bool bEnabled)
{
	bLiveMotion = bEnabled;
	SetComponentTickEnabled(bLiveMotion);
}

void UBlenderGNWallNoiseMotionComponent::OnRegister()
{
	Super::OnRegister();
	BindRuntime();
}

void UBlenderGNWallNoiseMotionComponent::OnUnregister()
{
	UnbindRuntime();
	Super::OnUnregister();
}

void UBlenderGNWallNoiseMotionComponent::BeginPlay()
{
	Super::BeginPlay();
	BindRuntime();
	RebuildCache();
	SetComponentTickEnabled(bLiveMotion);
}

void UBlenderGNWallNoiseMotionComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
	if (bLiveMotion)
	{
		ApplyMotion(GetWorld() ? GetWorld()->GetTimeSeconds() : 0.0f);
	}
}

void UBlenderGNWallNoiseMotionComponent::HandleMeshUpdated(UProceduralMeshComponent* ProceduralMesh)
{
	RebuildCache();
}

void UBlenderGNWallNoiseMotionComponent::BindRuntime()
{
	UBlenderGeometryNodesComponent* Resolved = BlenderGNProcMesh::ResolveRuntime(GetOwner(), Runtime);
	if (Resolved == BoundRuntime)
	{
		return;
	}

	UnbindRuntime();
	BoundRuntime = Resolved;
	if (BoundRuntime)
	{
		BoundRuntime->OnMeshUpdated.AddUniqueDynamic(this, &UBlenderGNWallNoiseMotionComponent::HandleMeshUpdated);
	}
}

void UBlenderGNWallNoiseMotionComponent::UnbindRuntime()
{
	if (BoundRuntime)
	{
		BoundRuntime->OnMeshUpdated.RemoveDynamic(this, &UBlenderGNWallNoiseMotionComponent::HandleMeshUpdated);
		BoundRuntime = nullptr;
	}
}

void UBlenderGNWallNoiseMotionComponent::RebuildCache()
{
	BindRuntime();
	if (!BoundRuntime)
	{
		return;
	}

	BaseVertices = BoundRuntime->GetLastMeshData().Vertices;
	CachedVertexCount = BaseVertices.Num();
	AnimatedVertices.SetNum(CachedVertexCount);
	NormalGroups = BlenderGNProcMesh::BuildPositionGroups(BaseVertices, PositionMergeQuantization);
	SyncFromRuntimeInputs();
}

void UBlenderGNWallNoiseMotionComponent::SyncFromRuntimeInputs()
{
	if (!BoundRuntime)
	{
		return;
	}

	Strength = FMath::Clamp(BoundRuntime->GetFloatInput(TEXT("Noise Strength"), Strength), 0.0f, 150.0f);
	Speed = FMath::Clamp(BoundRuntime->GetFloatInput(TEXT("Wave Speed"), Speed), -5.0f, 5.0f);
	Scale = FMath::Clamp(BoundRuntime->GetFloatInput(TEXT("Noise Scale"), Scale), 0.1f, 12.0f);
}

void UBlenderGNWallNoiseMotionComponent::ApplyMotion(float WorldTimeSeconds)
{
	BindRuntime();
	if (!BoundRuntime)
	{
		return;
	}

	if (BoundRuntime->GetLastMeshData().Vertices.Num() != CachedVertexCount || BaseVertices.Num() == 0)
	{
		RebuildCache();
	}
	if (BaseVertices.Num() == 0)
	{
		return;
	}

	SyncFromRuntimeInputs();
	const int32 Axis = static_cast<int32>(DisplacementAxis);
	const float T = WorldTimeSeconds * Speed;
	const float Frequency = FMath::Max(0.01f, Scale);
	const float Amplitude = FMath::Max(0.0f, Strength);
	const float ClampedSmoothness = FMath::Clamp(Smoothness, 0.0f, 1.0f);
	for (int32 Index = 0; Index < BaseVertices.Num(); ++Index)
	{
		const FVector V = BaseVertices[Index];
		const FVector2D Sample = BlenderGNProcMesh::AxisSampleCoordinates(V, Axis);
		const float N0 = (FMath::PerlinNoise2D(FVector2D(Sample.X * Frequency + T, Sample.Y * Frequency + T * 0.37f)) + 1.0f) * 0.5f;
		const float N1 = (FMath::PerlinNoise2D(FVector2D(Sample.X * Frequency * 2.03f - T * 0.41f, Sample.Y * Frequency * 2.03f + T * 0.73f)) + 1.0f) * 0.5f;
		float Wave = (N0 * 0.78f + N1 * 0.22f - 0.5f) * 2.0f;
		Wave = FMath::Lerp(Wave, FMath::SmoothStep(-1.0f, 1.0f, Wave), ClampedSmoothness);
		AnimatedVertices[Index] = BlenderGNProcMesh::ApplyAxisOffset(V, Axis, Wave * Amplitude);
	}

	TArray<FVector> Normals;
	if (bRecalculateAnimatedNormals)
	{
		BlenderGNProcMesh::RecalculateNormals(BoundRuntime->GetLastMeshData(), AnimatedVertices, Normals);
		if (bSmoothSplitNormals)
		{
			BlenderGNProcMesh::SmoothNormalsByGroups(NormalGroups, SmoothingAngle, Normals);
		}
	}
	BlenderGNProcMesh::ApplyVertices(BoundRuntime, AnimatedVertices, Normals);
}
