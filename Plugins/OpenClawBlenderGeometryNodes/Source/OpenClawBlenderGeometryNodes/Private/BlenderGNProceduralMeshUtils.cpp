#include "BlenderGNProceduralMeshUtils.h"

#include "BlenderGeometryNodesComponent.h"
#include "BlenderGeometryNodesTypes.h"
#include "ProceduralMeshComponent.h"

namespace
{
	FIntVector QuantizePosition(const FVector& Value, float Quantization)
	{
		const float SafeQuantization = FMath::Max(1.0f, Quantization);
		return FIntVector(
			FMath::RoundToInt(Value.X * SafeQuantization),
			FMath::RoundToInt(Value.Y * SafeQuantization),
			FMath::RoundToInt(Value.Z * SafeQuantization));
	}
}

UBlenderGeometryNodesComponent* BlenderGNProcMesh::ResolveRuntime(const AActor* Owner, UBlenderGeometryNodesComponent* ExplicitRuntime)
{
	if (IsValid(ExplicitRuntime))
	{
		return ExplicitRuntime;
	}
	return Owner ? Owner->FindComponentByClass<UBlenderGeometryNodesComponent>() : nullptr;
}

bool BlenderGNProcMesh::ReadSectionVertices(const UProceduralMeshComponent* Mesh, TArray<FVector>& OutVertices)
{
	OutVertices.Reset();
	if (!Mesh)
	{
		return false;
	}

	const FProcMeshSection* Section = const_cast<UProceduralMeshComponent*>(Mesh)->GetProcMeshSection(0);
	if (!Section || Section->ProcVertexBuffer.Num() == 0)
	{
		return false;
	}

	OutVertices.Reserve(Section->ProcVertexBuffer.Num());
	for (const FProcMeshVertex& Vertex : Section->ProcVertexBuffer)
	{
		OutVertices.Add(Vertex.Position);
	}
	return true;
}

bool BlenderGNProcMesh::ApplyVertices(UBlenderGeometryNodesComponent* Runtime, const TArray<FVector>& Vertices, const TArray<FVector>& Normals)
{
	if (!Runtime)
	{
		return false;
	}

	UProceduralMeshComponent* Mesh = Runtime->GetProceduralMesh();
	const FBlenderGNMeshData& MeshData = Runtime->GetLastMeshData();
	if (!Mesh || Vertices.Num() == 0 || MeshData.Sections.Num() == 0)
	{
		return false;
	}

	const TArray<FVector>& SafeNormals = Normals.Num() == Vertices.Num() ? Normals : MeshData.Normals;
	TArray<FLinearColor> VertexColors;
	TArray<FProcMeshTangent> Tangents;
	for (int32 SectionIndex = 0; SectionIndex < MeshData.Sections.Num(); ++SectionIndex)
	{
		Mesh->UpdateMeshSection_LinearColor(
			SectionIndex,
			Vertices,
			SafeNormals.Num() == Vertices.Num() ? SafeNormals : TArray<FVector>(),
			MeshData.UVs,
			VertexColors,
			Tangents);
	}
	return true;
}

void BlenderGNProcMesh::RecalculateNormals(const FBlenderGNMeshData& MeshData, const TArray<FVector>& Vertices, TArray<FVector>& OutNormals)
{
	OutNormals.SetNumZeroed(Vertices.Num());
	for (const FBlenderGNMeshSection& Section : MeshData.Sections)
	{
		for (int32 Index = 0; Index + 2 < Section.Triangles.Num(); Index += 3)
		{
			const int32 A = Section.Triangles[Index];
			const int32 B = Section.Triangles[Index + 1];
			const int32 C = Section.Triangles[Index + 2];
			if (!Vertices.IsValidIndex(A) || !Vertices.IsValidIndex(B) || !Vertices.IsValidIndex(C))
			{
				continue;
			}

			const FVector Normal = FVector::CrossProduct(Vertices[B] - Vertices[A], Vertices[C] - Vertices[A]).GetSafeNormal();
			OutNormals[A] += Normal;
			OutNormals[B] += Normal;
			OutNormals[C] += Normal;
		}
	}

	for (FVector& Normal : OutNormals)
	{
		Normal = Normal.IsNearlyZero() ? FVector::UpVector : Normal.GetSafeNormal();
	}
}

TArray<TArray<int32>> BlenderGNProcMesh::BuildPositionGroups(const TArray<FVector>& Vertices, float Quantization)
{
	TMap<FIntVector, TArray<int32>> Buckets;
	Buckets.Reserve(Vertices.Num());
	for (int32 Index = 0; Index < Vertices.Num(); ++Index)
	{
		Buckets.FindOrAdd(QuantizePosition(Vertices[Index], Quantization)).Add(Index);
	}

	TArray<TArray<int32>> Groups;
	for (TPair<FIntVector, TArray<int32>>& Pair : Buckets)
	{
		if (Pair.Value.Num() > 1)
		{
			Groups.Add(MoveTemp(Pair.Value));
		}
	}
	return Groups;
}

void BlenderGNProcMesh::SmoothNormalsByGroups(const TArray<TArray<int32>>& Groups, float SmoothingAngleDegrees, TArray<FVector>& Normals)
{
	if (SmoothingAngleDegrees <= 0.0f || Normals.Num() == 0)
	{
		return;
	}

	const float DotThreshold = FMath::Cos(FMath::DegreesToRadians(SmoothingAngleDegrees));
	TArray<FVector> Smoothed = Normals;
	for (const TArray<int32>& Group : Groups)
	{
		for (int32 VertexIndex : Group)
		{
			if (!Normals.IsValidIndex(VertexIndex))
			{
				continue;
			}

			FVector Sum = FVector::ZeroVector;
			for (int32 OtherIndex : Group)
			{
				if (Normals.IsValidIndex(OtherIndex) && FVector::DotProduct(Normals[VertexIndex], Normals[OtherIndex]) >= DotThreshold)
				{
					Sum += Normals[OtherIndex];
				}
			}
			if (!Sum.IsNearlyZero())
			{
				Smoothed[VertexIndex] = Sum.GetSafeNormal();
			}
		}
	}
	Normals = MoveTemp(Smoothed);
}

float BlenderGNProcMesh::Hash01(int32 Seed)
{
	uint32 X = static_cast<uint32>(Seed);
	X ^= X >> 16;
	X *= 0x7feb352d;
	X ^= X >> 15;
	X *= 0x846ca68b;
	X ^= X >> 16;
	return static_cast<float>(X & 0x00FFFFFF) / 16777215.0f;
}

FVector BlenderGNProcMesh::AxisVector(int32 Axis)
{
	switch (Axis)
	{
	case 0:
		return FVector::XAxisVector;
	case 1:
		return FVector::YAxisVector;
	default:
		return FVector::ZAxisVector;
	}
}

FVector BlenderGNProcMesh::ApplyAxisOffset(FVector Vertex, int32 Axis, float Offset)
{
	Vertex += AxisVector(Axis) * Offset;
	return Vertex;
}

FVector2D BlenderGNProcMesh::AxisSampleCoordinates(const FVector& Vertex, int32 Axis)
{
	switch (Axis)
	{
	case 0:
		return FVector2D(Vertex.Y, Vertex.Z);
	case 1:
		return FVector2D(Vertex.X, Vertex.Z);
	default:
		return FVector2D(Vertex.X, Vertex.Y);
	}
}
