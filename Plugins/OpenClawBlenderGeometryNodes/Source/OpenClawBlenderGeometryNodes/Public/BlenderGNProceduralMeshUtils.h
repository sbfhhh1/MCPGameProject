#pragma once

#include "CoreMinimal.h"

class UBlenderGeometryNodesComponent;
class UProceduralMeshComponent;
struct FBlenderGNMeshData;

namespace BlenderGNProcMesh
{
	UBlenderGeometryNodesComponent* ResolveRuntime(const AActor* Owner, UBlenderGeometryNodesComponent* ExplicitRuntime);
	bool ReadSectionVertices(const UProceduralMeshComponent* Mesh, TArray<FVector>& OutVertices);
	bool ApplyVertices(UBlenderGeometryNodesComponent* Runtime, const TArray<FVector>& Vertices, const TArray<FVector>& Normals);
	void RecalculateNormals(const FBlenderGNMeshData& MeshData, const TArray<FVector>& Vertices, TArray<FVector>& OutNormals);
	TArray<TArray<int32>> BuildPositionGroups(const TArray<FVector>& Vertices, float Quantization);
	void SmoothNormalsByGroups(const TArray<TArray<int32>>& Groups, float SmoothingAngleDegrees, TArray<FVector>& Normals);
	float Hash01(int32 Seed);
	FVector AxisVector(int32 Axis);
	FVector ApplyAxisOffset(FVector Vertex, int32 Axis, float Offset);
	FVector2D AxisSampleCoordinates(const FVector& Vertex, int32 Axis);
}
