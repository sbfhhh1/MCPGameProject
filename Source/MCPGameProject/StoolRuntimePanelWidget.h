#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "StoolRuntimePanelWidget.generated.h"

class UBlenderGeometryNodesComponent;
class UTextBlock;
class USlider;

UCLASS(BlueprintType, Blueprintable)
class MCPGAMEPROJECT_API UStoolRuntimePanelWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stool")
	TObjectPtr<UBlenderGeometryNodesComponent> Target;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stool", meta = (ClampMin = "0.02", ClampMax = "2.0"))
	float RebuildDebounceSeconds = 0.12f;

	UFUNCTION(BlueprintCallable, Category = "Stool")
	void SetTarget(UBlenderGeometryNodesComponent* InTarget);

protected:
	virtual TSharedRef<SWidget> RebuildWidget() override;
	virtual void NativeConstruct() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

private:
	UPROPERTY(Transient)
	TArray<TObjectPtr<USlider>> InputSliders;

	UPROPERTY(Transient)
	TArray<TObjectPtr<UTextBlock>> InputValueTexts;

	UPROPERTY(Transient)
	TArray<int32> InputIndices;

	UPROPERTY(Transient)
	TArray<float> LastSliderValues;

	UPROPERTY(Transient)
	TObjectPtr<UTextBlock> StatusTextBlock;

	bool bSynchronizingControls = false;
	bool bRebuildQueued = false;
	double RebuildAtSeconds = 0.0;

	void BuildDefaultPanel();
	void SynchronizeControls();
	void UpdateValueText(int32 ControlIndex);
	void UpdateStatusText();
	void QueueRebuild();
	void PumpQueuedRebuild();

	UFUNCTION()
	void HandleSliderChanged(float Value);
};
