#pragma once

#include "CoreMinimal.h"
#include "TimerManager.h"
#include "GameFramework/Actor.h"
#include "CylinderMatrixField.generated.h"

class AActor;
class UCurveFloat;
class UInstancedStaticMeshComponent;
class USceneComponent;
class UStaticMesh;

UCLASS(Blueprintable)
class MCPGAMEPROJECT_API ACylinderMatrixField : public AActor
{
	GENERATED_BODY()

public:
	ACylinderMatrixField();

	virtual void OnConstruction(const FTransform& Transform) override;
	virtual void Tick(float DeltaTime) override;

#if WITH_EDITOR
	virtual bool ShouldTickIfViewportsOnly() const override;
#endif

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<USceneComponent> Root;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UInstancedStaticMeshComponent> CylinderInstances;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UInstancedStaticMeshComponent> DirectionShaftInstances;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UInstancedStaticMeshComponent> DirectionHeadInstances;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Matrix|Layout", meta = (ClampMin = "1", UIMin = "1"))
	int32 Columns = 11;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Matrix|Layout", meta = (ClampMin = "1", UIMin = "1"))
	int32 Rows = 11;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Matrix|Layout", meta = (ClampMin = "1.0", UIMin = "10.0"))
	double Spacing = 130.0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Matrix|Shape", meta = (ClampMin = "1.0", UIMin = "5.0"))
	double CylinderRadius = 25.0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Matrix|Shape", meta = (ClampMin = "1.0", UIMin = "1.0"))
	double PlaneHeight = 12.0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Matrix|Shape", meta = (ClampMin = "1.0", UIMin = "50.0"))
	double RestHeight = 100.0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Matrix|Distance Field", meta = (ClampMin = "1.0", UIMin = "50.0"))
	double FalloffRadius = 500.0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Matrix|Distance Field", meta = (ClampMin = "0.01", UIMin = "0.1"))
	double FalloffPower = 1.0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Matrix|Distance Field")
	TObjectPtr<UCurveFloat> FalloffCurve;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Matrix|Motion", meta = (ClampMin = "0.0", UIMin = "0.0"))
	double HeightInterpSpeed = 8.0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Matrix|Motion", meta = (ClampMin = "0.01", UIMin = "0.01"))
	double RuntimeUpdateInterval = 0.016;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Matrix|Target")
	TObjectPtr<AActor> TargetActor;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Matrix|Target")
	FName TargetTag = TEXT("Matrix_TargetSphere");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Matrix|Target")
	bool bAutoFindTargetActor = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Matrix|Target")
	bool bApplyBoundsToTarget = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Matrix|Target", meta = (ClampMin = "0.0", UIMin = "0.0"))
	double TargetBoundsPadding = 40.0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Matrix|Direction Markers")
	bool bShowDirectionMarkers = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Matrix|Direction Markers", meta = (ClampMin = "0.1", UIMin = "1.0"))
	double MarkerLift = 8.0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Matrix|Direction Markers", meta = (ClampMin = "0.1", UIMin = "1.0"))
	double MarkerLength = 28.0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Matrix|Direction Markers", meta = (ClampMin = "0.1", UIMin = "1.0"))
	double MarkerWidth = 4.5;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Matrix|Direction Markers", meta = (ClampMin = "0.1", UIMin = "1.0"))
	double MarkerHeadLength = 8.0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Matrix|Direction Markers", meta = (ClampMin = "0.1", UIMin = "1.0"))
	double MarkerHeadWidth = 15.0;

	UFUNCTION(BlueprintCallable, CallInEditor, Category = "Matrix")
	void RebuildMatrix();

	UFUNCTION(BlueprintCallable, CallInEditor, Category = "Matrix")
	void RefreshMatrixField(bool bSnapToTarget = true);

	UFUNCTION(BlueprintCallable, Category = "Matrix")
	void RefreshMatrixFieldDelta(float DeltaTime, bool bSnapToTarget = false);

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

private:
	UPROPERTY(Transient)
	TArray<FVector> InstancePositions;

	UPROPERTY(Transient)
	TArray<double> CurrentHeights;

	FTimerHandle RuntimeUpdateTimerHandle;

	void HandleRuntimeUpdate();
	double EvaluateFalloff(double NormalizedDistance) const;
	AActor* ResolveTargetActor();
	double ComputeHeightForPosition(const FVector& LocalPosition, const AActor* ActiveTarget) const;
	void ApplyTargetBounds();
	void UpdateInstanceTransforms(float DeltaTime, bool bSnap);
};
