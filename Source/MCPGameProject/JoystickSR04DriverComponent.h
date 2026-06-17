#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "JoystickSR04ReceiverComponent.h"
#include "JoystickSR04DriverComponent.generated.h"

/**
 * UE5 Joystick + SR04 Driver
 * Maps joystick direction to actor XY movement, SR04 distance to visual feedback
 *
 * Joystick: direction -> actor movement (speed configurable)
 * SR04: distance -> material parameter (e.g. glow/emission) or actor scale
 */
UCLASS(ClassGroup="Sensors", meta=(BlueprintSpawnableComponent))
class MCPGAMEPROJECT_API UJoystickSR04DriverComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UJoystickSR04DriverComponent();

    // -- Data Source --

    /** Actor that owns the JoystickSR04Receiver component. Pick JoySrick_Sro4_BP from the level. */
    UPROPERTY(EditInstanceOnly, BlueprintReadWrite, Category = "JoyDriver|Source")
    AActor* ReceiverActor = nullptr;

    /** Optional direct component reference. Usually leave this empty and set ReceiverActor instead. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "JoyDriver|Source", meta = (UseComponentPicker = "true"))
    UJoystickSR04ReceiverComponent* Receiver;

    // -- Movement Target --

    /** Actor to move. Leave empty to move this component's owner, e.g. Cube. */
    UPROPERTY(EditInstanceOnly, BlueprintReadWrite, Category = "JoyDriver|Movement")
    AActor* MoveTarget;

    /** Movement speed in cm/s */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "JoyDriver|Movement")
    float MoveSpeed = 200.0f;

    /** Movement smoothing time */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "JoyDriver|Movement")
    float MoveSmoothTime = 0.1f;

    /** Keep the controlled actor on its starting Z height so joystick data only moves it across the ground. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "JoyDriver|Movement")
    bool bLockTargetZ = true;

    // -- Distance Visual --

    /** Target mesh for distance-based material parameter */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "JoyDriver|Distance", meta = (UseComponentPicker = "true"))
    UMeshComponent* TargetMesh;

    /** Material parameter name to drive with distance (e.g. "GlowIntensity") */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "JoyDriver|Distance")
    FName DistanceParamName = TEXT("GlowIntensity");

    /** Map distance range [MinDist..MaxDist] -> [0..1] for material param */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "JoyDriver|Distance")
    float MinDistance = 5.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "JoyDriver|Distance")
    float MaxDistance = 100.0f;

    /** Invert: closer = higher value when true */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "JoyDriver|Distance")
    bool bInvertDistance = true;

    // -- Debug (read-only) --

    UPROPERTY(BlueprintReadOnly, Category = "JoyDriver|Debug")
    FVector CurrentVelocity = FVector::ZeroVector;

    UPROPERTY(BlueprintReadOnly, Category = "JoyDriver|Debug")
    float DistanceFraction = 0.0f;

protected:
    virtual void BeginPlay() override;
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

private:
    FVector DesiredDirection = FVector::ZeroVector;
    FVector SmoothedVelocity = FVector::ZeroVector;
    float LockedTargetZ = 0.0f;

    void AutoBindReceiver();
    void AutoBindMoveTarget();

    UFUNCTION()
    void OnSensorDataReceived(EJoystickDir JoyDir, float InDistance, bool bValid,
        int32 Up, int32 Down, int32 Left, int32 Right);
};
