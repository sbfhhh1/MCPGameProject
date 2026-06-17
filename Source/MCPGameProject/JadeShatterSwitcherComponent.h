#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "JadeShatterSwitcherComponent.generated.h"

class UStaticMeshComponent;
class UStaticMesh;
class UMaterialInterface;
class APlayerController;

// 单个碎块运行时数据
USTRUCT()
struct FJadeShardRuntime
{
	GENERATED_BODY()

	UPROPERTY(Transient)
	TObjectPtr<UStaticMeshComponent> Comp = nullptr;

	// 碎块在拼合态时相对玉石中心的位置（归一化+缩放后），涡流路径以此为起点
	FVector RestCentroid = FVector::ZeroVector;

	// 几何偏移 = stateScale × mesh本地质心；SMC相对位置 = 涡流目标 - GeomOffset
	FVector GeomOffset = FVector::ZeroVector;

	// 飞散用的每块随机扰动方向与自旋
	FVector TurbulenceDir = FVector::ZeroVector;
	FRotator SpinPerUnit = FRotator::ZeroRotator;
};

USTRUCT()
struct FJadeShardSet
{
	GENERATED_BODY()

	UPROPERTY(Transient)
	TArray<FJadeShardRuntime> Shards;

	// 每状态的朝向 pivot（复现原版玉石的 roll90+yaw 显示朝向）
	UPROPERTY(Transient)
	TObjectPtr<USceneComponent> Pivot = nullptr;
};

// 玉石“破碎成块→涡流飞散→重组”切换组件。
// 保留 opaque SSS 玉质：靠几何碎块飞散而非材质淡出来做过渡。
UCLASS(ClassGroup=(TransformationVFX), meta=(BlueprintSpawnableComponent))
class MCPGAMEPROJECT_API UJadeShatterSwitcherComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UJadeShatterSwitcherComponent();

	// 三个玉石碎块资产所在目录（jadeA/B/C）
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Jade Shatter|Assets")
	TArray<FString> ShardFolders;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Jade Shatter|Assets")
	TObjectPtr<UMaterialInterface> JadeMaterial;

	// 拼合后玉石的目标高度（世界单位）。每状态自动按其碎块合并包围盒归一化到此高度，
	// 不依赖 FBX 往返的缩放，并自动居中到 actor 原点。
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Jade Shatter|Transform", meta=(ClampMin="1.0"))
	float TargetHeight = 196.0f;

	// 时序
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Jade Shatter|Timing", meta=(ClampMin="0.05"))
	float DisperseDuration = 1.4f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Jade Shatter|Timing", meta=(ClampMin="0.05"))
	float AssembleDuration = 1.6f;

	// 飞散与重组的重叠时长：旧块还在飞、新块已开始聚拢，过渡更连贯
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Jade Shatter|Timing", meta=(ClampMin="0.0"))
	float OverlapDuration = 0.5f;

	// 涡流参数
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Jade Shatter|Vortex")
	FVector VortexAxis = FVector(0,0,1);

	// 径向外扩距离（世界单位）
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Jade Shatter|Vortex")
	float OutwardDistance = 220.0f;

	// 绕轴旋转圈数（飞散全程累计），×2π 弧度
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Jade Shatter|Vortex")
	float SwirlTurns = 1.25f;

	// 沿轴抬升高度（龙卷上升感）
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Jade Shatter|Vortex")
	float LiftHeight = 140.0f;

	// 随机扰动幅度
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Jade Shatter|Vortex")
	float Turbulence = 70.0f;

	// 碎块飞行时自旋总角度（度）
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Jade Shatter|Vortex")
	float SpinDegrees = 540.0f;

	// 飞散曲线指数（>1 先慢后快）
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Jade Shatter|Vortex", meta=(ClampMin="0.1"))
	float EaseExponent = 2.0f;

	// 每状态显示朝向（复现原版玉石 Roll90 + 各自 Yaw）。索引对应 ShardFolders。
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Jade Shatter|Transform")
	TArray<FRotator> StateRotations;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Jade Shatter|State")
	int32 InitialState = 0;

	UFUNCTION(BlueprintCallable, Category="Jade Shatter")
	void SwitchToState(int32 StateIndex);

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

private:
	void BuildShardSets();
	void SetStateVisible(int32 StateIndex, bool bVisible);
	// 计算某块在飞散进度 p(0=拼合,1=完全飞散) 下的相对 location 偏移与额外旋转
	void ApplyShardPose(const FJadeShardRuntime& Shard, float Disperse, FVector& OutRelLoc, FRotator& OutRelRot) const;
	void UpdateStatePose(int32 StateIndex, float Disperse);

	UPROPERTY(Transient)
	TArray<FJadeShardSet> StateSets;

	UPROPERTY(Transient)
	TObjectPtr<APlayerController> PlayerController;

	int32 CurrentState = 0;
	int32 PendingState = INDEX_NONE;

	bool bDispersing = false;   // 旧玉石飞散中
	bool bAssembling = false;   // 新玉石聚拢中
	float DisperseElapsed = 0.0f;
	float AssembleElapsed = 0.0f;
	bool bShardsBuilt = false;
};
