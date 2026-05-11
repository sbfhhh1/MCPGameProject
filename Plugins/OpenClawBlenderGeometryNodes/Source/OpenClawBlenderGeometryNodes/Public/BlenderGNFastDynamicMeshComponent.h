#pragma once

#include "CoreMinimal.h"
#include "Components/MeshComponent.h"
#include "ProceduralMeshComponent.h"
#include "BlenderGNFastDynamicMeshComponent.generated.h"

UCLASS(ClassGroup = (OpenClaw), meta = (BlueprintSpawnableComponent))
class OPENCLAWBLENDERGEOMETRYNODES_API UBlenderGNFastDynamicMeshComponent : public UMeshComponent
{
	GENERATED_BODY()

public:
	UBlenderGNFastDynamicMeshComponent();

	void InitMesh(
		const TArray<FVector>& Vertices,
		const TArray<int32>& Triangles,
		const TArray<FVector>& Normals,
		const TArray<FVector2D>& UVs,
		const TArray<FColor>& Colors,
		const TArray<FProcMeshTangent>& Tangents);

	void UpdatePositionsOnly(const TArray<FVector>& NewPositions);

	int32 GetVertexCount() const { return CachedVertexCount; }

	virtual FPrimitiveSceneProxy* CreateSceneProxy() override;
	virtual FBoxSphereBounds CalcBounds(const FTransform& LocalToWorld) const override;
	virtual int32 GetNumMaterials() const override;
	virtual UMaterialInterface* GetMaterial(int32 ElementIndex) const override;

private:
	TArray<FVector3f> PositionBuffer;
	TArray<FVector3f> NormalBuffer;
	TArray<FVector2f> UVBuffer;
	TArray<FColor> ColorBuffer;
	TArray<uint32> IndexBuffer;
	TArray<FVector3f> TangentXBuffer;
	TArray<FVector4f> TangentZBuffer;
	FBox LocalBounds;
	int32 CachedVertexCount = 0;
};
