#include "WireEncoderDriverComponent.h"
#include "GameFramework/Actor.h"
#include "Components/SceneComponent.h"

UWireEncoderDriverComponent::UWireEncoderDriverComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.TickInterval = 0.016f;
}

void UWireEncoderDriverComponent::BeginPlay()
{
    Super::BeginPlay();

    if (Receiver)
    {
        Receiver->OnDataReceived.AddDynamic(this, &UWireEncoderDriverComponent::OnEncoderDataReceived);
    }
}

void UWireEncoderDriverComponent::OnEncoderDataReceived(float InPosition, float InAngle, float InVelocity, int32 InDirection, float InTotalAngle, int64 InPulse)
{
    // Data is already stored in Receiver's properties, TickComponent will handle it
}

void UWireEncoderDriverComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

    if (!Receiver || !Receiver->bIsConnected) return;
    if (!MoveTarget) return;

    // Initialize base position
    if (!bInitialized)
    {
        BaseMovePos = MoveTarget->GetActorLocation();
        BaseZ = BaseMovePos.Z; // UE5: Z is up
        PulledZ = bTargetIsAbsolute ? TargetWorldZ : BaseZ + TargetWorldZ;
        if (bInvertDirection) PulledZ = BaseZ - (PulledZ - BaseZ);
        CurrentZ = BaseZ;
        TargetZ = BaseZ;
        bInitialized = true;
        UE_LOG(LogTemp, Log, TEXT("[WireEncoderDriver] Base Z=%.2f, Target Z=%.2f"), BaseZ, PulledZ);
    }

    // Rotation (optional)
    if (RotateTarget != nullptr)
    {
        float A = Receiver->Angle * AngleScale;
        FRotator Rot = RotateTarget->GetRelativeRotation();
        if (bRotateX) Rot.Pitch = A;
        if (bRotateY) Rot.Yaw = A;
        if (bRotateZ) Rot.Roll = A;
        RotateTarget->SetRelativeRotation(Rot);
    }

    // Position mapping
    float RawPos = Receiver->Position;
    float Pos = bUseAbsolutePosition ? FMath::Abs(RawPos) : RawPos;

    float Denom = FMath::IsNearlyZero(PullPositionAtTarget) ? 1.0f : PullPositionAtTarget;
    PulledFraction = FMath::Clamp(Pos / Denom, 0.0f, 1.0f);

    TargetZ = FMath::Lerp(BaseZ, PulledZ, PulledFraction);

    bReleased = Pos <= ReleaseThreshold;

    // Manual SmoothDamp (FMath doesn't have SmoothDamp in UE5)
    float Smooth = (TargetZ > CurrentZ) ? FollowSmoothTime : ResetSmoothTime;
    float Omega = 2.0f / FMath::Max(Smooth, 0.0001f);
    float X = Omega * DeltaTime;
    float Exp = 1.0f / (1.0f + X + 0.48f * X * X + 0.235f * X * X * X);
    float Delta = TargetZ - CurrentZ;
    float MaxDelta = MaxSpeed * Smooth;
    Delta = FMath::Clamp(Delta, -MaxDelta, MaxDelta);
    float NewTarget = CurrentZ + Delta;
    float Temp = (SmoothVelocity + Omega * Delta) * DeltaTime;
    SmoothVelocity = (SmoothVelocity - Omega * Temp) * Exp;
    CurrentZ = NewTarget + (Delta + Temp) * Exp;

    FVector P = MoveTarget->GetActorLocation();
    FVector NewPos(P.X, P.Y, CurrentZ);
    MoveTarget->SetActorLocation(NewPos);
}
