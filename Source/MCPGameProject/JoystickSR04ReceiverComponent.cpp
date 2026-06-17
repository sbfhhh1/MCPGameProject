#include "JoystickSR04ReceiverComponent.h"
#include "Containers/StringConv.h"
#include "Dom/JsonObject.h"
#include "Engine/World.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

UJoystickSR04ReceiverComponent::UJoystickSR04ReceiverComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.TickInterval = 0.016f;
}

EJoystickDir UJoystickSR04ReceiverComponent::IntToJoyDir(int32 Dir)
{
    if (Dir >= 0 && Dir <= 8)
        return static_cast<EJoystickDir>(Dir);
    return EJoystickDir::Center;
}

void UJoystickSR04ReceiverComponent::BeginPlay()
{
    Super::BeginPlay();
    SetupUDP();
    CacheMoveTargetHeight();
}

void UJoystickSR04ReceiverComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
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

void UJoystickSR04ReceiverComponent::SetupUDP()
{
    UDPReceiver = NewObject<UUDPComponent>(GetOwner());
    if (UDPReceiver)
    {
        UDPReceiver->Settings.ReceiveIP = TEXT("0.0.0.0");
        UDPReceiver->Settings.ReceivePort = UDPPort;
        UDPReceiver->Settings.SendIP = ESP32IP;
        UDPReceiver->Settings.SendPort = UDPPort;
        UDPReceiver->Settings.bShouldAutoOpenReceive = true;
        UDPReceiver->Settings.bShouldAutoOpenSend = false;
        UDPReceiver->Settings.bReceiveDataOnGameThread = true;
        UDPReceiver->Settings.BufferSize = 65536;

        UDPReceiver->OnReceiveSocketOpened.AddDynamic(this, &UJoystickSR04ReceiverComponent::HandleReceiveSocketOpened);
        UDPReceiver->OnReceivedBytes.AddDynamic(this, &UJoystickSR04ReceiverComponent::HandleReceivedBytes);

        UDPReceiver->RegisterComponent();
        if (!UDPReceiver->Settings.bIsReceiveOpen)
        {
            UDPReceiver->OpenReceiveSocket(UDPReceiver->Settings.ReceiveIP, UDPReceiver->Settings.ReceivePort);
        }

        UE_LOG(LogTemp, Log, TEXT("[JoystickSR04] Receiver created, port %d, ESP32=%s"), UDPPort, *ESP32IP);
    }

    UDPSender = NewObject<UUDPComponent>(GetOwner());
    if (UDPSender)
    {
        UDPSender->Settings.SendIP = ESP32IP;
        UDPSender->Settings.SendPort = UDPPort;
        UDPSender->Settings.bShouldAutoOpenSend = true;
        UDPSender->Settings.bShouldAutoOpenReceive = false;
        UDPSender->Settings.BufferSize = 4096;

        UDPSender->RegisterComponent();
        if (!UDPSender->Settings.bIsSendOpen)
        {
            UDPSender->OpenSendSocket(UDPSender->Settings.SendIP, UDPSender->Settings.SendPort);
        }

        UE_LOG(LogTemp, Log, TEXT("[JoystickSR04] Sender created, target %s:%d"), *ESP32IP, UDPPort);
    }
}

void UJoystickSR04ReceiverComponent::CacheMoveTargetHeight()
{
    if (!bDriveMoveTarget)
    {
        return;
    }

    if (MoveTarget)
    {
        LockedMoveTargetZ = MoveTarget->GetActorLocation().Z;
        UE_LOG(LogTemp, Log, TEXT("[JoystickSR04] Move target selected: %s"), *MoveTarget->GetName());
        return;
    }

    UE_LOG(LogTemp, Warning, TEXT("[JoystickSR04] MoveTarget is not set. Select Cube in the placed receiver component details."));
}

FVector UJoystickSR04ReceiverComponent::GetJoystickMoveDirection() const
{
    switch (JoyDirection)
    {
    case EJoystickDir::Up:        return FVector(1, 0, 0);
    case EJoystickDir::UpRight:   return FVector(1, 1, 0).GetSafeNormal();
    case EJoystickDir::Right:     return FVector(0, 1, 0);
    case EJoystickDir::DownRight: return FVector(-1, 1, 0).GetSafeNormal();
    case EJoystickDir::Down:      return FVector(-1, 0, 0);
    case EJoystickDir::DownLeft:  return FVector(-1, -1, 0).GetSafeNormal();
    case EJoystickDir::Left:      return FVector(0, -1, 0);
    case EJoystickDir::UpLeft:    return FVector(1, -1, 0).GetSafeNormal();
    default:                      return FVector::ZeroVector;
    }
}

void UJoystickSR04ReceiverComponent::HandleReceiveSocketOpened(int32 Port)
{
    UE_LOG(LogTemp, Log, TEXT("[JoystickSR04] Receive socket opened on port %d"), Port);
}

void UJoystickSR04ReceiverComponent::HandleReceivedBytes(const TArray<uint8>& Bytes, const FString& IPAddress, const int32& Port)
{
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
        UE_LOG(LogTemp, Log, TEXT("[JoystickSR04] Auto-discovered device IP: %s"), *IPAddress);
    }

    FUTF8ToTCHAR Converted(reinterpret_cast<const ANSICHAR*>(Bytes.GetData()), Bytes.Num());
    FString Json(Converted.Get(), Converted.Length());
    Json.TrimStartAndEndInline();

    const int32 JsonStart = Json.Find(TEXT("{\"type\""), ESearchCase::IgnoreCase);
    if (JsonStart > 0)
    {
        Json.RightChopInline(JsonStart);
    }

    int32 BraceDepth = 0;
    int32 JsonEnd = INDEX_NONE;
    for (int32 Index = 0; Index < Json.Len(); ++Index)
    {
        if (Json[Index] == TEXT('{'))
        {
            ++BraceDepth;
        }
        else if (Json[Index] == TEXT('}'))
        {
            --BraceDepth;
            if (BraceDepth == 0)
            {
                JsonEnd = Index + 1;
                break;
            }
        }
    }

    if (JsonEnd > 0 && JsonEnd < Json.Len())
    {
        Json.LeftInline(JsonEnd);
    }

    if (JsonEnd > 0 && ParseSensorJson(Json))
    {
        bIsConnected = true;
        LastReceiveTime = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.0f;
        OnDataReceived.Broadcast(JoyDirection, Distance, bDistanceValid, JoyUp, JoyDown, JoyLeft, JoyRight);
    }
}

void UJoystickSR04ReceiverComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

    if (!GetWorld()) return;

    if (bIsConnected && GetWorld()->GetTimeSeconds() - LastReceiveTime > ConnectionTimeout)
    {
        bIsConnected = false;
        bHasDiscovered = false;
        DiscoveredIP.Empty();
    }

    if (bUsePolling && UDPReceiver && UDPReceiver->Settings.bIsReceiveOpen)
    {
        PollTimer += DeltaTime;
        if (PollTimer >= PollInterval)
        {
            PollTimer = 0.0f;
            SendGet();
        }
    }

    if (bDriveMoveTarget && bIsConnected)
    {
        if (MoveTarget)
        {
            FVector NewLocation = MoveTarget->GetActorLocation() + GetJoystickMoveDirection() * MoveSpeed * DeltaTime;
            if (bLockMoveTargetZ)
            {
                NewLocation.Z = LockedMoveTargetZ;
            }
            MoveTarget->SetActorLocation(NewLocation);
        }
    }
}

void UJoystickSR04ReceiverComponent::SendGet()
{
    if (UDPSender && UDPSender->Settings.bIsSendOpen)
    {
        FString Cmd = TEXT("GET");
        TArray<uint8> Bytes;
        Bytes.Append((const uint8*)TCHAR_TO_ANSI(*Cmd), Cmd.Len());
        UDPSender->EmitBytes(Bytes);
    }
}

void UJoystickSR04ReceiverComponent::SendInfo()
{
    if (UDPSender && UDPSender->Settings.bIsSendOpen)
    {
        FString Cmd = TEXT("INFO");
        TArray<uint8> Bytes;
        Bytes.Append((const uint8*)TCHAR_TO_ANSI(*Cmd), Cmd.Len());
        UDPSender->EmitBytes(Bytes);
    }
}

void UJoystickSR04ReceiverComponent::SendCommand(const FString& Command)
{
    if (UDPSender && UDPSender->Settings.bIsSendOpen)
    {
        TArray<uint8> Bytes;
        Bytes.Append((const uint8*)TCHAR_TO_ANSI(*Command), Command.Len());
        UDPSender->EmitBytes(Bytes);
    }
}

bool UJoystickSR04ReceiverComponent::ParseSensorJson(const FString& Json)
{
    TSharedPtr<FJsonObject> Root;
    const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Json);
    if (!FJsonSerializer::Deserialize(Reader, Root) || !Root.IsValid())
    {
        UE_LOG(LogTemp, Warning, TEXT("[JoystickSR04] Ignored malformed UDP JSON: %s"), *Json);
        return false;
    }

    FString Type;
    if (!Root->TryGetStringField(TEXT("type"), Type) || Type != TEXT("sensors"))
    {
        return false;
    }

    const TSharedPtr<FJsonObject>* JoyObject = nullptr;
    const TSharedPtr<FJsonObject>* SR04Object = nullptr;
    if (!Root->TryGetObjectField(TEXT("joy"), JoyObject) || !JoyObject || !JoyObject->IsValid() ||
        !Root->TryGetObjectField(TEXT("sr04"), SR04Object) || !SR04Object || !SR04Object->IsValid())
    {
        UE_LOG(LogTemp, Warning, TEXT("[JoystickSR04] Sensor JSON missing joy/sr04 object: %s"), *Json);
        return false;
    }

    auto ReadInt = [](const TSharedPtr<FJsonObject>& Object, const TCHAR* FieldName, int32 DefaultValue)
    {
        int32 Value = DefaultValue;
        double Number = 0.0;
        if (Object->TryGetNumberField(FieldName, Number))
        {
            Value = FMath::RoundToInt(Number);
        }
        return Value;
    };

    JoyUp = ReadInt(*JoyObject, TEXT("up"), 0);
    JoyDown = ReadInt(*JoyObject, TEXT("down"), 0);
    JoyLeft = ReadInt(*JoyObject, TEXT("left"), 0);
    JoyRight = ReadInt(*JoyObject, TEXT("right"), 0);
    JoyDirection = IntToJoyDir(ReadInt(*JoyObject, TEXT("dir"), 0));

    double DistanceNumber = -1.0;
    (*SR04Object)->TryGetNumberField(TEXT("distance"), DistanceNumber);
    Distance = static_cast<float>(DistanceNumber);

    bool bValid = false;
    (*SR04Object)->TryGetBoolField(TEXT("valid"), bValid);
    bDistanceValid = bValid && Distance >= 0.0f;

    return true;
}
