#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "UpwardMeshStateSwitcherComponent.generated.h"

class UNiagaraComponent;
class UMaterialInstanceDynamic;
class UMaterialInterface;
class UStaticMesh;
class UStaticMeshComponent;

UCLASS(ClassGroup=(TransformationVFX), meta=(BlueprintSpawnableComponent))
class MCPGAMEPROJECT_API UUpwardMeshStateSwitcherComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UUpwardMeshStateSwitcherComponent();

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Model States")
	TArray<TObjectPtr<UStaticMesh>> StateMeshes;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Model States", meta=(ClampMin="0.1"))
	float TransitionDuration = 2.0f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Model States", meta=(ClampMin="0.0"))
	float SourceHideDelay = 0.12f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Model States", meta=(ClampMin="0.1"))
	float FadeInDuration = 2.0f;

	UFUNCTION(BlueprintCallable, Category="Model States")
	void SwitchToState(int32 StateIndex);

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

private:
	void BindNumberKeys();
	void CacheOwnerComponents();
	void DisableLegacyOverlapTrigger();
	void HideSourceMesh();
	void StopParticleSpawning();
	void FinishTransition();
	void BeginModelFadeIn();
	void CompleteModelFadeIn();
	void SwitchToStateOne();
	void SwitchToStateTwo();
	void SwitchToStateThree();

	UPROPERTY(Transient)
	TObjectPtr<UStaticMeshComponent> SourceMeshComponent;

	UPROPERTY(Transient)
	TObjectPtr<UStaticMeshComponent> TargetMeshComponent;

	UPROPERTY(Transient)
	TObjectPtr<UNiagaraComponent> TransformationNiagara;

	UPROPERTY(Transient)
	TObjectPtr<UMaterialInstanceDynamic> ActiveFadeMaterial;

	UPROPERTY(Transient)
	TArray<TObjectPtr<UMaterialInterface>> StateFadeMaterials;

	int32 CurrentStateIndex = 0;
	int32 PendingStateIndex = INDEX_NONE;
	float FadeInElapsed = 0.0f;
	FVector ModelFullScale = FVector::OneVector;
	bool bFadeInActive = false;
	bool bFadeRevealPending = false;
	FTimerHandle HideSourceTimer;
	FTimerHandle StopParticleSpawningTimer;
	FTimerHandle FinishTransitionTimer;
};
