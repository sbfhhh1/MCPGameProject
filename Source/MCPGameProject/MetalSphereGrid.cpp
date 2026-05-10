#include "MetalSphereGrid.h"
#include "UObject/ConstructorHelpers.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Engine/World.h"

AMetalSphereGrid::AMetalSphereGrid()
{
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.TickInterval = 0.0f;

    // ---- 主网格（球体） ----
    InstancedMesh = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("InstancedMesh"));
    RootComponent = InstancedMesh;

    static ConstructorHelpers::FObjectFinder<UStaticMesh> SphereMesh(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
    if (SphereMesh.Succeeded())
    {
        InstancedMesh->SetStaticMesh(SphereMesh.Object);
    }

    // 使用 DefaultLitMaterial 获得完整光照响应
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> MainMat(TEXT("/Engine/EngineMaterials/DefaultLitMaterial.DefaultLitMaterial"));
    if (MainMat.Succeeded())
    {
        InstancedMesh->SetMaterial(0, MainMat.Object);
    }

    InstancedMesh->SetCollisionProfileName(TEXT("NoCollision"));
    InstancedMesh->SetCastShadow(true);

    // ---- 光晕网格（略大半透明，模拟发光光晕） ----
    GlowMesh = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("GlowMesh"));
    GlowMesh->SetupAttachment(RootComponent);
    if (SphereMesh.Succeeded())
    {
        GlowMesh->SetStaticMesh(SphereMesh.Object);
    }
    // 光晕使用半透明材质
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> GlowMatRef(TEXT("/Engine/EngineMaterials/DefaultLitMaterial.DefaultLitMaterial"));
    if (GlowMatRef.Succeeded())
    {
        GlowMesh->SetMaterial(0, GlowMatRef.Object);
    }
    GlowMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    GlowMesh->SetCastShadow(false);

    // ---- 底部光柱 ----
    static ConstructorHelpers::FObjectFinder<UStaticMesh> CylinderMesh(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
    PillarMesh = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("PillarMesh"));
    PillarMesh->SetupAttachment(RootComponent);
    if (CylinderMesh.Succeeded())
    {
        PillarMesh->SetStaticMesh(CylinderMesh.Object);
    }
    if (MainMat.Succeeded())
    {
        PillarMesh->SetMaterial(0, MainMat.Object);
    }
    PillarMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    PillarMesh->SetCastShadow(false);
    PillarMesh->SetVisibility(true); // 启用光柱增强视觉效果
}

void AMetalSphereGrid::OnConstruction(const FTransform& Transform)
{
    Super::OnConstruction(Transform);
    RebuildGrid();
}

void AMetalSphereGrid::BeginPlay()
{
    Super::BeginPlay();
    RunningTime = 0.0f;
}

void AMetalSphereGrid::Tick(float DeltaTime)
{
    Super::Tick(DeltaTime);

    if (!bEnableAnimation)
        return;

    RunningTime += DeltaTime * AnimationSpeed;
    UpdateAnimation(RunningTime);
}

void AMetalSphereGrid::RebuildGrid()
{
    if (!InstancedMesh || !InstancedMesh->GetStaticMesh())
        return;

    // 清空
    InstancedMesh->ClearInstances();
    GlowMesh->ClearInstances();
    PillarMesh->ClearInstances();
    BaseTransforms.Empty();

    // 创建动态材质
    UMaterialInstanceDynamic* DynMaterial = nullptr;
    if (InstancedMesh->GetMaterial(0))
    {
        DynMaterial = UMaterialInstanceDynamic::Create(InstancedMesh->GetMaterial(0), this);
        if (DynMaterial)
        {
            InstancedMesh->SetMaterial(0, DynMaterial);
        }
    }

    // 光晕材质（半透明）
    UMaterialInstanceDynamic* GlowMaterial = nullptr;
    if (GlowMesh->GetMaterial(0))
    {
        GlowMaterial = UMaterialInstanceDynamic::Create(GlowMesh->GetMaterial(0), this);
        if (GlowMaterial)
        {
            GlowMesh->SetMaterial(0, GlowMaterial);
        }
    }

    // 计算居中偏移
    const float OffsetX = (GridCountX - 1) * Spacing * 0.5f;
    const float OffsetY = (GridCountY - 1) * Spacing * 0.5f;

    // 生成网格
    for (int32 Y = 0; Y < GridCountY; ++Y)
    {
        for (int32 X = 0; X < GridCountX; ++X)
        {
            FVector Location(
                X * Spacing - OffsetX,
                Y * Spacing - OffsetY,
                0.0f
            );

            FTransform InstanceTransform(FQuat::Identity, Location, FVector(SphereScale));
            InstancedMesh->AddInstance(InstanceTransform, true);
            BaseTransforms.Add(InstanceTransform);

            // 光晕（略大，半透明效果在材质中控制）
            FTransform GlowTransform(FQuat::Identity, Location, FVector(SphereScale * 1.3f));
            GlowMesh->AddInstance(GlowTransform, true);

            // 底部光柱
            FTransform PillarTransform(
                FQuat(FRotator(0, 0, 0)),
                Location + FVector(0, 0, -150.0f),
                FVector(0.1f, 0.1f, 3.0f)
            );
            PillarMesh->AddInstance(PillarTransform, true);
        }
    }

    // 如果有材质，设置初始颜色
    if (DynMaterial)
    {
        DynMaterial->SetVectorParameterValue(TEXT("BaseColor"), ColorLow);
        DynMaterial->SetScalarParameterValue(TEXT("Metallic"), 0.8f);
        DynMaterial->SetScalarParameterValue(TEXT("Roughness"), 0.2f);
    }
    if (GlowMaterial)
    {
        GlowMaterial->SetVectorParameterValue(TEXT("BaseColor"), ColorMid);
        // 尝试设置透明度 - BasicShapeMaterial 不支持的话会忽略
        GlowMaterial->SetScalarParameterValue(TEXT("Opacity"), 0.15f);
    }
}

void AMetalSphereGrid::UpdateAnimation(float Time)
{
    if (BaseTransforms.Num() == 0)
        return;

    // 获取材质
    UMaterialInstanceDynamic* DynMaterial = Cast<UMaterialInstanceDynamic>(InstancedMesh->GetMaterial(0));
    UMaterialInstanceDynamic* GlowMaterial = Cast<UMaterialInstanceDynamic>(GlowMesh->GetMaterial(0));

    int32 Index = 0;
    float MaxHeight = 0.0f;

    for (int32 Y = 0; Y < GridCountY; ++Y)
    {
        for (int32 X = 0; X < GridCountX; ++X)
        {
            if (Index >= BaseTransforms.Num())
                break;

            float Height = GetWaveHeight(X, Y, Time);
            MaxHeight = FMath::Max(MaxHeight, Height);

            FTransform BaseTransform = BaseTransforms[Index];
            FVector Location = BaseTransform.GetLocation();
            Location.Z = Height;
            BaseTransform.SetLocation(Location);
            InstancedMesh->UpdateInstanceTransform(Index, BaseTransform, false, false, false);

            // 更新光晕位置跟随
            FTransform GlowTransform = BaseTransform;
            GlowTransform.SetScale3D(FVector(SphereScale * 1.3f));
            GlowMesh->UpdateInstanceTransform(Index, GlowTransform, false, false, false);

            // 更新光柱高度跟随
            float PillarHeight = FMath::Max(Height + 150.0f, 0.0f);
            FTransform PillarTransform(
                FQuat(FRotator(0, 0, 0)),
                Location + FVector(0, 0, -PillarHeight * 0.5f),
                FVector(0.08f, 0.08f, PillarHeight / 100.0f)
            );
            PillarMesh->UpdateInstanceTransform(Index, PillarTransform, false, false, false);

            ++Index;
        }
    }

    // 批量更新变换
    InstancedMesh->MarkRenderStateDirty();
    GlowMesh->MarkRenderStateDirty();
    PillarMesh->MarkRenderStateDirty();

    // 更新颜色 - 颜色随时间在色相环上偏移
    if (DynMaterial)
    {
        float ColorHue = FMath::Frac(Time * ColorShiftSpeed * 0.05f);
        FLinearColor GlowColor = FLinearColor::MakeFromHSV8(ColorHue * 255.0f, 200, 200);
        DynMaterial->SetVectorParameterValue(TEXT("BaseColor"), GlowColor);
        DynMaterial->SetScalarParameterValue(TEXT("Metallic"), 0.8f);
        DynMaterial->SetScalarParameterValue(TEXT("Roughness"), 0.15f);

        // 尝试设置自发光色（如果材质支持）
        DynMaterial->SetVectorParameterValue(TEXT("EmissiveColor"), GlowColor * 0.3f);
    }
    if (GlowMaterial)
    {
        float GlowHue = FMath::Frac(Time * ColorShiftSpeed * 0.05f + 0.5f);
        FLinearColor GlowColor = FLinearColor::MakeFromHSV8(GlowHue * 255.0f, 180, 255);
        GlowMaterial->SetVectorParameterValue(TEXT("BaseColor"), GlowColor);

        // 尝试设置自发光
        GlowMaterial->SetVectorParameterValue(TEXT("EmissiveColor"), GlowColor * 0.6f);
    }
}

float AMetalSphereGrid::GetWaveHeight(int32 X, int32 Y, float Time) const
{
    // 使用多层正弦波产生丰富的水波纹效果
    float DistFromCenter = FMath::Sqrt(
        FMath::Square(X - (GridCountX - 1) * 0.5f) +
        FMath::Square(Y - (GridCountY - 1) * 0.5f)
    );

    // 主波 - 向外扩散的波纹
    float Wave1 = FMath::Sin(DistFromCenter * WaveFrequency * 0.5f - Time * 2.0f) * WaveAmplitude;

    // 第二层波 - X/Y 方向交叉波
    float Wave2 = FMath::Sin(X * WaveFrequency + Time * 1.5f) * 0.6f +
                  FMath::Cos(Y * WaveFrequencyB + Time * 1.8f) * 0.6f;
    Wave2 *= WaveAmplitude * 0.7f;

    // 第三层 - 对角线方向波
    float Wave3 = FMath::Sin((X + Y) * 0.8f + Time * 2.5f) +
                  FMath::Cos((X - Y) * 0.6f + Time * 1.2f);
    Wave3 *= WaveAmplitude * 0.4f;

    // 噪声层 - 使用伪随机噪点
    float Noise = FMath::PerlinNoise2D(FVector2D(X * 0.3f + Time * 0.5f, Y * 0.3f + Time * 0.5f));
    Noise *= NoiseStrength;

    float Height = Wave1 + Wave2 + Wave3 + Noise;

    // 确保最低不低于水平面
    return FMath::Max(Height, 0.0f);
}

FLinearColor AMetalSphereGrid::GetColorForHeight(float NormalizedHeight, float Time) const
{
    // 基于高度混合颜色
    float Shift = FMath::Sin(Time * ColorShiftSpeed) * 0.1f;

    if (NormalizedHeight < 0.33f)
    {
        float T = NormalizedHeight / 0.33f;
        return FMath::Lerp(ColorLow, ColorMid, T + Shift);
    }
    else if (NormalizedHeight < 0.66f)
    {
        float T = (NormalizedHeight - 0.33f) / 0.33f;
        return FMath::Lerp(ColorMid, ColorHigh, T + Shift);
    }
    else
    {
        return ColorHigh;
    }
}
