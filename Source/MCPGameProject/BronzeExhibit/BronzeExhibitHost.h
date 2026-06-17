#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "BronzeExhibitTypes.h"
#include "BronzeExhibitHost.generated.h"

class ABronzeArtifactStage;
class UBronzeExhibitWidget;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FBronzeExhibitStateChanged, EBronzeExhibitState, NewState);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FBronzeExhibitPageChanged, int32, ChapterIndex, int32, PageIndex);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FBronzeTobiiSimulationChanged, bool, bEnabled);

UCLASS(BlueprintType, Blueprintable)
class MCPGAMEPROJECT_API ABronzeExhibitHost : public AActor
{
	GENERATED_BODY()

public:
	ABronzeExhibitHost();

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	UFUNCTION(BlueprintCallable, Category = "Bronze Exhibit|Navigation")
	void NextPage();

	UFUNCTION(BlueprintCallable, Category = "Bronze Exhibit|Navigation")
	void PreviousPage();

	UFUNCTION(BlueprintCallable, Category = "Bronze Exhibit|Navigation")
	bool SelectChapter(int32 ChapterIndex);

	UFUNCTION(BlueprintCallable, Category = "Bronze Exhibit|Navigation")
	bool SelectPage(int32 ChapterIndex, int32 PageIndex);

	UFUNCTION(BlueprintCallable, Category = "Bronze Exhibit|Navigation")
	bool SelectGlobalPage(int32 GlobalPageIndex);

	UFUNCTION(BlueprintCallable, Category = "Bronze Exhibit|Playback")
	void StartAutoPlay();

	UFUNCTION(BlueprintCallable, Category = "Bronze Exhibit|Playback")
	void PauseAutoPlay();

	UFUNCTION(BlueprintCallable, Category = "Bronze Exhibit|Playback")
	void ToggleAutoPlay();

	UFUNCTION(BlueprintCallable, Category = "Bronze Exhibit|Tobii")
	void ToggleTobiiSimulation();

	UFUNCTION(BlueprintCallable, Category = "Bronze Exhibit|Tobii")
	bool SetTobiiSimulationEnabled(bool bEnabled);

	UFUNCTION(BlueprintPure, Category = "Bronze Exhibit|Tobii")
	bool IsTobiiSimulationEnabled() const;

	UFUNCTION(BlueprintCallable, Category = "Bronze Exhibit|Widget")
	void RefreshWidget();

	UFUNCTION(BlueprintPure, Category = "Bronze Exhibit|Data")
	bool GetCurrentChapter(FBronzeExhibitChapterRecord& OutChapter) const;

	UFUNCTION(BlueprintPure, Category = "Bronze Exhibit|Data")
	bool GetCurrentPage(FBronzeExhibitPageRecord& OutPage) const;

	UFUNCTION(BlueprintPure, Category = "Bronze Exhibit|Data")
	int32 GetTotalPageCount() const;

	UFUNCTION(BlueprintPure, Category = "Bronze Exhibit|Data")
	int32 GetCurrentGlobalPageIndex() const;

	UFUNCTION(BlueprintPure, Category = "Bronze Exhibit|Playback")
	float GetPageProgress() const;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bronze Exhibit|Data")
	TArray<FBronzeExhibitChapterRecord> Chapters;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bronze Exhibit|Stage")
	TObjectPtr<ABronzeArtifactStage> ArtifactStage;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bronze Exhibit|Stage")
	FName ArtifactStageTag = TEXT("BronzeArtifactStage");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bronze Exhibit|Stage")
	bool bSpawnStageIfMissing = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bronze Exhibit|Widget")
	TSubclassOf<UBronzeExhibitWidget> WidgetClass;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bronze Exhibit|Widget")
	int32 WidgetZOrder = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bronze Exhibit|Playback")
	bool bAutoPlayAtStart = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bronze Exhibit|Playback")
	bool bLoopAutoPlay = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bronze Exhibit|Playback")
	bool bPauseAutoPlayOnManualNavigation = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bronze Exhibit|Playback", meta = (ClampMin = "1.0"))
	float DefaultAutoAdvanceSeconds = 12.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bronze Exhibit|Tobii")
	bool bEnableTobiiSimulationAtStart = false;

	UPROPERTY(BlueprintReadOnly, Category = "Bronze Exhibit|State")
	EBronzeExhibitState State = EBronzeExhibitState::Initializing;

	UPROPERTY(BlueprintReadOnly, Category = "Bronze Exhibit|State")
	int32 CurrentChapterIndex = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Bronze Exhibit|State")
	int32 CurrentPageIndex = 0;

	UPROPERTY(BlueprintAssignable, Category = "Bronze Exhibit|Events")
	FBronzeExhibitStateChanged OnStateChanged;

	UPROPERTY(BlueprintAssignable, Category = "Bronze Exhibit|Events")
	FBronzeExhibitPageChanged OnPageChanged;

	UPROPERTY(BlueprintAssignable, Category = "Bronze Exhibit|Events")
	FBronzeTobiiSimulationChanged OnTobiiSimulationChanged;

private:
	UPROPERTY(Transient)
	TObjectPtr<UBronzeExhibitWidget> RuntimeWidget;

	float CurrentPageElapsedSeconds = 0.0f;
	bool bLastTobiiSimulationState = false;

	void BuildDefaultChapters();
	void ResolveOrSpawnStage();
	void CreateRuntimeWidget();
	void ConfigureRuntimeWidget();
	void UpdateWidgetGaze();
	void ApplyCurrentPage(bool bNotifyWidget);
	void SetState(EBronzeExhibitState NewState);
	void AdvancePage(bool bForward, bool bManualNavigation);
	float GetCurrentPageDuration() const;
	UObject* ResolveTobiiSubsystem() const;
	bool CallBoolFunction(UObject* Target, FName FunctionName, bool bArgument, bool& OutReturnValue) const;
	bool CallBoolGetter(UObject* Target, FName FunctionName, bool& OutReturnValue) const;
	void CallWidgetFunction(FName FunctionName, void* Parameters = nullptr);

	UFUNCTION()
	void HandleWidgetPageChanged(int32 GlobalPageIndex);

	UFUNCTION()
	void HandleWidgetNavigationRequested(FName NavigationId);
};
