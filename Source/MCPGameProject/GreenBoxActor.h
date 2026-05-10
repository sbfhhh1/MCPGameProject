#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "GreenBoxActor.generated.h"

UCLASS()
class MCPGAMEPROJECT_API AGreenBoxActor : public AActor
{
    GENERATED_BODY()
    
public:
    AGreenBoxActor();
    
protected:
    virtual void BeginPlay() override;
    
public:
    virtual void Tick(float DeltaTime) override;
    
    // Static mesh component for the box
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
    class UStaticMeshComponent* BoxMesh;
};