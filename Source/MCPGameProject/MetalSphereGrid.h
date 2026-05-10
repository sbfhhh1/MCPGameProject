#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "MetalSphereGrid.generated.h"

UCLASS(Blueprintable, meta=(DisplayName="Metal Sphere Grid"))
class MCPGAMEPROJECT_API AMetalSphereGrid : public AActor
{
    GENERATED_BODY()

public:
    AMetalSphereGrid();

    // ---- 网格参数 ----

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Grid", meta = (ClampMin = "1", ClampMax = "50"))
    int32 GridCountX = 10;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Grid", meta = (ClampMin = "1", ClampMax = "50"))
    int32 GridCountY = 10;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Grid", meta = (ClampMin = "10", ClampMax = "5000"))
    float Spacing = 200.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Grid", meta = (ClampMin = "0.1", ClampMax = "100"))
    float SphereScale = 0.8f;

    // ---- 动画参数 ----

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Animation")
    bool bEnableAnimation = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Animation", meta = (ClampMin = "0", ClampMax = "10"))
    float AnimationSpeed = 2.0f;

    /** 波浪幅度（球体上下浮动范围） */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Animation", meta = (ClampMin = "0", ClampMax = "1000"))
    float WaveAmplitude = 150.0f;

    /** 波浪频率 */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Animation", meta = (ClampMin = "0", ClampMax = "5"))
    float WaveFrequency = 0.5f;

    /** 第二层波浪频率（产生更复杂的波纹） */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Animation", meta = (ClampMin = "0", ClampMax = "5"))
    float WaveFrequencyB = 1.3f;

    /** 噪声强度（让波动更自然） */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Animation", meta = (ClampMin = "0", ClampMax = "200"))
    float NoiseStrength = 30.0f;

    // ---- 颜色参数 ----

    /** 主色 A（低处） */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Colors")
    FLinearColor ColorLow = FLinearColor(0.05f, 0.1f, 0.3f);

    /** 主色 B（中间） */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Colors")
    FLinearColor ColorMid = FLinearColor(0.8f, 0.2f, 0.4f);

    /** 主色 C（高处） */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Colors")
    FLinearColor ColorHigh = FLinearColor(1.0f, 0.6f, 0.1f);

    /** 颜色偏移速度 */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Colors", meta = (ClampMin = "0", ClampMax = "5"))
    float ColorShiftSpeed = 0.5f;

    // ---- 组件 ----

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
    UInstancedStaticMeshComponent* InstancedMesh;

    /** 第二个发光网格（可选择添加子光晕） */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
    UInstancedStaticMeshComponent* GlowMesh;

    /** 底部光柱网格 */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
    UInstancedStaticMeshComponent* PillarMesh;

    virtual void Tick(float DeltaTime) override;

protected:
    virtual void OnConstruction(const FTransform& Transform) override;
    virtual void BeginPlay() override;

private:
    void RebuildGrid();
    void UpdateAnimation(float Time);
    FLinearColor GetColorForHeight(float NormalizedHeight, float Time) const;
    float GetWaveHeight(int32 X, int32 Y, float Time) const;

    TArray<FTransform> BaseTransforms;
    float RunningTime = 0.0f;
};
