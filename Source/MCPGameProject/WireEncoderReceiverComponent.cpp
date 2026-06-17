#include "WireEncoderReceiverComponent.h"
#include "Misc/DefaultValueHelper.h"
#include "Engine/World.h"

UWireEncoderReceiverComponent::UWireEncoderReceiverComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.TickInterval = 0.016f; // ~60fps
}

void UWireEncoderReceiverComponent::BeginPlay()
{
    Super::BeginPlay();
    SetupUDP();
}

void UWireEncoderReceiverComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    if (UDPReceiver)
    {
        UDPReceiver->CloseReceiveSocket();
        UDPReceiver = nullptr;
    }
    if (UDPSender)
    {
        UDPSender->CloseSendSocket();
        UDPSender = nullptr;
    }
    Super::EndPlay(EndPlayReason);
}

void UWireEncoderReceiverComponent::SetupUDP()
{
    // Create receiver component - listen on UDP 4210
    UDPReceiver = NewObject<UUDPComponent>(GetOwner());
    if (UDPReceiver)
    {
        UDPReceiver->RegisterComponent();
        UDPReceiver->Settings.ReceiveIP = TEXT("0.0.0.0");
        UDPReceiver->Settings.ReceivePort = UDPPort;
        UDPReceiver->Settings.SendIP = ESP32IP;
        UDPReceiver->Settings.SendPort = UDPPort;
        UDPReceiver->Settings.bShouldAutoOpenReceive = true;
        UDPReceiver->Settings.bShouldAutoOpenSend = false;
        UDPReceiver->Settings.bReceiveDataOnGameThread = true;
        UDPReceiver->Settings.BufferSize = 65536;

        UDPReceiver->OnReceiveSocketOpened.AddDynamic(this, &UWireEncoderReceiverComponent::HandleReceiveSocketOpened);
        UDPReceiver->OnReceivedBytes.AddDynamic(this, &UWireEncoderReceiverComponent::HandleReceivedBytes);

        UE_LOG(LogTemp, Log, TEXT("[WireEncoder] Receiver created, port %d, ESP32=%s"), UDPPort, *ESP32IP);
    }

    // Create sender component for GET polling and commands
    UDPSender = NewObject<UUDPComponent>(GetOwner());
    if (UDPSender)
    {
        UDPSender->RegisterComponent();
        UDPSender->Settings.SendIP = ESP32IP;
        UDPSender->Settings.SendPort = UDPPort;
        UDPSender->Settings.bShouldAutoOpenSend = true;
        UDPSender->Settings.bShouldAutoOpenReceive = false;
        UDPSender->Settings.BufferSize = 4096;

        UE_LOG(LogTemp, Log, TEXT("[WireEncoder] Sender created, target %s:%d"), *ESP32IP, UDPPort);
    }
}

void UWireEncoderReceiverComponent::HandleReceiveSocketOpened(int32 Port)
{
    UE_LOG(LogTemp, Log, TEXT("[WireEncoder] Receive socket opened on port %d"), Port);
}

void UWireEncoderReceiverComponent::HandleReceivedBytes(const TArray<uint8>& Bytes, const FString& IPAddress, const int32& Port)
{
    // Auto-discover: remember device's real IP
    if (!bHasDiscovered || DiscoveredIP != IPAddress)
    {
        DiscoveredIP = IPAddress;
        bHasDiscovered = true;
        if (UDPSender)
        {
            UDPSender->CloseSendSocket();
            UDPSender->Settings.SendIP = IPAddress;
            UDPSender->OpenSendSocket(IPAddress, UDPPort);
        }
        UE_LOG(LogTemp, Log, TEXT("[WireEncoder] Auto-discovered device IP: %s"), *IPAddress);
    }

    // Parse JSON
    FString Json;
    Json.AppendChars((const ANSICHAR*)Bytes.GetData(), Bytes.Num());

    if (ParseJson(Json))
    {
        bIsConnected = true;
        LastReceiveTime = GetWorld()->GetTimeSeconds();
        OnDataReceived.Broadcast(Position, Angle, Velocity, Direction, TotalAngle, Pulse);
    }
}

void UWireEncoderReceiverComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

    if (!GetWorld()) return;

    // Connection timeout
    if (bIsConnected && GetWorld()->GetTimeSeconds() - LastReceiveTime > ConnectionTimeout)
    {
        bIsConnected = false;
        bHasDiscovered = false;
        DiscoveredIP.Empty();
    }

    // GET polling
    if (bUsePolling && UDPReceiver && UDPReceiver->Settings.bIsReceiveOpen)
    {
        PollTimer += DeltaTime;
        if (PollTimer >= PollInterval)
        {
            PollTimer = 0.0f;
            SendGet();
        }
    }
}

void UWireEncoderReceiverComponent::SendGet()
{
    if (UDPSender && UDPSender->Settings.bIsSendOpen)
    {
        FString Cmd = TEXT("GET");
        TArray<uint8> Bytes;
        Bytes.Append((const uint8*)TCHAR_TO_ANSI(*Cmd), Cmd.Len());
        UDPSender->EmitBytes(Bytes);
    }
}

void UWireEncoderReceiverComponent::SendReset()
{
    if (UDPSender && UDPSender->Settings.bIsSendOpen)
    {
        FString Cmd = TEXT("RESET");
        TArray<uint8> Bytes;
        Bytes.Append((const uint8*)TCHAR_TO_ANSI(*Cmd), Cmd.Len());
        UDPSender->EmitBytes(Bytes);
    }
}

void UWireEncoderReceiverComponent::SendCommand(const FString& Command)
{
    if (UDPSender && UDPSender->Settings.bIsSendOpen)
    {
        TArray<uint8> Bytes;
        Bytes.Append((const uint8*)TCHAR_TO_ANSI(*Command), Command.Len());
        UDPSender->EmitBytes(Bytes);
    }
}

bool UWireEncoderReceiverComponent::ParseJson(const FString& Json)
{
    // Quick check: skip scan/info/status response frames
    if (!Json.Contains(TEXT("pulse"))) return false;

    Position = ExtractFloat(Json, TEXT("position"));
    Angle = ExtractFloat(Json, TEXT("angle"));
    Velocity = ExtractFloat(Json, TEXT("velocity"));
    Direction = ExtractInt(Json, TEXT("direction"));
    TotalAngle = ExtractFloat(Json, TEXT("totalAngle"));
    Pulse = ExtractInt64(Json, TEXT("pulse"));

    return true;
}

float UWireEncoderReceiverComponent::ExtractFloat(const FString& Json, const FString& Key) const
{
    FString Search = FString::Printf(TEXT("\"%s\":"), *Key);
    int32 Idx = Json.Find(Search, ESearchCase::IgnoreCase, ESearchDir::FromStart);
    if (Idx == INDEX_NONE)
        return 0.0f;

    Idx += Search.Len();
    while (Idx < Json.Len() && Json[Idx] == ' ')
        Idx++;

    int32 End = Idx;
    while (End < Json.Len() && Json[End] != ',' && Json[End] != '}' && Json[End] != ' ')
        End++;

    FString ValueStr = Json.Mid(Idx, End - Idx);
    return FCString::Atof(*ValueStr);
}

int32 UWireEncoderReceiverComponent::ExtractInt(const FString& Json, const FString& Key) const
{
    return (int32)ExtractFloat(Json, Key);
}

int64 UWireEncoderReceiverComponent::ExtractInt64(const FString& Json, const FString& Key) const
{
    FString Search = FString::Printf(TEXT("\"%s\":"), *Key);
    int32 Idx = Json.Find(Search, ESearchCase::IgnoreCase, ESearchDir::FromStart);
    if (Idx == INDEX_NONE)
        return 0;

    Idx += Search.Len();
    while (Idx < Json.Len() && Json[Idx] == ' ')
        Idx++;

    int32 End = Idx;
    while (End < Json.Len() && Json[End] != ',' && Json[End] != '}' && Json[End] != ' ')
        End++;

    FString ValueStr = Json.Mid(Idx, End - Idx);
    return FCString::Atoi64(*ValueStr);
}
