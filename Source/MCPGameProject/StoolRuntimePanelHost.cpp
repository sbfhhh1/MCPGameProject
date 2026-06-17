#include "StoolRuntimePanelHost.h"

#include "BlenderGeometryNodesComponent.h"
#include "Kismet/GameplayStatics.h"
#include "StoolRuntimePanelWidget.h"
#include "EngineUtils.h"

AStoolRuntimePanelHost::AStoolRuntimePanelHost()
{
	PrimaryActorTick.bCanEverTick = false;
	WidgetClass = UStoolRuntimePanelWidget::StaticClass();
}

void AStoolRuntimePanelHost::BeginPlay()
{
	Super::BeginPlay();

	UBlenderGeometryNodesComponent* TargetComponent = ResolveTargetComponent();
	if (!TargetComponent || !WidgetClass)
	{
		return;
	}

	APlayerController* PlayerController = UGameplayStatics::GetPlayerController(this, 0);
	RuntimeWidget = CreateWidget<UStoolRuntimePanelWidget>(PlayerController, WidgetClass);
	if (!RuntimeWidget)
	{
		return;
	}

	RuntimeWidget->SetTarget(TargetComponent);
	RuntimeWidget->AddToViewport();

	if (PlayerController)
	{
		PlayerController->bShowMouseCursor = true;
		PlayerController->SetInputMode(FInputModeGameAndUI());
	}
}

UBlenderGeometryNodesComponent* AStoolRuntimePanelHost::ResolveTargetComponent() const
{
	if (TargetActor)
	{
		if (UBlenderGeometryNodesComponent* Component = TargetActor->FindComponentByClass<UBlenderGeometryNodesComponent>())
		{
			return Component;
		}
	}

	if (TargetActorTag.IsNone())
	{
		return nullptr;
	}

	TArray<AActor*> TaggedActors;
	UGameplayStatics::GetAllActorsWithTag(this, TargetActorTag, TaggedActors);
	for (AActor* Actor : TaggedActors)
	{
		if (!Actor)
		{
			continue;
		}

		if (UBlenderGeometryNodesComponent* Component = Actor->FindComponentByClass<UBlenderGeometryNodesComponent>())
		{
			return Component;
		}
	}

	const FString TargetName = TargetActorTag.ToString();
	for (TActorIterator<AActor> It(GetWorld()); It; ++It)
	{
		AActor* Actor = *It;
		if (!Actor)
		{
			continue;
		}

		bool bMatchesName = Actor->GetName() == TargetName;
#if WITH_EDITOR
		bMatchesName = bMatchesName || Actor->GetActorLabel() == TargetName;
#endif
		if (!bMatchesName)
		{
			continue;
		}

		if (UBlenderGeometryNodesComponent* Component = Actor->FindComponentByClass<UBlenderGeometryNodesComponent>())
		{
			return Component;
		}
	}

	return nullptr;
}
