#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "UDPComponent.h"
#include "JoystickSR04ReceiverComponent.generated.h"

class AActor;

/** Joystick direction enum (8-directional + center) */
UENUM(BlueprintType)
enum class EJoystickDir : uint8
{
    Center   = 0 UMETA(DisplayName = "Center"),
    Up       = 1 UMETA(DisplayName = "Up"),
    UpRight  = 2 UMETA(DisplayName = "Up-Right"),
    Right    = 3 UMETA(DisplayName = "Right"),
    DownRight= 4 UMETA(DisplayName = "Down-Right"),
    Down     = 5 UMETA(DisplayName = "Down"),
    DownLeft = 6 UMETA(DisplayName = "Down-Left"),
    Left     = 7 UMETA(DisplayName = "Left"),
    UpLeft   = 8 UMETA(DisplayName = "Up-Left")
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_SevenParams(FOnJoystickSR04Data,
    EJoystickDir, JoyDir, float, Distance, bool, bDistanceValid,
    int32, Up, int32, Down, int32, Left, int32, Right);

/**
 * UE5 Joystick + SR04 Ultrasonic UDP Receiver
 * Matches JoystickSR04_FINAL.ino firmware on ESP32
 *
 * Data format: {"type":"sensors","joy":{"up":0,"down":0,"left":0,"right":0,"dir":0},"sr04":{"distance":25.30,"valid":true}}
 *
 * Usage: Add to any Actor, bind OnDataReceived or read properties in Tick
 */
UCLASS(ClassGroup="Sensors", meta=(BlueprintSpawnableComponent))
class MCPGAMEPROJECT_API UJoystickSR04ReceiverComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UJoystickSR04ReceiverComponent();

    // -- Configuration --

    /** ESP32 IP (initial hint, auto-discovered at runtime) */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "JoystickSR04")
    FString ESP32IP = TEXT("192.168.8.112");

    /** UDP port, must match ESP32 sketch (default 4210) */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "JoystickSR04")
    int32 UDPPort = 4210;

    /** Enable GET polling */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "JoystickSR04")
    bool bUsePolling = true;

    /** GET polling interval (seconds) */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "JoystickSR04", meta = (EditCondition = "bUsePolling"))
    float PollInterval = 0.05f;

    /** Connection timeout (seconds) */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "JoystickSR04")
    float ConnectionTimeout = 2.0f;

    /** Move a level actor directly from joystick data. Useful when the separate driver component is not present. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "JoystickSR04|Movement")
    bool bDriveMoveTarget = true;

    /** Actor to move from joystick data. Select this from the placed actor instance in the level. */
    UPROPERTY(EditInstanceOnly, BlueprintReadWrite, Category = "JoystickSR04|Movement", meta = (EditCondition = "bDriveMoveTarget"))
    AActor* MoveTarget = nullptr;

    /** Movement speed in cm/s. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "JoystickSR04|Movement", meta = (EditCondition = "bDriveMoveTarget"))
    float MoveSpeed = 200.0f;

    /** Keep the controlled actor on its starting Z height. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "JoystickSR04|Movement", meta = (EditCondition = "bDriveMoveTarget"))
    bool bLockMoveTargetZ = true;

    // -- Joystick Data (read-only) --

    UPROPERTY(BlueprintReadOnly, Category = "JoystickSR04|Joystick")
    EJoystickDir JoyDirection = EJoystickDir::Center;

    UPROPERTY(BlueprintReadOnly, Category = "JoystickSR04|Joystick")
    int32 JoyUp = 0;

    UPROPERTY(BlueprintReadOnly, Category = "JoystickSR04|Joystick")
    int32 JoyDown = 0;

    UPROPERTY(BlueprintReadOnly, Category = "JoystickSR04|Joystick")
    int32 JoyLeft = 0;

    UPROPERTY(BlueprintReadOnly, Category = "JoystickSR04|Joystick")
    int32 JoyRight = 0;

    // -- SR04 Data (read-only) --

    /** Distance in cm, -1 if invalid */
    UPROPERTY(BlueprintReadOnly, Category = "JoystickSR04|SR04")
    float Distance = -1.0f;

    /** Whether SR04 reading is valid */
    UPROPERTY(BlueprintReadOnly, Category = "JoystickSR04|SR04")
    bool bDistanceValid = false;

    // -- Status --

    UPROPERTY(BlueprintReadOnly, Category = "JoystickSR04|Status")
    bool bIsConnected = false;

    // -- Events --

    /** Fired each time a new sensor frame is received */
    UPROPERTY(BlueprintAssignable, Category = "JoystickSR04|Events")
    FOnJoystickSR04Data OnDataReceived;

    // -- Commands --

    /** Send GET for immediate data */
    UFUNCTION(BlueprintCallable, Category = "JoystickSR04")
    void SendGet();

    /** Send INFO command (returns WiFi/IP/RSSI) */
    UFUNCTION(BlueprintCallable, Category = "JoystickSR04")
    void SendInfo();

    /** Send custom command (WIFI:ssid,pass / WIFICLEAR / SCAN) */
    UFUNCTION(BlueprintCallable, Category = "JoystickSR04")
    void SendCommand(const FString& Command);

protected:
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

private:
    UPROPERTY()
    UUDPComponent* UDPReceiver;

    UPROPERTY()
    UUDPComponent* UDPSender;

    float LastReceiveTime = 0.0f;
    float PollTimer = 0.0f;
    FString DiscoveredIP;
    bool bHasDiscovered = false;
    float LockedMoveTargetZ = 0.0f;

    void SetupUDP();
    void CacheMoveTargetHeight();
    FVector GetJoystickMoveDirection() const;
    bool ParseSensorJson(const FString& Json);

    static EJoystickDir IntToJoyDir(int32 Dir);

    UFUNCTION()
    void HandleReceiveSocketOpened(int32 Port);
    UFUNCTION()
    void HandleReceivedBytes(const TArray<uint8>& Bytes, const FString& IPAddress, const int32& Port);
};
