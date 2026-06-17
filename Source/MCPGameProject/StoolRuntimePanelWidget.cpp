#include "StoolRuntimePanelWidget.h"

#include "BlenderGeometryNodesComponent.h"
#include "BlenderGeometryNodesTypes.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/Slider.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Widgets/SWidget.h"

namespace
{
FString GetInputLabel(const FBlenderGNInput& Input)
{
	return !Input.DisplayName.IsEmpty() ? Input.DisplayName : Input.GetBestName();
}

float GetInputValue(const FBlenderGNInput& Input)
{
	return Input.Type == EBlenderGNParameterType::Int ? static_cast<float>(Input.IntValue) : Input.FloatValue;
}

FText FormatInputValue(const FBlenderGNInput& Input)
{
	if (Input.Type == EBlenderGNParameterType::Int)
	{
		return FText::AsNumber(Input.IntValue);
	}

	FNumberFormattingOptions Options;
	Options.SetMaximumFractionalDigits(3);
	return FText::AsNumber(Input.FloatValue, &Options);
}
}

TSharedRef<SWidget> UStoolRuntimePanelWidget::RebuildWidget()
{
	if (WidgetTree && !WidgetTree->RootWidget)
	{
		BuildDefaultPanel();
	}

	return Super::RebuildWidget();
}

void UStoolRuntimePanelWidget::NativeConstruct()
{
	Super::NativeConstruct();
	SynchronizeControls();
	UpdateStatusText();
}

void UStoolRuntimePanelWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);
	PumpQueuedRebuild();
	UpdateStatusText();
}

void UStoolRuntimePanelWidget::SetTarget(UBlenderGeometryNodesComponent* InTarget)
{
	Target = InTarget;
	SynchronizeControls();
	UpdateStatusText();
}

void UStoolRuntimePanelWidget::BuildDefaultPanel()
{
	InputSliders.Reset();
	InputValueTexts.Reset();
	InputIndices.Reset();
	LastSliderValues.Reset();

	UCanvasPanel* Root = WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass(), TEXT("StoolControlRoot"));
	WidgetTree->RootWidget = Root;

	UBorder* Panel = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("StoolControlPanel"));
	Panel->SetBrushColor(FLinearColor(0.02f, 0.025f, 0.035f, 0.9f));
	Panel->SetPadding(FMargin(12.0f));
	if (UCanvasPanelSlot* PanelSlot = Root->AddChildToCanvas(Panel))
	{
		PanelSlot->SetAnchors(FAnchors(0.0f, 0.0f));
		PanelSlot->SetPosition(FVector2D(22.0f, 22.0f));
		PanelSlot->SetSize(FVector2D(390.0f, 430.0f));
	}

	UVerticalBox* Content = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("StoolControlContent"));
	Panel->SetContent(Content);

	auto MakeText = [this](const TCHAR* Name, const FString& Text, int32 FontSize, const FLinearColor& Color)
	{
		UTextBlock* TextBlock = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), Name);
		TextBlock->SetText(FText::FromString(Text));
		TextBlock->SetColorAndOpacity(FSlateColor(Color));
		FSlateFontInfo FontInfo = TextBlock->GetFont();
		FontInfo.Size = FontSize;
		TextBlock->SetFont(FontInfo);
		return TextBlock;
	};

	UTextBlock* Title = MakeText(TEXT("StoolControlTitle"), TEXT("Stool Runtime Control"), 18, FLinearColor(0.9f, 0.92f, 1.0f, 1.0f));
	if (UVerticalBoxSlot* TitleSlot = Content->AddChildToVerticalBox(Title))
	{
		TitleSlot->SetPadding(FMargin(0.0f, 0.0f, 0.0f, 8.0f));
	}

	if (Target)
	{
		for (int32 InputIndex = 0; InputIndex < Target->Inputs.Num(); ++InputIndex)
		{
			const FBlenderGNInput& Input = Target->Inputs[InputIndex];
			if (!Input.bShowInRuntimePanel || (Input.Type != EBlenderGNParameterType::Float && Input.Type != EBlenderGNParameterType::Int))
			{
				continue;
			}

			UHorizontalBox* Row = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), *FString::Printf(TEXT("StoolInputRow_%d"), InputIndex));
			if (UVerticalBoxSlot* RowSlot = Content->AddChildToVerticalBox(Row))
			{
				RowSlot->SetPadding(FMargin(0.0f, 4.0f, 0.0f, 4.0f));
			}

			UTextBlock* LabelText = MakeText(*FString::Printf(TEXT("StoolInputLabel_%d"), InputIndex), GetInputLabel(Input), 13, FLinearColor(0.72f, 0.76f, 0.84f, 1.0f));
			LabelText->SetMinDesiredWidth(110.0f);
			if (UHorizontalBoxSlot* LabelSlot = Row->AddChildToHorizontalBox(LabelText))
			{
				LabelSlot->SetPadding(FMargin(0.0f, 0.0f, 8.0f, 0.0f));
				LabelSlot->SetSize(FSlateChildSize(ESlateSizeRule::Automatic));
				LabelSlot->SetVerticalAlignment(VAlign_Center);
			}

			USlider* Slider = WidgetTree->ConstructWidget<USlider>(USlider::StaticClass(), *FString::Printf(TEXT("StoolInputSlider_%d"), InputIndex));
			Slider->SetMinValue(Input.SliderMin);
			Slider->SetMaxValue(FMath::Max(Input.SliderMin + KINDA_SMALL_NUMBER, Input.SliderMax));
			Slider->SetValue(GetInputValue(Input));
			Slider->OnValueChanged.AddDynamic(this, &UStoolRuntimePanelWidget::HandleSliderChanged);
			if (UHorizontalBoxSlot* SliderSlot = Row->AddChildToHorizontalBox(Slider))
			{
				SliderSlot->SetPadding(FMargin(0.0f, 0.0f, 8.0f, 0.0f));
				SliderSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
				SliderSlot->SetVerticalAlignment(VAlign_Center);
			}

			UTextBlock* ValueText = MakeText(*FString::Printf(TEXT("StoolInputValue_%d"), InputIndex), TEXT("0"), 12, FLinearColor(0.92f, 0.94f, 1.0f, 1.0f));
			ValueText->SetMinDesiredWidth(48.0f);
			if (UHorizontalBoxSlot* ValueSlot = Row->AddChildToHorizontalBox(ValueText))
			{
				ValueSlot->SetSize(FSlateChildSize(ESlateSizeRule::Automatic));
				ValueSlot->SetVerticalAlignment(VAlign_Center);
			}

			InputIndices.Add(InputIndex);
			InputSliders.Add(Slider);
			InputValueTexts.Add(ValueText);
			LastSliderValues.Add(GetInputValue(Input));
		}
	}

	StatusTextBlock = MakeText(TEXT("StoolStatus"), TEXT("Idle"), 11, FLinearColor(0.58f, 0.64f, 0.72f, 1.0f));
	if (UVerticalBoxSlot* StatusSlot = Content->AddChildToVerticalBox(StatusTextBlock))
	{
		StatusSlot->SetPadding(FMargin(0.0f, 12.0f, 0.0f, 0.0f));
	}
}

void UStoolRuntimePanelWidget::SynchronizeControls()
{
	if (!Target)
	{
		return;
	}

	bSynchronizingControls = true;
	for (int32 ControlIndex = 0; ControlIndex < InputIndices.Num(); ++ControlIndex)
	{
		const int32 InputIndex = InputIndices[ControlIndex];
		if (!Target->Inputs.IsValidIndex(InputIndex))
		{
			continue;
		}

		const FBlenderGNInput& Input = Target->Inputs[InputIndex];
		const float Value = GetInputValue(Input);
		if (USlider* Slider = InputSliders.IsValidIndex(ControlIndex) ? InputSliders[ControlIndex].Get() : nullptr)
		{
			Slider->SetValue(Value);
		}
		if (LastSliderValues.IsValidIndex(ControlIndex))
		{
			LastSliderValues[ControlIndex] = Value;
		}
		UpdateValueText(ControlIndex);
	}
	bSynchronizingControls = false;
}

void UStoolRuntimePanelWidget::UpdateValueText(int32 ControlIndex)
{
	if (!Target || !InputIndices.IsValidIndex(ControlIndex) || !InputValueTexts.IsValidIndex(ControlIndex))
	{
		return;
	}

	const int32 InputIndex = InputIndices[ControlIndex];
	if (!Target->Inputs.IsValidIndex(InputIndex) || !InputValueTexts[ControlIndex])
	{
		return;
	}

	InputValueTexts[ControlIndex]->SetText(FormatInputValue(Target->Inputs[InputIndex]));
}

void UStoolRuntimePanelWidget::UpdateStatusText()
{
	if (!StatusTextBlock)
	{
		return;
	}

	const FString Status = Target
		? FString::Printf(TEXT("%s | %d verts | %d tris"), *Target->LastStatus, Target->LastVertexCount, Target->LastTriangleCount)
		: TEXT("No Geometry Nodes target");
	StatusTextBlock->SetText(FText::FromString(Status));
}

void UStoolRuntimePanelWidget::QueueRebuild()
{
	bRebuildQueued = true;
	RebuildAtSeconds = (GetWorld() ? GetWorld()->GetTimeSeconds() : 0.0) + RebuildDebounceSeconds;
}

void UStoolRuntimePanelWidget::PumpQueuedRebuild()
{
	if (!bRebuildQueued || !Target)
	{
		return;
	}

	const double Now = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.0;
	if (Now < RebuildAtSeconds || Target->bIsRunning)
	{
		return;
	}

	bRebuildQueued = false;
	Target->RequestRefresh(true);
}

void UStoolRuntimePanelWidget::HandleSliderChanged(float Value)
{
	if (bSynchronizingControls || !Target)
	{
		return;
	}

	for (int32 ControlIndex = 0; ControlIndex < InputSliders.Num(); ++ControlIndex)
	{
		USlider* Slider = InputSliders[ControlIndex];
		if (!Slider)
		{
			continue;
		}

		const float CurrentValue = Slider->GetValue();
		if (LastSliderValues.IsValidIndex(ControlIndex) && FMath::IsNearlyEqual(CurrentValue, LastSliderValues[ControlIndex], 0.0001f))
		{
			continue;
		}

		const int32 InputIndex = InputIndices.IsValidIndex(ControlIndex) ? InputIndices[ControlIndex] : INDEX_NONE;
		if (!Target->Inputs.IsValidIndex(InputIndex))
		{
			continue;
		}

		const FBlenderGNInput& Input = Target->Inputs[InputIndex];
		if (Input.Type == EBlenderGNParameterType::Int)
		{
			const int32 IntValue = FMath::RoundToInt(CurrentValue);
			Target->SetIntInput(Input.SocketName, IntValue, false);
			Slider->SetValue(static_cast<float>(IntValue));
			LastSliderValues[ControlIndex] = static_cast<float>(IntValue);
		}
		else
		{
			Target->SetFloatInput(Input.SocketName, CurrentValue, false);
			LastSliderValues[ControlIndex] = CurrentValue;
		}

		UpdateValueText(ControlIndex);
		QueueRebuild();
		return;
	}
}
