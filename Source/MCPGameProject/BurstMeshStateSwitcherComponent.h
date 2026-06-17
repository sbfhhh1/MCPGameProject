#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "BurstMeshStateSwitcherComponent.generated.h"

class UNiagaraComponent;
class UNiagaraSystem;
class APlayerController;
class UMaterialInstanceDynamic;
class UMaterialInterface;
class UStaticMeshComponent;
struct FLeapFrameData;

UCLASS(ClassGroup=(TransformationVFX), meta=(BlueprintSpawnableComponent))
class MCPGAMEPROJECT_API UBurstMeshStateSwitcherComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UBurstMeshStateSwitcherComponent();

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Burst Switcher|Particles|Materials")
	TArray<TObjectPtr<UMaterialInterface>> StateParticleMaterials;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Burst Switcher|Models")
	TArray<TObjectPtr<UMaterialInterface>> StateFadeMaterials;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Burst Switcher|Models")
	TObjectPtr<UMaterialInterface> FallbackModelFadeMaterial;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Burst Switcher|Timing", meta=(ClampMin="0.1"))
	float FrontHalfDuration = 2.5f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Burst Switcher|Timing", meta=(ClampMin="0.1"))
	float ModelFadeInDuration = 1.5f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Burst Switcher|Timing", meta=(ClampMin="0.0"))
	float SourceHideDelay = 0.08f;

	// 粒子消散与模型淡入的重叠时长：模型淡入会比粒子完全消散提前这么多秒启动，
	// 让粒子淡出尾段与模型淡入重叠，过渡更连贯。设 0 则维持“粒子完全结束后再淡入”。
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Burst Switcher|Timing", meta=(ClampMin="0.0"))
	float ParticleModelOverlapDuration = 0.8f;

	// 旧模型溶解淡出的时长：切换时旧模型用 Dissolve 1->0 渐变消散，而不是瞬间隐藏。
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Burst Switcher|Timing", meta=(ClampMin="0.0"))
	float SourceFadeOutDuration = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Burst Switcher|Particles|Transform", meta=(ClampMin="0.01"))
	float ParticleEffectScale = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Burst Switcher|Particles|Transform", meta=(ClampMin="0.1"))
	float InhalationSpreadScale = 1.75f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Burst Switcher|Particles|Transform")
	FVector ParticleNonUniformScale = FVector::OneVector;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Burst Switcher|Particles|Transform")
	FVector ParticleLocationOffset = FVector::ZeroVector;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Burst Switcher|Particles|Transform")
	FRotator ParticleRotationOffset = FRotator::ZeroRotator;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Burst Switcher|Particles|Motion")
	FVector AttractorPosition = FVector::ZeroVector;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Burst Switcher|Particles|Materials")
	bool bUseStateParticleMaterials = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Burst Switcher|Particles|Materials")
	TObjectPtr<UMaterialInterface> ParticleMaterial;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Burst Switcher|Particles|System")
	TObjectPtr<UNiagaraSystem> ParticleSystem;

	// 网格→网格粒子变形系统（P_Morph_5_SM 风格）：粒子从源网格表面采样、流动重组成目标网格形状。
	// 这是新属性，BP 实例不会覆盖它，因此这里的默认值始终生效，避免旧的 ParticleSystem 覆盖值（NS_Return_SM）干扰。
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Burst Switcher|Particles|System")
	TObjectPtr<UNiagaraSystem> MorphParticleSystem;

	// 是否用下面的值覆盖 P_Morph_5_SM 的内置参数。关闭时完全沿用系统默认外观，最贴近 BP_Morph_SM_5。
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Burst Switcher|Morph")
	bool bOverrideMorphParameters = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Burst Switcher|Morph", meta=(EditCondition="bOverrideMorphParameters"))
	FLinearColor MorphEmissiveColor = FLinearColor(1.0f, 1.0f, 1.0f, 1.0f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Burst Switcher|Morph", meta=(EditCondition="bOverrideMorphParameters"))
	float MorphNoiseForce = 200.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Burst Switcher|Morph", meta=(EditCondition="bOverrideMorphParameters"))
	float MorphSpawnRate = 30000.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Burst Switcher|Morph", meta=(EditCondition="bOverrideMorphParameters"))
	float MorphSpringForce = 30.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Burst Switcher|Particles|System")
	int32 ParticleCurrentMode = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Burst Switcher|Particles|Motion", meta=(ClampMin="0.0", ClampMax="1.0"))
	float InitialTransformationAlpha = 0.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Burst Switcher|Particles|Motion", meta=(ClampMin="0.0", ClampMax="1.0"))
	float FirstHalfEndTransformationAlpha = 0.5f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Burst Switcher|Particles|Motion", meta=(ClampMin="0.1"))
	float TransformationAlphaEaseExponent = 2.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Burst Switcher|Particles|Fade")
	bool bUseNaturalParticleFadeOut = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Burst Switcher|Particles|Fade", meta=(ClampMin="0.0"))
	float ParticleFadeOutDuration = 1.5f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Burst Switcher|Particles|Fade", meta=(ClampMin="0.1"))
	float ParticleFadeOutEaseExponent = 2.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Burst Switcher|Particles|Fade")
	FName ParticleFadeOpacityParameter = TEXT("Fade Opacity");

	// 玉石溶解材质（移植自 M_Chair_Dissolve）语义：Dissolve Amount 1.0=完全显示，0.0=完全溶解消失。
	// 因此模型淡入出现需要从 0.0（不可见）渐变到 1.0（完全显示）。
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Burst Switcher|Model Fade", meta=(ClampMin="0.0", ClampMax="1.0"))
	float ModelFadeStartDissolve = 0.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Burst Switcher|Model Fade", meta=(ClampMin="0.0", ClampMax="1.0"))
	float ModelFadeEndDissolve = 1.0f;

	// ---------------- Leap Motion 挥手手势 ----------------
	// 右手向左摆动 → 模型 ID 反向更新；左手向右挥动 → 模型 ID 正向更新。
	// 通过速度阈值 + 水平分量主导 + 每手冷却 + 过渡期屏蔽四重防抖，避免数据抖动导致模型闪烁切换。
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Burst Switcher|Leap Gesture")
	bool bEnableLeapSwipe = true;

	// 触发挥手所需的最小掌心水平速度（UE 空间 cm/s）。低于此值的微小移动视为抖动并忽略。
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Burst Switcher|Leap Gesture", meta=(ClampMin="1.0"))
	float SwipeVelocityThreshold = 80.0f;

	// 一次挥手触发后，该手的冷却时间（秒）。防止单次挥动在多帧内重复触发，是防闪烁的关键。
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Burst Switcher|Leap Gesture", meta=(ClampMin="0.0"))
	float SwipeCooldownSeconds = 0.8f;

	// 手部跟踪置信度低于此值时忽略，避免跟踪不稳定时误触发。
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Burst Switcher|Leap Gesture", meta=(ClampMin="0.0", ClampMax="1.0"))
	float MinHandConfidence = 0.2f;

	// 若设备安装朝向导致左右方向（Y 轴）相反，勾选此项翻转判定方向。
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Burst Switcher|Leap Gesture")
	bool bInvertSwipeAxis = false;

	// 默认在切换过渡进行中忽略新的挥手，确保模型完整成形后再响应下一次，进一步防闪烁。
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Burst Switcher|Leap Gesture")
	bool bAllowSwipeDuringTransition = false;

	// ---------------- 模型自转 ----------------
	// 模型完整显示时绕竖直轴（世界 Z 轴）从当前角度缓慢自转；隐藏或切换过渡中不转。
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Burst Switcher|Rotation")
	bool bEnableModelRotation = true;

	// 自转速度（度/秒）。正值逆时针、负值顺时针；0 等同关闭。
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Burst Switcher|Rotation")
	float RotationSpeedDegreesPerSecond = 30.0f;

	UFUNCTION(BlueprintCallable, Category="Burst Switcher|Models")
	void SwitchToState(int32 StateIndex);

	// 按方向循环切换模型（+1 正向 / -1 反向），带环绕。
	UFUNCTION(BlueprintCallable, Category="Burst Switcher|Models")
	void CycleModel(int32 Direction);

protected:
	virtual void OnRegister() override;
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

private:
	void CacheOwnerComponents();
	void ApplyInitialStateMaterials();
	void DisableLegacyTriggerAndUI();
	void SetRuntimeStateVisibility(int32 VisibleStateIndex);
	void ApplyParticleSettings();
	void ApplyMorphParameters();
	void SetTransformationAlpha(float Alpha);
	UMaterialInterface* ResolveParticleMaterial() const;
	void HideSourceMesh();
	void BeginSourceFadeOut();
	void BeginModelReveal();
	void FinishParticlesAndRevealTarget();
	void BeginTargetModelFadeIn();
	void BeginParticleFadeOut();
	void StopAndHideParticles();
	void CompleteTransition();
	void SwitchToStateOne();
	void SwitchToStateTwo();
	void SwitchToStateThree();
	void PollLeapSwipeGestures(float DeltaTime);
	void UpdateModelRotation(float DeltaTime);
	bool IsTransitionInProgress() const;
	// 判定掌心速度是否构成一次有效的水平挥手（阈值 + 水平分量主导）。
	bool IsLateralSwipe(const FVector& Velocity) const;
	// Leap 帧回调（游戏线程）：仅缓存左右手掌心速度/置信度，实际判定放在 Tick 中按 DeltaTime 走冷却。
	void OnLeapTrackingData(const FLeapFrameData& Frame);

	UPROPERTY(Transient)
	TObjectPtr<UStaticMeshComponent> SourceMeshComponent;

	UPROPERTY(Transient)
	TObjectPtr<UStaticMeshComponent> TargetMeshComponent;

	UPROPERTY(Transient)
	TArray<TObjectPtr<UStaticMeshComponent>> StateMeshComponents;

	UPROPERTY(Transient)
	TObjectPtr<UNiagaraComponent> TransformationNiagara;

	UPROPERTY(Transient)
	TObjectPtr<APlayerController> PlayerController;

	UPROPERTY(Transient)
	TArray<TObjectPtr<UMaterialInstanceDynamic>> ActiveFadeMaterials;

	UPROPERTY(Transient)
	TArray<TObjectPtr<UMaterialInstanceDynamic>> ActiveSourceFadeMaterials;

	UPROPERTY(Transient)
	TObjectPtr<UMaterialInstanceDynamic> ActiveParticleMaterial;

	FVector NiagaraBaseLocation = FVector::ZeroVector;
	FVector NiagaraBaseScale = FVector::OneVector;
	FRotator NiagaraBaseRotation = FRotator::ZeroRotator;
	int32 CurrentStateIndex = 0;
	int32 PendingStateIndex = INDEX_NONE;
	float TransitionElapsed = 0.0f;
	float ActiveTransitionDuration = 1.0f;
	float FadeInElapsed = 0.0f;
	float SourceFadeOutElapsed = 0.0f;
	bool bSourceFadeOutActive = false;
	float ParticleFadeOutElapsed = 0.0f;
	bool bTransitionActive = false;
	bool bFadeInActive = false;
	bool bFadeRevealPending = false;
	bool bParticleFadeOutActive = false;
	bool bInitialStateMaterialsApplied = false;
	FTimerHandle HideSourceTimer;
	FTimerHandle BeginRevealTimer;
	FTimerHandle ParticleFadeOutTimer;

	// 每手挥手冷却剩余时间（秒），左右手独立计时。
	float LeftHandSwipeCooldown = 0.0f;
	float RightHandSwipeCooldown = 0.0f;

	// Leap 帧回调缓存的最新手部数据（游戏线程写入，Tick 读取）。
	FVector LeftPalmVelocity = FVector::ZeroVector;
	FVector RightPalmVelocity = FVector::ZeroVector;
	float LeftHandConfidence = 0.0f;
	float RightHandConfidence = 0.0f;
	bool bLeftHandPresent = false;
	bool bRightHandPresent = false;
	float TimeSinceLeapFrame = 1000.0f;
	FDelegateHandle LeapFrameDelegateHandle;
};
