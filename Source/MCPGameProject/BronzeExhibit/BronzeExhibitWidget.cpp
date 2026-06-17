#include "BronzeExhibitWidget.h"

#include "BronzeExhibitHost.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/Image.h"
#include "Components/ProgressBar.h"
#include "Components/TextBlock.h"
#include "Engine/Font.h"
#include "HAL/PlatformTime.h"
#include "Input/Reply.h"
#include "InputCoreTypes.h"
#include "Engine/GameInstance.h"
#include "Engine/Texture2D.h"
#include "Misc/Paths.h"
#include "UObject/UnrealType.h"
#include "Widgets/SWidget.h"

namespace BronzeExhibitStyle
{
	// Warm charcoal rice-paper palette matched to the reference video (no teal cast).
	const FLinearColor Ink(0.052f, 0.049f, 0.044f, 1.0f);          // warm near-black paper
	const FLinearColor InkRaised(0.085f, 0.080f, 0.072f, 0.92f);   // raised warm panel
	const FLinearColor Gold(0.78f, 0.62f, 0.30f, 1.0f);            // seal-script gold
	const FLinearColor GoldSoft(0.62f, 0.52f, 0.33f, 1.0f);        // muted body gold-gray
	const FLinearColor GoldFaint(0.34f, 0.29f, 0.18f, 0.8f);       // inactive dot/line
	const FLinearColor GoldHighlight(0.92f, 0.76f, 0.40f, 1.0f);   // bright title gold
	const FLinearColor SealRed(0.60f, 0.13f, 0.10f, 1.0f);         // vermillion seal
	const FLinearColor Transparent(0.0f, 0.0f, 0.0f, 0.0f);

	void Place(UCanvasPanel* Canvas, UWidget* Widget, const FAnchors& Anchors, const FMargin& Offsets, const FVector2D& Alignment = FVector2D::ZeroVector)
	{
		if (UCanvasPanelSlot* Slot = Canvas ? Canvas->AddChildToCanvas(Widget) : nullptr)
		{
			Slot->SetAnchors(Anchors);
			Slot->SetOffsets(Offsets);
			Slot->SetAlignment(Alignment);
		}
	}
}

TSharedRef<SWidget> UBronzeExhibitWidget::RebuildWidget()
{
	if (WidgetTree && !WidgetTree->RootWidget)
	{
		BuildExhibit();
	}

	return Super::RebuildWidget();
}

void UBronzeExhibitWidget::NativeConstruct()
{
	Super::NativeConstruct();
	RefreshPage();
}

void UBronzeExhibitWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);
	PollTobiiGaze();
	UpdateGazeInteraction(MyGeometry, FPlatformTime::Seconds());
}

void UBronzeExhibitWidget::SetPages(const TArray<FBronzeExhibitPage>& InPages, int32 InitialPage)
{
	Pages = InPages;
	CurrentPage = Pages.IsEmpty() ? 0 : FMath::Clamp(InitialPage, 0, Pages.Num() - 1);
	RefreshPage();
}

void UBronzeExhibitWidget::SetNavigationItems(const TArray<FText>& Labels, const TArray<FName>& Ids)
{
	NavigationLabels = Labels;
	NavigationIds = Ids;

	if (bBuilt)
	{
		BuildExhibit();
		InvalidateLayoutAndVolatility();
	}
}

void UBronzeExhibitWidget::SetExhibitHost(ABronzeExhibitHost* InHost)
{
	ExhibitHost = InHost;
	SynchronizeFromHost();
}

void UBronzeExhibitWidget::HandleExhibitPageChanged()
{
	SynchronizeFromHost();
}

void UBronzeExhibitWidget::HandleExhibitStateChanged()
{
	// Reserved for host-driven state badges or autoplay presentation changes.
}

void UBronzeExhibitWidget::HandleTobiiSimulationChanged()
{
	TobiiSubsystem.Reset();
}

void UBronzeExhibitWidget::SetPage(int32 PageIndex, bool bNotifyHost)
{
	if (Pages.IsEmpty())
	{
		return;
	}

	const int32 NewPage = FMath::Clamp(PageIndex, 0, Pages.Num() - 1);
	if (NewPage == CurrentPage)
	{
		return;
	}

	CurrentPage = NewPage;
	RefreshPage();
	if (bNotifyHost)
	{
		OnPageChanged.Broadcast(CurrentPage);
	}
}

void UBronzeExhibitWidget::ShowNextPage()
{
	if (!Pages.IsEmpty())
	{
		SetPage((CurrentPage + 1) % Pages.Num());
	}
}

void UBronzeExhibitWidget::ShowPreviousPage()
{
	if (!Pages.IsEmpty())
	{
		SetPage((CurrentPage - 1 + Pages.Num()) % Pages.Num());
	}
}

void UBronzeExhibitWidget::SubmitTobiiGazeNormalized(FVector2D NormalizedDisplayPoint, bool bValid, bool bTobiiBottomUpY)
{
	LatestGazePoint.X = FMath::Clamp(NormalizedDisplayPoint.X, 0.0, 1.0);
	LatestGazePoint.Y = FMath::Clamp(bTobiiBottomUpY ? 1.0 - NormalizedDisplayPoint.Y : NormalizedDisplayPoint.Y, 0.0, 1.0);
	bLatestGazeValid = bValid;
	LastGazeSampleSeconds = FPlatformTime::Seconds();
}

void UBronzeExhibitWidget::ClearTobiiGaze()
{
	bLatestGazeValid = false;
	ResetGazeInteraction();
}

FReply UBronzeExhibitWidget::NativeOnPreviewMouseButtonDown(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent)
{
	if (InMouseEvent.GetEffectingButton() == EKeys::LeftMouseButton)
	{
		LastMouseInputSeconds = FPlatformTime::Seconds();
		const int32 InteractionIndex = FindInteractionAtScreenPoint(InMouseEvent.GetScreenSpacePosition());
		if (InteractionIndex != INDEX_NONE)
		{
			ResetGazeInteraction();
			SetVisualInteraction(InteractionIndex, false);
			ActivateInteraction(InteractionIndex);
			return FReply::Handled();
		}
	}

	return Super::NativeOnPreviewMouseButtonDown(InGeometry, InMouseEvent);
}

FReply UBronzeExhibitWidget::NativeOnMouseMove(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent)
{
	LastMouseInputSeconds = FPlatformTime::Seconds();
	ResetGazeInteraction();
	SetVisualInteraction(FindInteractionAtScreenPoint(InMouseEvent.GetScreenSpacePosition()), false);
	return Super::NativeOnMouseMove(InGeometry, InMouseEvent);
}

void UBronzeExhibitWidget::NativeOnMouseLeave(const FPointerEvent& InMouseEvent)
{
	SetVisualInteraction(INDEX_NONE, false);
	Super::NativeOnMouseLeave(InMouseEvent);
}

void UBronzeExhibitWidget::BuildExhibit()
{
	using namespace BronzeExhibitStyle;

	Interactions.Reset();
	PageDots.Reset();
	VisualInteractionIndex = INDEX_NONE;
	GazeInteractionIndex = INDEX_NONE;

	// Load presentation textures.
	UTexture2D* PaperTexture = LoadObject<UTexture2D>(nullptr, TEXT("/Game/BronzeExhibit/Visual/T_Bronze_Paper.T_Bronze_Paper"));
	UTexture2D* InkWashTexture = LoadObject<UTexture2D>(nullptr, TEXT("/Game/BronzeExhibit/Visual/T_Bronze_InkWash.T_Bronze_InkWash"));
	InkMountainsTexture = LoadObject<UTexture2D>(nullptr, TEXT("/Game/BronzeExhibit/Visual/T_Bronze_InkMountains.T_Bronze_InkMountains"));
	ExhibitFont = LoadObject<UObject>(nullptr, TEXT("/Game/BronzeExhibit/Fonts/NotoSerifSC.NotoSerifSC"));

	// Per-page bronze artifact photos — dark-matte versions (white studio bg removed).
	ArtifactTextures.Reset();
	for (const TCHAR* Path : {
			TEXT("/Game/BronzeExhibit/Visual/T_Bronze_Zun_Dark.T_Bronze_Zun_Dark"),
			TEXT("/Game/BronzeExhibit/Visual/T_Bronze_Ding_Dark.T_Bronze_Ding_Dark"),
			TEXT("/Game/BronzeExhibit/Visual/T_Bronze_Gui_Dark.T_Bronze_Gui_Dark") })
	{
		if (UTexture2D* T = LoadObject<UTexture2D>(nullptr, Path))
		{
			ArtifactTextures.Add(T);
		}
	}

	RootCanvas = WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass(), TEXT("BronzeExhibitRoot"));
	WidgetTree->RootWidget = RootCanvas;

	// --- Background: warm charcoal paper grain, full screen ---
	UBorder* Background = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("InkBackground"));
	Background->SetBrushColor(Ink);
	Place(RootCanvas, Background, FAnchors(0.0f, 0.0f, 1.0f, 1.0f), FMargin(0.0f));

	if (PaperTexture)
	{
		UImage* Paper = WidgetTree->ConstructWidget<UImage>(UImage::StaticClass(), TEXT("PaperGrain"));
		Paper->SetBrushFromTexture(PaperTexture, false);
		Paper->SetColorAndOpacity(FLinearColor(1.0f, 1.0f, 1.0f, 1.0f));
		Paper->SetVisibility(ESlateVisibility::HitTestInvisible);
		Place(RootCanvas, Paper, FAnchors(0.0f, 0.0f, 1.0f, 1.0f), FMargin(0.0f));
	}

	if (InkMountainsTexture)
	{
		UImage* InkMountains = WidgetTree->ConstructWidget<UImage>(UImage::StaticClass(), TEXT("InkMountainsBackground"));
		InkMountains->SetBrushFromTexture(InkMountainsTexture, false);
		InkMountains->SetColorAndOpacity(FLinearColor(0.72f, 0.66f, 0.55f, 0.16f)); // warm, faint
		InkMountains->SetVisibility(ESlateVisibility::HitTestInvisible);
		Place(RootCanvas, InkMountains, FAnchors(0.0f, 0.55f, 1.0f, 1.0f), FMargin(0.0f));
	}

	auto MakeText = [this](const FName Name, const FText& Text, int32 Size, const FLinearColor& Color)
	{
		UTextBlock* Block = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), Name);
		Block->SetText(Text);
		Block->SetColorAndOpacity(FSlateColor(Color));
		FSlateFontInfo Font(FPaths::ProjectContentDir() / TEXT("BronzeExhibit/SourceArt/NotoSerifSC-VF.ttf"), Size);
		Block->SetFont(Font);
		return Block;
	};

	// --- Top bar: seal logo (left) + gold hairline ---
	UBorder* SealLogo = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("SealLogo"));
	SealLogo->SetBrushColor(Transparent);
	SealLogo->SetPadding(FMargin(0.0f));
	Place(RootCanvas, SealLogo, FAnchors(0.0f, 0.0f), FMargin(64.0f, 24.0f, 72.0f, 72.0f));
	{
		// gold square frame
		UBorder* SealFrame = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("SealLogoFrame"));
		SealFrame->SetBrushColor(Gold);
		Place(RootCanvas, SealFrame, FAnchors(0.0f, 0.0f), FMargin(64.0f, 24.0f, 60.0f, 60.0f));
		// red seal field inside the gold frame (matches the vermillion stamp in the video)
		UBorder* SealInner = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("SealLogoInner"));
		SealInner->SetBrushColor(SealRed);
		Place(RootCanvas, SealInner, FAnchors(0.0f, 0.0f), FMargin(67.0f, 27.0f, 54.0f, 54.0f));
		// 2x2 seal-script glyphs in light cream
		UTextBlock* SealGlyph = MakeText(TEXT("SealGlyph"), FText::FromString(TEXT("青銅\n典藏")), 15, FLinearColor(0.96f, 0.92f, 0.84f, 1.0f));
		SealGlyph->SetJustification(ETextJustify::Center);
		SealGlyph->SetAutoWrapText(true);
		Place(RootCanvas, SealGlyph, FAnchors(0.0f, 0.0f), FMargin(69.0f, 28.0f, 50.0f, 50.0f));
	}

	UBorder* HeaderLine = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("HeaderGoldLine"));
	HeaderLine->SetBrushColor(GoldFaint);
	Place(RootCanvas, HeaderLine, FAnchors(0.0f, 0.0f, 1.0f, 0.0f), FMargin(150.0f, 96.0f, 150.0f, 1.0f));

	// ============================================================
	//  FIXED COVER PAGE  "精寶藏珍"  (replicates the reference home screen)
	//  Layout reference (1920x1080):
	//   - Right: ink-wash brush sweep + dark-matte bronze artifact (crane-lid zun stand-in)
	//   - Left: gold-framed vertical seal title 精寶藏珍 (2 cols), 铜器时代 small vertical + red seal,
	//           bronze-ornament motif under the seal, English segments with gold divider lines
	//   - Bottom-right: gold cloud-scroll line
	// ============================================================

	// Big ink-wash brush sweep across the centre/right (uses the ink-mountains art as a wash).
	if (InkMountainsTexture)
	{
		UImage* Brush = WidgetTree->ConstructWidget<UImage>(UImage::StaticClass(), TEXT("CoverInkBrush"));
		Brush->SetBrushFromTexture(InkMountainsTexture, false);
		Brush->SetColorAndOpacity(FLinearColor(0.02f, 0.02f, 0.02f, 0.85f));
		Brush->SetVisibility(ESlateVisibility::HitTestInvisible);
		Place(RootCanvas, Brush, FAnchors(0.18f, 0.18f, 1.0f, 0.78f), FMargin(0.0f));
	}

	// Dark-matte bronze artifact on the right (no white box now).
	ArtifactImage = WidgetTree->ConstructWidget<UImage>(UImage::StaticClass(), TEXT("ArtifactImage"));
	ArtifactImage->SetColorAndOpacity(FLinearColor::White);
	ArtifactImage->SetVisibility(ESlateVisibility::Visible);
	Place(RootCanvas, ArtifactImage, FAnchors(0.56f, 0.18f, 0.80f, 0.96f), FMargin(0.0f));
	if (ArtifactTextures.Num() > 0 && ArtifactTextures[0])
	{
		ArtifactImage->SetBrushFromTexture(ArtifactTextures[0], true);
	}

	// --- Left: gold-framed vertical seal title 精寶藏珍 ---
	const float SealX = 470.0f;          // left of seal frame
	const float SealY = 300.0f;          // top of seal frame
	const float SealW = 150.0f, SealH = 360.0f;
	UBorder* TitleFrame = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("CoverTitleFrame"));
	TitleFrame->SetBrushColor(Gold);
	Place(RootCanvas, TitleFrame, FAnchors(0.0f, 0.0f), FMargin(SealX, SealY, SealW, SealH));
	UBorder* TitleInner = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("CoverTitleInner"));
	TitleInner->SetBrushColor(Ink);
	Place(RootCanvas, TitleInner, FAnchors(0.0f, 0.0f), FMargin(SealX + 4.0f, SealY + 4.0f, SealW - 8.0f, SealH - 8.0f));
	// two vertical columns of seal-script glyphs: 精寶 / 藏珍
	TitleText = MakeText(TEXT("CoverTitleColA"), FText::FromString(TEXT("精\n寶")), 56, GoldHighlight);
	TitleText->SetJustification(ETextJustify::Center);
	Place(RootCanvas, TitleText, FAnchors(0.0f, 0.0f), FMargin(SealX + 78.0f, SealY + 30.0f, 64.0f, 300.0f));
	UTextBlock* TitleColB = MakeText(TEXT("CoverTitleColB"), FText::FromString(TEXT("藏\n珍")), 56, GoldHighlight);
	TitleColB->SetJustification(ETextJustify::Center);
	Place(RootCanvas, TitleColB, FAnchors(0.0f, 0.0f), FMargin(SealX + 14.0f, SealY + 130.0f, 64.0f, 300.0f));

	// 铜器时代 vertical small text left of the seal frame
	EyebrowText = MakeText(TEXT("CoverEra"), FText::FromString(TEXT("銅\n器\n时\n代")), 14, GoldSoft);
	EyebrowText->SetJustification(ETextJustify::Center);
	Place(RootCanvas, EyebrowText, FAnchors(0.0f, 0.0f), FMargin(SealX - 56.0f, SealY + 70.0f, 30.0f, 170.0f));
	// small red seal under the 铜器时代 column
	UBorder* CoverRedSeal = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("CoverRedSeal"));
	CoverRedSeal->SetBrushColor(SealRed);
	Place(RootCanvas, CoverRedSeal, FAnchors(0.0f, 0.0f), FMargin(SealX - 58.0f, SealY + 250.0f, 34.0f, 34.0f));

	// bronze-ornament motif strip under the seal frame (use ornaments texture if present)
	UTexture2D* OrnTex = LoadObject<UTexture2D>(nullptr, TEXT("/Game/BronzeExhibit/Visual/T_Bronze_Ornaments.T_Bronze_Ornaments"));
	if (OrnTex)
	{
		UImage* Orn = WidgetTree->ConstructWidget<UImage>(UImage::StaticClass(), TEXT("CoverOrnament"));
		Orn->SetBrushFromTexture(OrnTex, false);
		Orn->SetColorAndOpacity(FLinearColor(0.78f, 0.62f, 0.30f, 0.85f));
		Orn->SetVisibility(ESlateVisibility::HitTestInvisible);
		Place(RootCanvas, Orn, FAnchors(0.0f, 0.0f), FMargin(SealX - 30.0f, SealY + SealH + 14.0f, 180.0f, 46.0f));
	}

	// --- English segment block to the right of the seal title, with gold divider lines ---
	auto MakeEng = [this, &MakeText](const TCHAR* Name, const FText& T, int32 Size, const FLinearColor& C, float X, float Y, float W)
	{
		UTextBlock* B = MakeText(FName(Name), T, Size, C);
		Place(RootCanvas, B, FAnchors(0.0f, 0.0f), FMargin(X, Y, W, 60.0f));
		return B;
	};
	const float EngX = SealX + SealW + 30.0f;
	MakeEng(TEXT("EngA"), FText::FromString(TEXT("AUSPICIOUS\nMETALS")), 15, GoldSoft, EngX, SealY + 6.0f, 300.0f);
	{
		UBorder* L = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("EngLine1"));
		L->SetBrushColor(GoldFaint);
		Place(RootCanvas, L, FAnchors(0.0f, 0.0f), FMargin(EngX, SealY + 66.0f, 150.0f, 1.0f));
	}
	MakeEng(TEXT("EngB"), FText::FromString(TEXT("CHINESE\nCULTURE")), 21, GoldHighlight, EngX, SealY + 84.0f, 300.0f);
	MakeEng(TEXT("EngC"), FText::FromString(TEXT("IS  BROADS\nAND PRODOUND")), 13, GoldSoft, EngX, SealY + 150.0f, 320.0f);
	{
		UBorder* L = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("EngLine2"));
		L->SetBrushColor(GoldFaint);
		Place(RootCanvas, L, FAnchors(0.0f, 0.0f), FMargin(EngX, SealY + 206.0f, 150.0f, 1.0f));
	}
	MakeEng(TEXT("EngD"), FText::FromString(TEXT("EXCELLENT\nPRODUCTS")), 15, GoldSoft, EngX, SealY + 224.0f, 300.0f);

	// --- Bottom-right gold cloud-scroll line (simple stepped回纹 from thin gold bars) ---
	auto GoldBar = [this](const TCHAR* Name, float X, float Y, float W, float H)
	{
		UBorder* B = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), FName(Name));
		B->SetBrushColor(BronzeExhibitStyle::Gold);
		B->SetVisibility(ESlateVisibility::HitTestInvisible);
		Place(RootCanvas, B, FAnchors(1.0f, 1.0f), FMargin(X, Y, W, H), FVector2D(1.0f, 1.0f));
	};
	// a small ruyi/cloud meander built from gold segments, lower-right corner
	GoldBar(TEXT("Cloud1"), -360.0f, -150.0f, 220.0f, 2.0f);
	GoldBar(TEXT("Cloud2"), -140.0f, -150.0f, 2.0f, 64.0f);
	GoldBar(TEXT("Cloud3"), -240.0f, -88.0f, 100.0f, 2.0f);
	GoldBar(TEXT("Cloud4"), -240.0f, -150.0f, 2.0f, 64.0f);
	GoldBar(TEXT("Cloud5"), -240.0f, -206.0f, 160.0f, 2.0f);
	GoldBar(TEXT("Cloud6"), -80.0f, -206.0f, 2.0f, 58.0f);

	// --- Hidden holders so RefreshPage / interactions stay valid on the cover ---
	EnglishSubtitleText = MakeText(TEXT("HiddenEng"), FText::GetEmpty(), 12, GoldSoft);
	EnglishSubtitleText->SetVisibility(ESlateVisibility::Collapsed);
	Place(RootCanvas, EnglishSubtitleText, FAnchors(1.0f, 1.0f), FMargin(-20.0f, -20.0f, 10.0f, 10.0f), FVector2D(1.0f, 1.0f));
	BodyText = MakeText(TEXT("HiddenBody"), FText::GetEmpty(), 12, GoldSoft);
	BodyText->SetVisibility(ESlateVisibility::Collapsed);
	Place(RootCanvas, BodyText, FAnchors(1.0f, 1.0f), FMargin(-20.0f, -34.0f, 10.0f, 10.0f), FVector2D(1.0f, 1.0f));
	ArchiveCodeText = MakeText(TEXT("ArchiveCode"), FText::GetEmpty(), 12, GoldSoft);
	ArchiveCodeText->SetVisibility(ESlateVisibility::Collapsed);
	Place(RootCanvas, ArchiveCodeText, FAnchors(1.0f, 1.0f), FMargin(-20.0f, -48.0f, 10.0f, 10.0f), FVector2D(1.0f, 1.0f));
	PageNumberText = MakeText(TEXT("PageNumber"), FText::GetEmpty(), 12, GoldSoft);
	PageNumberText->SetVisibility(ESlateVisibility::Collapsed);
	Place(RootCanvas, PageNumberText, FAnchors(1.0f, 1.0f), FMargin(-20.0f, -62.0f, 10.0f, 10.0f), FVector2D(1.0f, 1.0f));

	PreviewPanel = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("GazePreviewPanel"));
	PreviewPanel->SetBrushColor(FLinearColor(0.10f, 0.085f, 0.06f, 0.97f));
	PreviewPanel->SetPadding(FMargin(18.0f, 12.0f));
	PreviewPanel->SetVisibility(ESlateVisibility::Collapsed);
	Place(RootCanvas, PreviewPanel, FAnchors(0.5f, 1.0f), FMargin(-190.0f, -172.0f, 380.0f, 58.0f));

	PreviewText = MakeText(TEXT("GazePreviewText"), FText::FromString(TEXT("凝视预览")), 15, GoldHighlight);
	PreviewText->SetJustification(ETextJustify::Center);
	PreviewPanel->SetContent(PreviewText);

	GazeProgress = WidgetTree->ConstructWidget<UProgressBar>(UProgressBar::StaticClass(), TEXT("GazeProgress"));
	GazeProgress->SetFillColorAndOpacity(GoldHighlight);
	GazeProgress->SetPercent(0.0f);
	GazeProgress->SetVisibility(ESlateVisibility::Collapsed);
	Place(RootCanvas, GazeProgress, FAnchors(0.5f, 1.0f), FMargin(-150.0f, -105.0f, 300.0f, 4.0f));

	BuildNavigation();
	BuildPageDots();
	bBuilt = true;
	RefreshPage();
}

void UBronzeExhibitWidget::BuildNavigation()
{
	using namespace BronzeExhibitStyle;

	if (NavigationLabels.IsEmpty())
	{
		NavigationLabels = {
			FText::FromString(TEXT("典藏")),
			FText::FromString(TEXT("纹饰")),
			FText::FromString(TEXT("工艺")),
			FText::FromString(TEXT("源流")),
			FText::FromString(TEXT("礼制")),
			FText::FromString(TEXT("铭文")),
			FText::FromString(TEXT("新生"))
		};
		NavigationIds = { TEXT("archive"), TEXT("patterns"), TEXT("craft"), TEXT("history"), TEXT("ritual"), TEXT("inscriptions"), TEXT("renewal") };
	}

	const int32 Count = NavigationLabels.Num();
	const float ItemWidth = Count >= 7 ? 76.0f : 96.0f;
	UE_LOG(LogTemp, Display, TEXT("BronzeExhibit: building %d navigation items."), Count);
	for (int32 Index = 0; Index < Count; ++Index)
	{
		UBorder* Border = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), *FString::Printf(TEXT("Nav_%d"), Index));
		Border->SetBrushColor(Transparent);
		Border->SetPadding(FMargin(6.0f, 8.0f));

		UTextBlock* Label = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), *FString::Printf(TEXT("NavLabel_%d"), Index));
		Label->SetText(NavigationLabels[Index]);
		Label->SetColorAndOpacity(FSlateColor(Index == 0 ? GoldHighlight : GoldSoft));
		FSlateFontInfo Font(FPaths::ProjectContentDir() / TEXT("BronzeExhibit/SourceArt/NotoSerifSC-VF.ttf"), 18);
		Label->SetFont(Font);
		Label->SetJustification(ETextJustify::Center);
		Border->SetContent(Label);

		const float AnchorX = Count > 1
			? FMath::Lerp(0.32f, 0.80f, static_cast<float>(Index) / static_cast<float>(Count - 1))
			: 0.58f;
		Place(RootCanvas, Border, FAnchors(AnchorX, 0.0f), FMargin(-ItemWidth * 0.5f, 30.0f, ItemWidth, 44.0f));

		FInteraction& Interaction = Interactions.AddDefaulted_GetRef();
		Interaction.HitWidget = Border;
		Interaction.VisualBorder = Border;
		Interaction.Label = Label;
		Interaction.Type = EInteractionType::Navigation;
		Interaction.Index = Index;
		Interaction.Id = NavigationIds.IsValidIndex(Index) ? NavigationIds[Index] : FName(*FString::Printf(TEXT("nav_%d"), Index));
	}

	auto AddPageControl = [this](const TCHAR* Name, const TCHAR* LabelString, const FAnchors& Anchors, const FMargin& Offsets, EInteractionType Type)
	{
		UBorder* Border = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), Name);
		Border->SetBrushColor(BronzeExhibitStyle::Transparent);
		Border->SetPadding(FMargin(14.0f, 8.0f));
		Place(RootCanvas, Border, Anchors, Offsets);

		UTextBlock* Label = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), *FString::Printf(TEXT("%s_Label"), Name));
		Label->SetText(FText::FromString(LabelString));
		Label->SetColorAndOpacity(FSlateColor(BronzeExhibitStyle::GoldSoft));
		FSlateFontInfo Font(FPaths::ProjectContentDir() / TEXT("BronzeExhibit/SourceArt/NotoSerifSC-VF.ttf"), 18);
		Label->SetFont(Font);
		Label->SetJustification(ETextJustify::Center);
		Border->SetContent(Label);

		FInteraction& Interaction = Interactions.AddDefaulted_GetRef();
		Interaction.HitWidget = Border;
		Interaction.VisualBorder = Border;
		Interaction.Label = Label;
		Interaction.Type = Type;
		Interaction.Id = Type == EInteractionType::PreviousPage ? TEXT("previous_page") : TEXT("next_page");
	};

	// Centered ‹  page  › pagination like the reference video.
	AddPageControl(TEXT("PreviousPage"), TEXT("‹"), FAnchors(0.5f, 1.0f), FMargin(-150.0f, -86.0f, 44.0f, 40.0f), EInteractionType::PreviousPage);
	AddPageControl(TEXT("NextPage"), TEXT("›"), FAnchors(0.5f, 1.0f), FMargin(106.0f, -86.0f, 44.0f, 40.0f), EInteractionType::NextPage);
}

void UBronzeExhibitWidget::BuildPageDots()
{
	using namespace BronzeExhibitStyle;

	const int32 DotCount = FMath::Max(Pages.Num(), 1);
	const float StartX = -((DotCount - 1) * 18.0f) * 0.5f;
	for (int32 Index = 0; Index < DotCount; ++Index)
	{
		UBorder* Dot = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), *FString::Printf(TEXT("PageDot_%d"), Index));
		Dot->SetBrushColor(Index == CurrentPage ? GoldHighlight : GoldFaint);
		Place(RootCanvas, Dot, FAnchors(0.5f, 1.0f), FMargin(StartX + Index * 18.0f, -48.0f, 8.0f, 8.0f));
		PageDots.Add(Dot);
	}
}

void UBronzeExhibitWidget::SynchronizeFromHost()
{
	if (!ExhibitHost)
	{
		return;
	}

	TArray<FBronzeExhibitPage> HostPages;
	TArray<FText> HostNavigationLabels;
	TArray<FName> HostNavigationIds;
	for (const FBronzeExhibitChapterRecord& Chapter : ExhibitHost->Chapters)
	{
		HostNavigationLabels.Add(Chapter.Title);
		HostNavigationIds.Add(Chapter.ChapterId);
		for (const FBronzeExhibitPageRecord& Record : Chapter.Pages)
		{
			FBronzeExhibitPage& Page = HostPages.AddDefaulted_GetRef();
			Page.Eyebrow = Record.Kicker;
			Page.Title = Record.Title;
			Page.Body = Record.Detail.IsEmpty()
				? Record.Body
				: FText::Format(FText::FromString(TEXT("{0}\n\n{1}")), Record.Body, Record.Detail);
			Page.ArchiveCode = FText::Format(FText::FromString(TEXT("{0}\n{1}\n{2}")), Record.Era, Record.Collection, FText::FromName(Record.PageId));
		}
	}

	const bool bNavigationChanged = NavigationIds != HostNavigationIds;
	Pages = MoveTemp(HostPages);
	NavigationLabels = MoveTemp(HostNavigationLabels);
	NavigationIds = MoveTemp(HostNavigationIds);
	CurrentPage = FMath::Clamp(ExhibitHost->GetCurrentGlobalPageIndex(), 0, FMath::Max(Pages.Num() - 1, 0));

	if (bBuilt && bNavigationChanged)
	{
		BuildExhibit();
		InvalidateLayoutAndVolatility();
	}
	else
	{
		RefreshPage();
	}
}

void UBronzeExhibitWidget::RefreshPage()
{
	if (!bBuilt || !EyebrowText || !TitleText || !BodyText || !ArchiveCodeText || !PageNumberText)
	{
		return;
	}

	// FIXED COVER PAGE: the title/era/artifact are constant ("精寶藏珍" home screen),
	// so RefreshPage intentionally does NOT overwrite them. Only keep dots in sync.
	RefreshPageDots();
}

void UBronzeExhibitWidget::RefreshPageDots()
{
	const int32 WantedDots = FMath::Max(Pages.Num(), 1);
	if (PageDots.Num() != WantedDots && bBuilt)
	{
		for (UBorder* Dot : PageDots)
		{
			if (Dot)
			{
				Dot->RemoveFromParent();
			}
		}
		PageDots.Reset();
		BuildPageDots();
	}

	for (int32 Index = 0; Index < PageDots.Num(); ++Index)
	{
		if (PageDots[Index])
		{
			PageDots[Index]->SetBrushColor(Index == CurrentPage ? BronzeExhibitStyle::GoldHighlight : BronzeExhibitStyle::GoldFaint);
		}
	}
}

void UBronzeExhibitWidget::PollTobiiGaze()
{
	if (!TobiiSubsystem.IsValid())
	{
		UGameInstance* GameInstance = GetGameInstance();
		UClass* TobiiClass = FindObject<UClass>(nullptr, TEXT("/Script/TobiiEyeTracker5.TobiiEyeTrackerSubsystem"));
		if (!TobiiClass)
		{
			TobiiClass = LoadObject<UClass>(nullptr, TEXT("/Script/TobiiEyeTracker5.TobiiEyeTrackerSubsystem"));
		}
		TobiiSubsystem = GameInstance && TobiiClass ? GameInstance->GetSubsystemBase(TobiiClass) : nullptr;
	}

	UObject* Subsystem = TobiiSubsystem.Get();
	UFunction* Function = Subsystem ? Subsystem->FindFunction(TEXT("GetLatestGaze")) : nullptr;
	if (!Function)
	{
		return;
	}

	TArray<uint8> Parameters;
	Parameters.SetNumZeroed(Function->ParmsSize);
	Subsystem->ProcessEvent(Function, Parameters.GetData());

	for (TFieldIterator<FStructProperty> It(Function); It; ++It)
	{
		FStructProperty* ReturnProperty = *It;
		if (!ReturnProperty->HasAnyPropertyFlags(CPF_ReturnParm))
		{
			continue;
		}

		void* Sample = ReturnProperty->ContainerPtrToValuePtr<void>(Parameters.GetData());
		const FStructProperty* PointProperty = FindFProperty<FStructProperty>(ReturnProperty->Struct, TEXT("DisplayPoint"));
		const FBoolProperty* ValidProperty = FindFProperty<FBoolProperty>(ReturnProperty->Struct, TEXT("bValid"));
		if (PointProperty && PointProperty->Struct == TBaseStructure<FVector2D>::Get() && ValidProperty)
		{
			const FVector2D Point = *PointProperty->ContainerPtrToValuePtr<FVector2D>(Sample);
			const bool bValid = ValidProperty->GetPropertyValue_InContainer(Sample);
			SubmitTobiiGazeNormalized(Point, bValid, true);
		}
		return;
	}
}

void UBronzeExhibitWidget::UpdateGazeInteraction(const FGeometry& MyGeometry, double Now)
{
	const bool bMouseHasPriority = Now - LastMouseInputSeconds < MousePrioritySeconds;
	const bool bGazeFresh = bLatestGazeValid && Now - LastGazeSampleSeconds < 0.35;

	if (bMouseHasPriority || !bGazeFresh)
	{
		if (GazeInteractionIndex != INDEX_NONE)
		{
			ResetGazeInteraction();
		}
		if (GazeProgress)
		{
			GazeProgress->SetVisibility(ESlateVisibility::Collapsed);
		}
		return;
	}

	const FVector2D AbsolutePoint = MyGeometry.LocalToAbsolute(LatestGazePoint * MyGeometry.GetLocalSize());
	const int32 HitIndex = FindInteractionAtScreenPoint(AbsolutePoint);

	if (HitIndex != GazeInteractionIndex)
	{
		GazeInteractionIndex = HitIndex;
		GazeTargetStartSeconds = Now;
		bGazePreviewVisible = false;
		bGazeActivated = false;
		SetVisualInteraction(HitIndex, true);
		SetPreviewVisible(false);
	}

	if (GazeInteractionIndex == INDEX_NONE)
	{
		if (GazeProgress)
		{
			GazeProgress->SetVisibility(ESlateVisibility::Collapsed);
		}
		return;
	}

	const double DwellSeconds = Now - GazeTargetStartSeconds;

	if (GazeProgress)
	{
		GazeProgress->SetVisibility(ESlateVisibility::HitTestInvisible);
		GazeProgress->SetPercent(FMath::Clamp(static_cast<float>(DwellSeconds / FMath::Max(GazeActivationSeconds, 0.1f)), 0.0f, 1.0f));
	}

	if (DwellSeconds >= GazePreviewSeconds && !bGazePreviewVisible)
	{
		SetPreviewVisible(true, GazeInteractionIndex);
	}

	if (DwellSeconds >= GazeActivationSeconds && !bGazeActivated)
	{
		bGazeActivated = true;
		ActivateInteraction(GazeInteractionIndex);
		GazeTargetStartSeconds = Now;
	}
}

void UBronzeExhibitWidget::ResetGazeInteraction()
{
	GazeInteractionIndex = INDEX_NONE;
	bGazeActivated = false;
	SetPreviewVisible(false);
	if (GazeProgress)
	{
		GazeProgress->SetVisibility(ESlateVisibility::Collapsed);
		GazeProgress->SetPercent(0.0f);
	}
}

void UBronzeExhibitWidget::SetVisualInteraction(int32 InteractionIndex, bool bFromGaze)
{
	using namespace BronzeExhibitStyle;

	if (VisualInteractionIndex == InteractionIndex)
	{
		return;
	}

	if (Interactions.IsValidIndex(VisualInteractionIndex))
	{
		FInteraction& Old = Interactions[VisualInteractionIndex];
		if (Old.VisualBorder.IsValid())
		{
			Old.VisualBorder->SetBrushColor(Transparent);
		}
		if (Old.Label.IsValid())
		{
			const bool bActiveTab = Old.Type == EInteractionType::Navigation && Old.Index == 0;
			Old.Label->SetColorAndOpacity(FSlateColor(bActiveTab ? GoldHighlight : GoldSoft));
		}
	}

	VisualInteractionIndex = InteractionIndex;

	if (Interactions.IsValidIndex(VisualInteractionIndex))
	{
		FInteraction& New = Interactions[VisualInteractionIndex];
		if (New.VisualBorder.IsValid())
		{
			New.VisualBorder->SetBrushColor(FLinearColor(Gold.R, Gold.G, Gold.B, 0.16f));
		}
		if (New.Label.IsValid())
		{
			New.Label->SetColorAndOpacity(FSlateColor(GoldHighlight));
		}
	}
}

void UBronzeExhibitWidget::SetPreviewVisible(bool bVisible, int32 InteractionIndex)
{
	if (bGazePreviewVisible == bVisible)
	{
		return;
	}

	bGazePreviewVisible = bVisible;
	if (PreviewPanel)
	{
		PreviewPanel->SetVisibility(bVisible ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
	}

	FName TargetId = NAME_None;
	if (bVisible && Interactions.IsValidIndex(InteractionIndex))
	{
		TargetId = GetInteractionId(Interactions[InteractionIndex]);
		if (PreviewText)
		{
			PreviewText->SetText(FText::Format(FText::FromString(TEXT("凝视预览 · {0}")), FText::FromName(TargetId)));
		}
	}

	OnPreviewChanged.Broadcast(TargetId, bVisible);
}

void UBronzeExhibitWidget::ActivateInteraction(int32 InteractionIndex)
{
	if (!Interactions.IsValidIndex(InteractionIndex))
	{
		return;
	}

	const FInteraction& Interaction = Interactions[InteractionIndex];
	switch (Interaction.Type)
	{
	case EInteractionType::Navigation:
		OnNavigationRequested.Broadcast(GetInteractionId(Interaction));
		break;
	case EInteractionType::PreviousPage:
		ShowPreviousPage();
		break;
	case EInteractionType::NextPage:
		ShowNextPage();
		break;
	default:
		break;
	}
}

int32 UBronzeExhibitWidget::FindInteractionAtScreenPoint(const FVector2D& ScreenPoint) const
{
	for (int32 Index = 0; Index < Interactions.Num(); ++Index)
	{
		const FInteraction& Interaction = Interactions[Index];
		if (!Interaction.HitWidget.IsValid())
		{
			continue;
		}

		const FGeometry Geometry = Interaction.HitWidget->GetCachedGeometry();
		const FVector2D Local = Geometry.AbsoluteToLocal(ScreenPoint);
		const FVector2D Size = Geometry.GetLocalSize();
		if (Local.X >= 0.0f && Local.Y >= 0.0f && Local.X <= Size.X && Local.Y <= Size.Y)
		{
			return Index;
		}
	}
	return INDEX_NONE;
}

FName UBronzeExhibitWidget::GetInteractionId(const FInteraction& Interaction) const
{
	return Interaction.Id;
}
