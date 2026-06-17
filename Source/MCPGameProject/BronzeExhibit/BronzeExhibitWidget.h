#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "BronzeExhibitWidget.generated.h"

class UBorder;
class UCanvasPanel;
class UImage;
class UProgressBar;
class UTextBlock;
class UTexture2D;
class UWidget;
class UFont;
class ABronzeExhibitHost;

USTRUCT(BlueprintType)
struct MCPGAMEPROJECT_API FBronzeExhibitPage
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bronze Exhibit")
	FText Eyebrow;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bronze Exhibit")
	FText Title;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bronze Exhibit")
	FText Body;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bronze Exhibit")
	FText ArchiveCode;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FBronzeExhibitWidgetPageChanged, int32, PageIndex);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FBronzeExhibitNavigationRequested, FName, NavigationId);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FBronzeExhibitPreviewChanged, FName, TargetId, bool, bVisible);

UCLASS(BlueprintType, Blueprintable)
class MCPGAMEPROJECT_API UBronzeExhibitWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	UPROPERTY(BlueprintAssignable, Category = "Bronze Exhibit|Events")
	FBronzeExhibitWidgetPageChanged OnPageChanged;

	UPROPERTY(BlueprintAssignable, Category = "Bronze Exhibit|Events")
	FBronzeExhibitNavigationRequested OnNavigationRequested;

	UPROPERTY(BlueprintAssignable, Category = "Bronze Exhibit|Events")
	FBronzeExhibitPreviewChanged OnPreviewChanged;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bronze Exhibit|Eye Tracking", meta = (ClampMin = "0.0"))
	float MousePrioritySeconds = 2.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bronze Exhibit|Eye Tracking", meta = (ClampMin = "0.0"))
	float GazeHighlightSeconds = 0.25f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bronze Exhibit|Eye Tracking", meta = (ClampMin = "0.0"))
	float GazePreviewSeconds = 0.8f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bronze Exhibit|Eye Tracking", meta = (ClampMin = "0.1"))
	float GazeActivationSeconds = 1.5f;

	UFUNCTION(BlueprintCallable, Category = "Bronze Exhibit")
	void SetPages(const TArray<FBronzeExhibitPage>& InPages, int32 InitialPage = 0);

	UFUNCTION(BlueprintCallable, Category = "Bronze Exhibit")
	void SetNavigationItems(const TArray<FText>& Labels, const TArray<FName>& Ids);

	UFUNCTION(BlueprintCallable, Category = "Bronze Exhibit|Host")
	void SetExhibitHost(ABronzeExhibitHost* InHost);

	UFUNCTION(BlueprintCallable, Category = "Bronze Exhibit|Host")
	void HandleExhibitPageChanged();

	UFUNCTION(BlueprintCallable, Category = "Bronze Exhibit|Host")
	void HandleExhibitStateChanged();

	UFUNCTION(BlueprintCallable, Category = "Bronze Exhibit|Host")
	void HandleTobiiSimulationChanged();

	UFUNCTION(BlueprintCallable, Category = "Bronze Exhibit")
	void SetPage(int32 PageIndex, bool bNotifyHost = true);

	UFUNCTION(BlueprintCallable, Category = "Bronze Exhibit")
	void ShowNextPage();

	UFUNCTION(BlueprintCallable, Category = "Bronze Exhibit")
	void ShowPreviousPage();

	/**
	 * Host-facing Tobii adapter. Pass FTobiiGazeSample::DisplayPoint and bValid.
	 * Tobii's normalized Y axis is bottom-to-top, so bTobiiBottomUpY defaults true.
	 */
	UFUNCTION(BlueprintCallable, Category = "Bronze Exhibit|Eye Tracking")
	void SubmitTobiiGazeNormalized(FVector2D NormalizedDisplayPoint, bool bValid, bool bTobiiBottomUpY = true);

	UFUNCTION(BlueprintCallable, Category = "Bronze Exhibit|Eye Tracking")
	void ClearTobiiGaze();

	UFUNCTION(BlueprintPure, Category = "Bronze Exhibit")
	int32 GetCurrentPage() const { return CurrentPage; }

protected:
	virtual TSharedRef<SWidget> RebuildWidget() override;
	virtual void NativeConstruct() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;
	virtual FReply NativeOnPreviewMouseButtonDown(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent) override;
	virtual FReply NativeOnMouseMove(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent) override;
	virtual void NativeOnMouseLeave(const FPointerEvent& InMouseEvent) override;

private:
	enum class EInteractionType : uint8
	{
		Navigation,
		PreviousPage,
		NextPage
	};

	struct FInteraction
	{
		TWeakObjectPtr<UWidget> HitWidget;
		TWeakObjectPtr<UBorder> VisualBorder;
		TWeakObjectPtr<UTextBlock> Label;
		EInteractionType Type = EInteractionType::Navigation;
		int32 Index = INDEX_NONE;
		FName Id;
	};

	UPROPERTY(Transient)
	TObjectPtr<UCanvasPanel> RootCanvas;

	UPROPERTY(Transient)
	TObjectPtr<UTextBlock> EyebrowText;

	UPROPERTY(Transient)
	TObjectPtr<UTextBlock> TitleText;

	UPROPERTY(Transient)
	TObjectPtr<UTextBlock> BodyText;

	UPROPERTY(Transient)
	TObjectPtr<UTextBlock> ArchiveCodeText;

	UPROPERTY(Transient)
	TObjectPtr<UTextBlock> EnglishSubtitleText;

	UPROPERTY(Transient)
	TObjectPtr<UImage> ArtifactImage;

	UPROPERTY(Transient)
	TObjectPtr<UImage> ArtifactInkWash;

	UPROPERTY(Transient)
	TArray<TObjectPtr<UTexture2D>> ArtifactTextures;

	UPROPERTY(Transient)
	TObjectPtr<UTextBlock> PageNumberText;

	UPROPERTY(Transient)
	TObjectPtr<UBorder> PreviewPanel;

	UPROPERTY(Transient)
	TObjectPtr<UTextBlock> PreviewText;

	UPROPERTY(Transient)
	TObjectPtr<UProgressBar> GazeProgress;

	UPROPERTY(Transient)
	TArray<TObjectPtr<UBorder>> PageDots;

	UPROPERTY(Transient)
	TArray<FBronzeExhibitPage> Pages;

	UPROPERTY(Transient)
	TArray<FText> NavigationLabels;

	UPROPERTY(Transient)
	TArray<FName> NavigationIds;

	UPROPERTY(Transient)
	TObjectPtr<ABronzeExhibitHost> ExhibitHost;

	UPROPERTY(Transient)
	TObjectPtr<UTexture2D> InkMountainsTexture;

	UPROPERTY(Transient)
	TObjectPtr<UObject> ExhibitFont;

	TArray<FInteraction> Interactions;
	TWeakObjectPtr<UObject> TobiiSubsystem;
	int32 CurrentPage = 0;
	int32 VisualInteractionIndex = INDEX_NONE;
	int32 GazeInteractionIndex = INDEX_NONE;
	double LastMouseInputSeconds = -1000.0;
	double LastGazeSampleSeconds = -1000.0;
	double GazeTargetStartSeconds = 0.0;
	FVector2D LatestGazePoint = FVector2D::ZeroVector;
	bool bLatestGazeValid = false;
	bool bGazePreviewVisible = false;
	bool bGazeActivated = false;
	bool bBuilt = false;

	void BuildExhibit();
	void BuildNavigation();
	void BuildPageDots();
	void SynchronizeFromHost();
	void RefreshPage();
	void RefreshPageDots();
	void PollTobiiGaze();
	void UpdateGazeInteraction(const FGeometry& MyGeometry, double Now);
	void ResetGazeInteraction();
	void SetVisualInteraction(int32 InteractionIndex, bool bFromGaze);
	void SetPreviewVisible(bool bVisible, int32 InteractionIndex = INDEX_NONE);
	void ActivateInteraction(int32 InteractionIndex);
	int32 FindInteractionAtScreenPoint(const FVector2D& ScreenPoint) const;
	FName GetInteractionId(const FInteraction& Interaction) const;
};
