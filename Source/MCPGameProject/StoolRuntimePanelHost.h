#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "StoolRuntimePanelHost.generated.h"

class UBlenderGeometryNodesComponent;
class UStoolRuntimePanelWidget;

UCLASS(Blueprintable)
class MCPGAMEPROJECT_API AStoolRuntimePanelHost : public AActor
{
	GENERATED_BODY()

public:
	AStoolRuntimePanelHost();

	virtual void BeginPlay() override;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stool")
	TObjectPtr<AActor> TargetActor;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stool")
	FName TargetActorTag = TEXT("Procedural_Stool_Runtime");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stool")
	TSubclassOf<UStoolRuntimePanelWidget> WidgetClass;

private:
	UPROPERTY(Transient)
	TObjectPtr<UStoolRuntimePanelWidget> RuntimeWidget;

	UBlenderGeometryNodesComponent* ResolveTargetComponent() const;
};
