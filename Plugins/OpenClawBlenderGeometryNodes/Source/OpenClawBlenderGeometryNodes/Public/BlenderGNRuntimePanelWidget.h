#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "BlenderGNRuntimePanelWidget.generated.h"

class UBlenderGNCageCornerMarkersComponent;
class UBlenderGNIslandBreathMotionComponent;
class UBlenderGNParasiteMotionComponent;
class UBlenderGNWallNoiseMotionComponent;
class UBlenderGeometryNodesComponent;

UCLASS(BlueprintType, Blueprintable)
class OPENCLAWBLENDERGEOMETRYNODES_API UBlenderGNRuntimePanelWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Binding")
	TObjectPtr<UBlenderGeometryNodesComponent> Target;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Binding")
	TObjectPtr<UBlenderGNIslandBreathMotionComponent> IslandMotion;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Binding")
	TObjectPtr<UBlenderGNParasiteMotionComponent> ParasiteMotion;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Binding")
	TObjectPtr<UBlenderGNWallNoiseMotionComponent> WallNoiseMotion;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Binding")
	TObjectPtr<UBlenderGNCageCornerMarkersComponent> CageCornerMarkers;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Runtime")
	bool bLiveMotion = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Runtime")
	bool bLiveBlenderRebuild = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Runtime")
	bool bDriveBlenderAnimation = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Runtime", meta = (ClampMin = "0.02", ClampMax = "1.25"))
	float RebuildDebounceSeconds = 0.12f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Runtime", meta = (ClampMin = "1.0", ClampMax = "60.0"))
	float BlenderFrameRate = 24.0f;

	UPROPERTY(BlueprintReadOnly, Category = "Status")
	bool bRebuildQueued = false;

	UPROPERTY(BlueprintReadOnly, Category = "Status")
	FString RebuildStatusText = TEXT("Blender Rebuild: Manual");

	UPROPERTY(BlueprintReadOnly, Category = "Status")
	FString RuntimeStatusText = TEXT("Idle");

	UFUNCTION(BlueprintCallable, Category = "Runtime")
	void ResolveReferences(AActor* SearchActor);

	UFUNCTION(BlueprintCallable, Category = "Runtime")
	void ApplyRuntimeSettings();

	UFUNCTION(BlueprintCallable, Category = "Runtime")
	void SetLiveMotion(bool bEnabled);

	UFUNCTION(BlueprintCallable, Category = "Runtime")
	void SetLiveBlenderRebuild(bool bEnabled);

	UFUNCTION(BlueprintCallable, Category = "Runtime")
	void QueueBlenderRebuild(bool bForce = true, float DelayOverride = -1.0f);

	UFUNCTION(BlueprintCallable, Category = "Runtime")
	void RefreshNow();

	UFUNCTION(BlueprintCallable, Category = "Geometry Nodes")
	void SetFloatInput(const FString& SocketName, float Value, bool bPreviewParasite = true);

	UFUNCTION(BlueprintCallable, Category = "Geometry Nodes")
	void SetIntInput(const FString& SocketName, int32 Value);

	UFUNCTION(BlueprintCallable, Category = "Geometry Nodes")
	void SetBoolInput(const FString& SocketName, bool bValue);

	UFUNCTION(BlueprintCallable, Category = "Geometry Nodes")
	void SetVectorInput(const FString& SocketName, FVector Value);

	UFUNCTION(BlueprintCallable, Category = "Motion")
	void SetWallNoiseStrength(float Value);

	UFUNCTION(BlueprintCallable, Category = "Motion")
	void SetWallNoiseSpeed(float Value);

	UFUNCTION(BlueprintCallable, Category = "Motion")
	void SetWallNoiseScale(float Value);

	UFUNCTION(BlueprintCallable, Category = "Status")
	void UpdateStatusText();

protected:
	virtual void NativeConstruct() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

private:
	bool bForceQueuedRebuild = false;
	double RebuildAtSeconds = 0.0;

	void PumpQueuedRebuild();
};
