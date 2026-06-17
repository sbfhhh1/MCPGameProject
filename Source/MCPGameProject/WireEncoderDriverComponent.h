#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "WireEncoderReceiverComponent.h"
#include "WireEncoderDriverComponent.generated.h"

/**
 * UE5 WireEncoder Driver - maps encoder position to actor transform
 * Corresponds to Unity's WireEncoderDriver: pull wire -> platform vertical motion
 *
 * Calibration: In Play mode, pull wire to target travel, read Receiver->Position,
 * fill into PullPositionAtTarget.
 */
UCLASS(ClassGroup="Sensors", meta=(BlueprintSpawnableComponent))
class MCPGAMEPROJECT_API UWireEncoderDriverComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UWireEncoderDriverComponent();

    // -- Data Source --

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WireEncoder|Source", meta = (UseComponentPicker = "true"))
    UWireEncoderReceiverComponent* Receiver;

    // -- Motion Target --

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WireEncoder|Motion", meta = (UseComponentPicker = "true"))
    AActor* MoveTarget;

    // -- Rotation Target (optional) --

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WireEncoder|Rotation", meta = (UseComponentPicker = "true"))
    USceneComponent* RotateTarget;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WireEncoder|Rotation")
    float AngleScale = 1.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WireEncoder|Rotation")
    bool bRotateX = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WireEncoder|Rotation")
    bool bRotateY = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WireEncoder|Rotation")
    bool bRotateZ = false;

    // -- Travel Calibration --

    /** Encoder position reading when wire is pulled to target travel.
     *  Calibration: Play mode -> pull wire to 1/3 travel -> read Receiver.Position -> fill here. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WireEncoder|Calibration")
    float PullPositionAtTarget = 100.0f;

    /** World Z coordinate the platform should reach at target travel */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WireEncoder|Calibration")
    float TargetWorldZ = -10.0f;

    /** Position below this threshold = released, platform starts resetting */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WireEncoder|Calibration")
    float ReleaseThreshold = 2.0f;

    /** Use absolute value of position (enable if pull makes position negative) */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WireEncoder|Calibration")
    bool bUseAbsolutePosition = true;

    /** Flip direction: mirror target around base position */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WireEncoder|Calibration")
    bool bInvertDirection = false;

    /** Treat TargetWorldZ as absolute world coordinate; false = relative offset from base */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WireEncoder|Calibration")
    bool bTargetIsAbsolute = true;

    // -- Range Clamping --

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WireEncoder|Smoothing")
    bool bClampToRange = true;

    // -- Smoothing --

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WireEncoder|Smoothing")
    float FollowSmoothTime = 0.08f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WireEncoder|Smoothing")
    float ResetSmoothTime = 0.25f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WireEncoder|Smoothing")
    float MaxSpeed = 50.0f;

    // -- Debug (read-only) --

    UPROPERTY(BlueprintReadOnly, Category = "WireEncoder|Debug")
    bool bReleased = true;

    UPROPERTY(BlueprintReadOnly, Category = "WireEncoder|Debug")
    float PulledFraction = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "WireEncoder|Debug")
    float TargetZ = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "WireEncoder|Debug")
    float CurrentZ = 0.0f;

protected:
    virtual void BeginPlay() override;
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

private:
    FVector BaseMovePos;
    float BaseZ = 0.0f;
    float PulledZ = 0.0f;
    float SmoothVelocity = 0.0f;
    bool bInitialized = false;

    UFUNCTION()
    void OnEncoderDataReceived(float InPosition, float InAngle, float InVelocity, int32 InDirection, float InTotalAngle, int64 InPulse);
};
