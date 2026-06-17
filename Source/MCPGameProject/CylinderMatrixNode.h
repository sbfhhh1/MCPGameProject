#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "CylinderMatrixNode.generated.h"

class UCurveFloat;
class USceneComponent;
class UStaticMeshComponent;

UCLASS()
class MCPGAMEPROJECT_API ACylinderMatrixNode : public AActor
{
	GENERATED_BODY()

public:
	ACylinderMatrixNode();

	virtual void Tick(float DeltaTime) override;

#if WITH_EDITOR
	virtual bool ShouldTickIfViewportsOnly() const override;
#endif

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<USceneComponent> Root;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UStaticMeshComponent> CylinderMesh;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UStaticMeshComponent> DirectionShaftMesh;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UStaticMeshComponent> DirectionHeadMesh;

	UPROPERTY(EditAnywhere, Category = "Matrix Settings")
	TObjectPtr<UCurveFloat> CurveAsset;

	UPROPERTY(EditInstanceOnly, Category = "Matrix Settings")
	TObjectPtr<AActor> TargetActor;

	UPROPERTY(EditAnywhere, Category = "Matrix Settings", meta = (ClampMin = "1.0"))
	double MaxDistance = 500.0;

	UPROPERTY(EditAnywhere, Category = "Matrix Settings", meta = (ClampMin = "0.01"))
	double PowerExp = 2.0;

protected:
	virtual void BeginPlay() override;

private:
	double EvaluateBellCurve(double NormalizedTime) const;

	void UpdateDirectionMarker(double CylinderHeight);
};
