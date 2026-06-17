#include "JoystickSR04DriverComponent.h"
#include "Components/MeshComponent.h"
#include "EngineUtils.h"
#include "GameFramework/Actor.h"
#include "Materials/MaterialInstanceDynamic.h"

UJoystickSR04DriverComponent::UJoystickSR04DriverComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.TickInterval = 0.016f;
}

void UJoystickSR04DriverComponent::BeginPlay()
{
    Super::BeginPlay();

    AutoBindReceiver();
    AutoBindMoveTarget();

    if (Receiver)
    {
        Receiver->OnDataReceived.AddDynamic(this, &UJoystickSR04DriverComponent::OnSensorDataReceived);
    }
    else
    {
        const FString OwnerName = GetOwner() ? GetOwner()->GetName() : TEXT("<no owner>");
        UE_LOG(LogTemp, Warning, TEXT("[JoystickSR04Driver] No receiver found on %s"), *OwnerName);
    }
}

void UJoystickSR04DriverComponent::AutoBindReceiver()
{
    if (!Receiver && ReceiverActor)
    {
        Receiver = ReceiverActor->FindComponentByClass<UJoystickSR04ReceiverComponent>();
        if (Receiver)
        {
            UE_LOG(LogTemp, Log, TEXT("[JoystickSR04Driver] Bound receiver from selected actor %s"), *ReceiverActor->GetName());
        }
        else
        {
            UE_LOG(LogTemp, Warning, TEXT("[JoystickSR04Driver] Selected receiver actor %s has no JoystickSR04ReceiverComponent"), *ReceiverActor->GetName());
        }
    }

    if (!Receiver && GetOwner())
    {
        Receiver = GetOwner()->FindComponentByClass<UJoystickSR04ReceiverComponent>();
        if (Receiver)
        {
            UE_LOG(LogTemp, Log, TEXT("[JoystickSR04Driver] Auto-bound receiver on %s"), *GetOwner()->GetName());
        }
    }

    if (!Receiver && GetWorld())
    {
        for (TActorIterator<AActor> It(GetWorld()); It; ++It)
        {
            AActor* Actor = *It;
            if (!IsValid(Actor))
            {
                continue;
            }

            UJoystickSR04ReceiverComponent* FoundReceiver = Actor->FindComponentByClass<UJoystickSR04ReceiverComponent>();
            if (FoundReceiver)
            {
                Receiver = FoundReceiver;
                UE_LOG(LogTemp, Log, TEXT("[JoystickSR04Driver] Auto-bound receiver from %s"), *Actor->GetName());
                break;
            }
        }
    }
}

void UJoystickSR04DriverComponent::AutoBindMoveTarget()
{
    if (!MoveTarget)
    {
        MoveTarget = GetOwner();
    }

    if (MoveTarget)
    {
        LockedTargetZ = MoveTarget->GetActorLocation().Z;
        if (!TargetMesh)
        {
            TargetMesh = MoveTarget->FindComponentByClass<UMeshComponent>();
        }
    }
}

void UJoystickSR04DriverComponent::OnSensorDataReceived(
    EJoystickDir JoyDir, float InDistance, bool bValid,
    int32 Up, int32 Down, int32 Left, int32 Right)
{
    // Convert 8-direction to UE5 world direction
    // UE5: X=forward, Y=right, Z=up
    DesiredDirection = FVector::ZeroVector;
    switch (JoyDir)
    {
    case EJoystickDir::Up:        DesiredDirection = FVector(1, 0, 0); break;
    case EJoystickDir::UpRight:   DesiredDirection = FVector(1, 1, 0).GetSafeNormal(); break;
    case EJoystickDir::Right:     DesiredDirection = FVector(0, 1, 0); break;
    case EJoystickDir::DownRight: DesiredDirection = FVector(-1, 1, 0).GetSafeNormal(); break;
    case EJoystickDir::Down:      DesiredDirection = FVector(-1, 0, 0); break;
    case EJoystickDir::DownLeft:  DesiredDirection = FVector(-1, -1, 0).GetSafeNormal(); break;
    case EJoystickDir::Left:      DesiredDirection = FVector(0, -1, 0); break;
    case EJoystickDir::UpLeft:    DesiredDirection = FVector(1, -1, 0).GetSafeNormal(); break;
    default: break; // Center = zero
    }
}

void UJoystickSR04DriverComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

    if (!Receiver || !Receiver->bIsConnected)
    {
        SmoothedVelocity = FVector::ZeroVector;
        CurrentVelocity = FVector::ZeroVector;
        return;
    }

    // -- Movement --
    if (MoveTarget)
    {
        FVector TargetVel = DesiredDirection * MoveSpeed;

        // Manual SmoothDamp for velocity
        float Omega = 2.0f / FMath::Max(MoveSmoothTime, 0.0001f);
        float X = Omega * DeltaTime;
        float Exp = 1.0f / (1.0f + X + 0.48f * X * X + 0.235f * X * X * X);

        FVector Delta = TargetVel - SmoothedVelocity;
        FVector Temp = (Omega * Delta) * DeltaTime;
        SmoothedVelocity = (SmoothedVelocity + Delta - Temp) * Exp;
        // Note: simplified smoothdamp without max speed clamping for 3D

        FVector NewLoc = MoveTarget->GetActorLocation() + SmoothedVelocity * DeltaTime;
        if (bLockTargetZ)
        {
            NewLoc.Z = LockedTargetZ;
        }
        MoveTarget->SetActorLocation(NewLoc);

        CurrentVelocity = SmoothedVelocity;
    }

    // -- Distance Visual --
    if (TargetMesh && Receiver->bDistanceValid)
    {
        float DistRange = FMath::Max(MaxDistance - MinDistance, 1.0f);
        DistanceFraction = FMath::Clamp((Receiver->Distance - MinDistance) / DistRange, 0.0f, 1.0f);
        if (bInvertDistance) DistanceFraction = 1.0f - DistanceFraction;

        UMaterialInstanceDynamic* DynMat = TargetMesh->CreateAndSetMaterialInstanceDynamic(0);
        if (DynMat)
        {
            DynMat->SetScalarParameterValue(DistanceParamName, DistanceFraction);
        }
    }
}
