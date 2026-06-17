#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "UDPComponent.h"
#include "WireEncoderReceiverComponent.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_SixParams(FOnWireEncoderData, float, Position, float, Angle, float, Velocity, int32, Direction, float, TotalAngle, int64, Pulse);

/**
 * UE5 Wire Rotary Encoder UDP Receiver
 * Matches Unity's WireEncoderReceiver - listens on ESP32 UDP port 4210
 *
 * Data format: {"pulse":1234,"angle":45.0,"velocity":30.0,"direction":1,"totalAngle":1350.0,"position":337.5,"pinA":1,"pinB":0}
 *
 * Usage: Add to any Actor, set ESP32 IP, bind OnDataReceived event
 */
UCLASS(ClassGroup="Sensors", meta=(BlueprintSpawnableComponent))
class MCPGAMEPROJECT_API UWireEncoderReceiverComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UWireEncoderReceiverComponent();

    /** ESP32 IP address (initial, will be overridden by auto-discovery) */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WireEncoder")
    FString ESP32IP = TEXT("192.168.8.112");

    /** UDP port, must match ESP32 sketch */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WireEncoder")
    int32 UDPPort = 4210;

    /** Enable GET polling (supplements ESP32 broadcast) */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WireEncoder")
    bool bUsePolling = true;

    /** GET polling interval in seconds */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WireEncoder", meta = (EditCondition = "bUsePolling"))
    float PollInterval = 0.05f;

    /** Connection timeout in seconds */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WireEncoder")
    float ConnectionTimeout = 2.0f;

    // -- Runtime Data (read-only) --

    UPROPERTY(BlueprintReadOnly, Category = "WireEncoder|Data")
    float Position = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "WireEncoder|Data")
    float Angle = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "WireEncoder|Data")
    float Velocity = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "WireEncoder|Data")
    int32 Direction = 0;

    UPROPERTY(BlueprintReadOnly, Category = "WireEncoder|Data")
    float TotalAngle = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "WireEncoder|Data")
    int64 Pulse = 0;

    UPROPERTY(BlueprintReadOnly, Category = "WireEncoder|Status")
    bool bIsConnected = false;

    // -- Events --

    /** Fired each time a new data frame is received */
    UPROPERTY(BlueprintAssignable, Category = "WireEncoder|Events")
    FOnWireEncoderData OnDataReceived;

    // -- Public Methods --

    /** Send GET command to ESP32 for immediate data */
    UFUNCTION(BlueprintCallable, Category = "WireEncoder")
    void SendGet();

    /** Send RESET command to ESP32 to zero the encoder */
    UFUNCTION(BlueprintCallable, Category = "WireEncoder")
    void SendReset();

    /** Send custom command to ESP32 */
    UFUNCTION(BlueprintCallable, Category = "WireEncoder")
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

    void SetupUDP();
    bool ParseJson(const FString& Json);
    float ExtractFloat(const FString& Json, const FString& Key) const;
    int32 ExtractInt(const FString& Json, const FString& Key) const;
    int64 ExtractInt64(const FString& Json, const FString& Key) const;

    UFUNCTION()
    void HandleReceiveSocketOpened(int32 Port);
    UFUNCTION()
    void HandleReceivedBytes(const TArray<uint8>& Bytes, const FString& IPAddress, const int32& Port);
};
