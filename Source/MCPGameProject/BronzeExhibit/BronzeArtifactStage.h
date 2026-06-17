#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "BronzeExhibitTypes.h"
#include "BronzeArtifactStage.generated.h"

class USceneComponent;
class UStaticMeshComponent;

UCLASS(BlueprintType, Blueprintable)
class MCPGAMEPROJECT_API ABronzeArtifactStage : public AActor
{
	GENERATED_BODY()

public:
	ABronzeArtifactStage();

	virtual void Tick(float DeltaSeconds) override;

	UFUNCTION(BlueprintCallable, Category = "Bronze Exhibit|Stage")
	void ApplyPage(const FBronzeExhibitPageRecord& Page);

	UFUNCTION(BlueprintCallable, Category = "Bronze Exhibit|Stage")
	void ClearArtifact();

	UFUNCTION(BlueprintCallable, Category = "Bronze Exhibit|Stage")
	void SetArtifactRotationEnabled(bool bEnabled);

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Bronze Exhibit|Stage")
	TObjectPtr<USceneComponent> StageRoot;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Bronze Exhibit|Stage")
	TObjectPtr<UStaticMeshComponent> ArtifactMesh;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Bronze Exhibit|Stage")
	bool bRotationEnabled = true;

	UPROPERTY(BlueprintReadOnly, Category = "Bronze Exhibit|Stage")
	FName CurrentPageId;

private:
	float CurrentRotationDegreesPerSecond = 0.0f;
};

